from django.apps import apps
from django.contrib.auth.models import Group as AuthGroup

from django.test import TestCase
from wiki.conf import settings as wiki_settings
from wiki.forms import Group as WikiGroup
from wiki.models import URLPath

from ..base import wiki_override_settings
from ..testdata.models import CustomGroup


class URLPathTests(TestCase):

    def test_manager(self):

        root = URLPath.create_root()
        child = URLPath.create_urlpath(root, "child")

        self.assertEqual(root.parent, None)
        self.assertEqual(list(root.children.all().active()), [child])


class CustomGroupTests(TestCase):
    def test_setting(self):
        self.assertEqual(WikiGroup, AuthGroup)
        self.assertEqual(wiki_settings.GROUP_MODEL, 'auth.Group')

    @wiki_override_settings(WIKI_GROUP_MODEL='testdata.CustomGroup')
    def test_custom(self):
        Group = apps.get_model(wiki_settings.GROUP_MODEL)
        self.assertEqual(Group, CustomGroup)
        self.assertEqual(wiki_settings.GROUP_MODEL, 'testdata.CustomGroup')
