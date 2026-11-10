"""Existing v1 config entries must remain loadable when installing the panel."""

import unittest

from custom_components.eltako.config.config_helpers import (
    get_gateway_name,
    get_id_from_gateway_name,
)


class TestLegacyGatewayDescription(unittest.TestCase):
    def test_saved_v1_description_with_base_id(self):
        description = 'EnOcean Gateway - fam14 (Id: 1, BaseId: FF-AA-80-00)'
        self.assertEqual(get_id_from_gateway_name(description), 1)

    def test_current_descriptions_round_trip(self):
        for gateway_id in (0, 1, 12):
            with self.subTest(gateway_id=gateway_id):
                description = get_gateway_name('My gateway', 'fam14', gateway_id)
                self.assertEqual(get_id_from_gateway_name(description), gateway_id)

    def test_malformed_description_is_rejected(self):
        for description in ('Gateway', 'Gateway (Id: bad)', 'Gateway (Id: 1bad)'):
            with self.subTest(description=description), self.assertRaises(ValueError):
                get_id_from_gateway_name(description)
