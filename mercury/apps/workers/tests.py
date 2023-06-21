from django.test import TestCase

from apps.workers.models import Machine
from apps.workers.utils import get_running_machines, shuffle_machines

# Create your tests here.
# python manage.py test apps.workers -v 2

class ManageMachinesTestCase(TestCase):
    def test_get_running_machines(self):
        ms = get_running_machines()
        self.assertEqual(len(ms), 0)

        Machine.objects.create(
            ipv4="0.0.0.0",
            state="Running"
        )
        ms = get_running_machines()
        self.assertEqual(len(ms), 1)

    def test_shuffle_machines(self):
        Machine.objects.create(
            ipv4="0.0.0.0",
            state="Running"
        )
        Machine.objects.create(
            ipv4="0.0.0.0",
            state="Running"
        )
        
        ms = get_running_machines()
        self.assertEqual(len(ms), 2)
        ms = shuffle_machines(ms)
        self.assertEqual(len(ms), 2)

