"""An unexpected base-id response must not redirect feedback away from entities."""
import unittest
from unittest.mock import Mock

from eltakobus.util import AddressExpression
from tests.mocks import GatewayMock


class TestConfiguredBaseId(unittest.TestCase):
    def test_mismatching_response_preserves_feedback_address(self):
        gateway = GatewayMock()
        configured = gateway.base_id
        gateway._fire_base_id_change_handlers = Mock()
        self.assertFalse(gateway._accept_reported_base_id(AddressExpression.parse('00-00-00-60')))
        self.assertEqual(gateway.base_id[0], configured[0])
        gateway._fire_base_id_change_handlers.assert_not_called()

    def test_matching_response_is_accepted(self):
        gateway = GatewayMock()
        gateway._fire_base_id_change_handlers = Mock()
        self.assertTrue(gateway._accept_reported_base_id(gateway.base_id))
        gateway._fire_base_id_change_handlers.assert_called_once_with(gateway.base_id)

    def test_unconfigured_gateway_can_discover_its_address(self):
        gateway = GatewayMock()
        gateway._configured_base_id = AddressExpression.parse('00-00-00-00')
        gateway._fire_base_id_change_handlers = Mock()
        reported = AddressExpression.parse('FF-AA-00-00')
        self.assertTrue(gateway._accept_reported_base_id(reported))
        self.assertEqual(gateway.base_id[0], reported[0])
