import os
import unittest
from collections import namedtuple

import django_functest
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.contrib.staticfiles.testing import StaticLiveServerTestCase

from django.core.exceptions import PermissionDenied
from django.template import Context, Template
from django.test import TestCase, override_settings
from django.urls import reverse
from wiki.models import URLPath

User = get_user_model()

TestUserInfo = namedtuple('UserInfo', 'username password mail permissions')
TestUserInfo.__doc__ = """ Helper structure for defining test user
information. Keep in mind that that this structure does not reflect
the database structure, nor is in any way tied-in into the database
structure. Its sole purpose is to provide a convenient way to access
information about test users without using the dict's [] operator.

Available attributes:

- username
- password
- mail
- permissions (tuple of strings, where each string represents a
  permission in Django admin system).

Attributes can be accessed with dot-syntax, like any standard
namedtuple. For example:

    user_info = TestUserInfo('user1', 'user1secret', 'user1@example.com', ())
    print(user_info.username)

    user_info = TestUserInfo('user1', 'user1secret', 'user1@example.com', ('wiki.assign', 'wiki.moderate'))
    print(user_info.permissions)
"""


SUPERUSER1_USERNAME = 'admin'
SUPERUSER1_PASSWORD = 'secret'


REGULAR_USERS = {
    'user1': TestUserInfo('user1', 'user1secret', 'user1@example.com', ()),
    'user2': TestUserInfo('user2', 'user2secret', 'user2@example.com', ()),
    'user3': TestUserInfo('user3', 'user3secret', 'user3@example.com', ()),
}


class TestException(Exception):
    """
    Exception raised internally by the test code itself in case the
    test code mixins or samples are not used correctly. The only
    purpose of this exception is to denote an error within the test
    code abstractions, and it must not be used for regular test code
    to mask-out any actual application-level exceptions.
    """
    pass


class RequireSuperuserMixin:
    def setUp(self):
        super().setUp()

        self.superuser1 = User.objects.create_superuser(
            SUPERUSER1_USERNAME,
            'nobody@example.com',
            SUPERUSER1_PASSWORD
        )


class RequireRegularUserMixin:

    def setUp(self):
        super(RequireRegularUserMixin, self).setUp()
        self.users = {}

        for user_id, user_info in REGULAR_USERS.items():
            user = User.objects.create_user(
                username=user_info.username,
                password=user_info.password,
                email=user_info.password,
            )

            for permission in user_info.permissions:
                user.user_permissions.add(Permission.objects.get(codename=permission))

            self.users[user_id] = user


class RequireBasicData(RequireRegularUserMixin, RequireSuperuserMixin):
    """
    Mixin that creates common data required for all tests.
    """
    pass


class TestBase(RequireBasicData, TestCase):
    pass


class RequireRootArticleMixin:

    def setUp(self):
        super().setUp()
        self.root = URLPath.create_root()
        self.root_article = URLPath.root().article
        rev = self.root_article.current_revision
        rev.title = "Root Article"
        rev.content = "root article content"
        rev.save()


class ArticleTestBase(RequireRootArticleMixin, TestBase):
    """
    Sets up basic data for testing with an article and some revisions
    """
    pass


class DjangoClientTestBase(TestBase):
    def setUp(self):
        super().setUp()

        self.login_as_user(SUPERUSER1_USERNAME)

    def login_as_user(self, user):
        """
        Logs-in the specified user. For list of users see the keys of
        REGULAR_USERS dictionary.

        If it is required to log-in as the administrator user, set
        user to 'name'.
        """

        if user == 'admin':
            username = 'admin'
            password = 'secret'
        else:
            try:
                username = REGULAR_USERS[user].username
                password = REGULAR_USERS[user].password
            except KeyError:
                raise TestException("No such test user '%s', available users are: %s" % (user, ", ". join(REGULAR_USERS.keys())))

        if not self.client.login(username=username, password=password):
            raise PermissionDenied("Could not log-in as specified test-user '%s' using password '%s'" % (username, password))


class WebTestCommonMixin(RequireBasicData, django_functest.ShortcutLoginMixin):
    """
    Common setup required for WebTest and Selenium tests
    """
    def setUp(self):
        super().setUp()

        self.shortcut_login(username=SUPERUSER1_USERNAME,
                            password=SUPERUSER1_PASSWORD)


class WebTestBase(WebTestCommonMixin, django_functest.FuncWebTestMixin, TestCase):
    pass


INCLUDE_SELENIUM_TESTS = os.environ.get('INCLUDE_SELENIUM_TESTS', '0') == '1'


@unittest.skipUnless(INCLUDE_SELENIUM_TESTS, "Skipping Selenium tests")
class SeleniumBase(WebTestCommonMixin, django_functest.FuncSeleniumMixin, StaticLiveServerTestCase):
    driver_name = "Chrome"
    display = os.environ.get('SELENIUM_SHOW_BROWSER', '0') == '1'

    if not INCLUDE_SELENIUM_TESTS:
        # Don't call super() in setUpClass(), it will attempt to instatiate
        # a browser instance which is slow and might fail
        @classmethod
        def setUpClass(cls):
            pass

        @classmethod
        def tearDownClass(cls):
            pass


class ArticleWebTestUtils:

    def get_by_path(self, path):
        """
        Get the article response for the path.
        Example:  self.get_by_path("Level1/Slug2/").title
        """

        return self.client.get(reverse('wiki:get', kwargs={'path': path}))


class TemplateTestCase(TestCase):

    @property
    def template(self):
        raise NotImplementedError("Subclasses must implement this")

    def render(self, context):
        return Template(self.template).render(Context(context))


# See
# https://github.com/django-wiki/django-wiki/pull/382
class wiki_override_settings(override_settings):

    def enable(self):
        super(wiki_override_settings, self).enable()
        self.reload_wiki_settings()

    def disable(self):
        super(wiki_override_settings, self).disable()
        self.reload_wiki_settings()

    def reload_wiki_settings(self):
        from importlib import reload
        from wiki.conf import settings
        reload(settings)
