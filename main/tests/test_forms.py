from django.test import TestCase

from main.forms_pra import PRAFormReason


class TestPRAFormReason(TestCase):
    def test_PRA_form_reason_valid_data(self):
        form = PRAFormReason(data={"authorized_reason": "Hybrid Working"})

        self.assertTrue(form.is_valid)
