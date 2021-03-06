"""
dj-stripe Event Model Tests.
"""
from copy import deepcopy
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import TestCase
from stripe.error import StripeError

from djstripe import webhooks
from djstripe.models import Event

from . import FAKE_CUSTOMER, FAKE_EVENT_TRANSFER_CREATED


class EventTest(TestCase):
	def setUp(self):
		self.user = get_user_model().objects.create_user(
			username="pydanny", email="pydanny@gmail.com"
		)
		self.customer = FAKE_CUSTOMER.create_for_user(self.user)

		patcher = patch.object(webhooks, "call_handlers")
		self.addCleanup(patcher.stop)
		self.call_handlers = patcher.start()

	def test_str(self):
		event = self._create_event(FAKE_EVENT_TRANSFER_CREATED)

		self.assertEqual(
			"<type={type}, id={id}>".format(
				type=FAKE_EVENT_TRANSFER_CREATED["type"], id=FAKE_EVENT_TRANSFER_CREATED["id"]
			),
			str(event),
		)

	def test_invoke_webhook_handlers_event_with_log_stripe_error(self):
		event = self._create_event(FAKE_EVENT_TRANSFER_CREATED)
		self.call_handlers.side_effect = StripeError("Boom!")
		with self.assertRaises(StripeError):
			event.invoke_webhook_handlers()

	def test_invoke_webhook_handlers_event_with_raise_stripe_error(self):
		event = self._create_event(FAKE_EVENT_TRANSFER_CREATED)
		self.call_handlers.side_effect = StripeError("Boom!")
		with self.assertRaises(StripeError):
			event.invoke_webhook_handlers()

	def test_invoke_webhook_handlers_event_when_invalid(self):
		event = self._create_event(FAKE_EVENT_TRANSFER_CREATED)
		event.valid = False
		event.invoke_webhook_handlers()

	#
	# Helpers
	#

	@patch("stripe.Event.retrieve")
	def _create_event(self, event_data, event_retrieve_mock):
		event_data = deepcopy(event_data)
		event_retrieve_mock.return_value = event_data
		event = Event.sync_from_stripe_data(event_data)
		return event
