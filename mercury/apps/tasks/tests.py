from django.test import TestCase

from apps.tasks.tasks import sanitize_string

# python manage.py test apps.tasks.tests -v 2


class SanitizeTestCase(TestCase):
    def test_CJK(self):
        input_string = """テスト(){}
                        asdfasdf"()"[]''{}:"""

        output_string = sanitize_string(input_string)

        self.assertTrue("(" not in output_string)
        self.assertTrue("[" not in output_string)
        self.assertTrue(output_string.startswith("テスト"))
        self.assertTrue(output_string.endswith("asdfasdf:"))
