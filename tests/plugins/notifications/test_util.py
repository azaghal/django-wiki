from django.utils.translation import ugettext as _

from wiki.plugins.notifications.util import get_title, truncate_title

import mock


TITLE_MAXIMUM_LENGTH_BEFORE_TRIMMING = 25


def test_truncate_title_title_is_false():
    assert truncate_title(False) == _("(none)")


def test_truncate_title_title_is_none():
    assert truncate_title(None) == _("(none)")


def test_truncate_title_not_trimmed_when_equal_or_under_maximum_length():
    title = "a" * TITLE_MAXIMUM_LENGTH_BEFORE_TRIMMING

    assert truncate_title(title) == title


def test_truncate_title_trimmed_when_above_maximum_length():
    title = "a" * (TITLE_MAXIMUM_LENGTH_BEFORE_TRIMMING + 1)
    trimmed_title = "%s..." % ("a" * (TITLE_MAXIMUM_LENGTH_BEFORE_TRIMMING - 3))

    assert truncate_title(title) == trimmed_title


def test_get_title_return_value():
    article = mock.Mock()
    article.title = "This is article title"
    assert get_title(article) == article.title


@mock.patch('wiki.plugins.notifications.util.truncate_title')
def test_get_title_calls_truncate_title(mock_truncate_title):
    article = mock.Mock()
    article.title = "This is article title"

    get_title(article)
    mock_truncate_title.assert_called_once_with(article.title)
