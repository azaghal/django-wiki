import mock

from django.test.testcases import TestCase

from wiki.admin import ArticleRevisionForm
from wiki.editors import getEditor


class TestArticleRevisionForm(TestCase):

    @mock.patch('wiki.editors.getEditor')
    def test_content_widget(self, mock_getEditor):
        mock_widget = mock.Mock()
        mock_editor = mock.Mock()
        mock_editor.get_admin_widget.return_value = mock_widget
        mock_getEditor.return_value = mock_editor

        form = ArticleRevisionForm()

        self.assertEqual(form.fields['content'].widget, mock_widget)
