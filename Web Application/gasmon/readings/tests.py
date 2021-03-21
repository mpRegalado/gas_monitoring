from django.test import TestCase
from .models import Session
from django.urls import reverse
from django.utils import timezone
import requests
import json
# Create your tests here.


class IndexViewTests(TestCase):

    def test_no_sessions(self):
        response = self.client.get(reverse('index'))
        self.assertContains(response, "No sessions on record")

    def test_one_session(self):
        Session(session_id=5, name="Test Session").save()
        response = self.client.get(reverse('index'))
        self.assertContains(response, "Test Session")
        self.assertQuerysetEqual(
            response.context['session_list'],
            ['<Session: Test Session>']
        )

class SessionModelTests(TestCase):
        def test_is_fixed_no_measurements(self):
            s = Session(session_id=69, name="No Measurement")
            self.assertEqual(s.is_fixed(),False)

        def test_is_fixed_unfixed_measurement(self):
            s = Session(session_id=69, name="Unfixed")
            s.save()
            m = s.measurement_set.create(gas_high=100,gas_avg=1)
            self.assertEqual(m.latitude,None)
            self.assertEqual(m.longitude,None)
            self.assertEqual(s.is_fixed(),False)

        def test_is_fixed_fixed_measurement(self):
            s = Session(session_id=69, name="Fixed")
            s.save()
            m = s.measurement_set.create(gas_high=100,gas_avg=1, latitude=90, longitude=45)

            self.assertEqual(m.latitude,90)
            self.assertEqual(m.longitude,45)
            self.assertEqual(s.is_fixed(),True)

        def test_is_fixed_unfixed_fixed(self):
            s = Session(session_id=69, name="Unfixed then fixed")
            s.save()
            unfixed = s.measurement_set.create(gas_high=100,gas_avg=1)
            fixed = s.measurement_set.create(gas_high=100,gas_avg=1, latitude=90, longitude=45)

            self.assertEqual(s.is_fixed(),True)

        def test_first_fixed_no_measurements(self):
            s = Session(session_id=69, name="No Measurement")
            self.assertEqual(s.get_first_fix(),None)

        def test_first_fixed_unfixed_measurement(self):
            s = Session(session_id=69, name="Unfixed")
            s.save()
            m = s.measurement_set.create(gas_high=100,gas_avg=1)
            self.assertEqual(s.get_first_fix(),None)
            self.assertEqual(m.is_fixed(),False)

        def test_first_fixed_fixed_measurement(self):
            s = Session(session_id=69, name="Fixed")
            s.save()
            m = s.measurement_set.create(gas_high=100,gas_avg=1, latitude=90, longitude=45)

            self.assertEqual(m,s.get_first_fix())
            self.assertEqual(m.is_fixed(),True)

        def test_first_fixed_unfixed_fixed(self):
            s = Session(session_id=69, name="Unfixed then fixed")
            s.save()
            unfixed = s.measurement_set.create(gas_high=100,gas_avg=1)
            fixed = s.measurement_set.create(gas_high=100,gas_avg=1, latitude=90, longitude=45)

            self.assertEqual(s.get_first_fix(),fixed)
            self.assertEqual(unfixed.is_fixed(),False)
            self.assertEqual(fixed.is_fixed(),True)

        def test_first_fixed_two_fixed(self):
            s = Session(session_id=69, name="Unfixed then fixed")
            s.save()
            fixed1 = s.measurement_set.create(gas_high=100,gas_avg=1, latitude=90, longitude=45)
            fixed2 = s.measurement_set.create(gas_high=100,gas_avg=1, latitude=90, longitude=45)

            self.assertEqual(fixed1,s.get_first_fix())

class PostViewTests(TestCase):
    def test_post_into_database(self):
        data = {
            'session_id': 69,
            'gas_avg':100,
            'gas_high': 420,
            'latitude': 4.13,
            'longitude': 80.08,
            'date_time': '2020-07-13 20:30:00'
        }
        headers = {'content-type':'application/json'}
        self.client.post(reverse('readings:post'), content_type='application/json',data=data)


        session=Session.objects.get(session_id=69)
        measurement=session.measurement_set.last()
        local_date_time = timezone.localtime(measurement.date_time)
        self.assertEqual(session.session_id, 69)
        self.assertEqual(measurement.gas_avg, 100)
        self.assertEqual(measurement.gas_high,420)
        self.assertEqual(measurement.latitude,4.13)
        self.assertEqual(measurement.longitude,80.08)
        self.assertEqual(measurement.date_time.day,13)
        self.assertEqual(measurement.date_time.month,7)
        self.assertEqual(measurement.date_time.year,2020)
        self.assertEqual(measurement.date_time.hour,20)
        self.assertEqual(measurement.date_time.minute,30)
        self.assertEqual(measurement.date_time.second,00)
