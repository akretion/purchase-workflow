# Copyright 2026 Akretion
# @author Guillaume MASSON <guillaume.masson@akretion.com>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo.exceptions import UserError
from odoo.tests.common import Form

from .common import TransitReceiptCommon


class TestPhysicalReceipt(TransitReceiptCommon):
    def test_blocked_before_transit_receipt(self):
        purchase = self._create_purchase()
        physical_receipt = self._next_picking(purchase.picking_ids)
        self.assertEqual(physical_receipt.state, "waiting")
        with self.assertRaises(UserError):
            self._validate(physical_receipt)

    def test_blocked_beyond_quantity_in_transit(self):
        purchase = self._create_purchase()
        transit_receipt = purchase.picking_ids
        self._validate(transit_receipt, quantity=2)
        physical_receipt = self._next_picking(transit_receipt)
        with self.assertRaises(UserError):
            self._validate(physical_receipt, quantity=3)
        self._validate(physical_receipt, quantity=2)
        self.assertEqual(purchase.order_line.qty_received, 2)

    def test_quantity_returned_to_vendor_no_longer_in_transit(self):
        purchase = self._create_purchase()
        transit_receipt = purchase.picking_ids
        self._validate(transit_receipt)
        physical_receipt = self._next_picking(transit_receipt)
        wizard_form = Form(
            self.env["stock.return.picking"].with_context(
                active_id=transit_receipt.id,
                active_ids=transit_receipt.ids,
                active_model="stock.picking",
            )
        )
        with wizard_form.product_return_moves.edit(0) as line:
            line.quantity = 2
        return_picking = self.env["stock.picking"].browse(
            wizard_form.save().create_returns()["res_id"]
        )
        self._validate(return_picking)
        with self.assertRaises(UserError):
            self._validate(physical_receipt, quantity=4)
