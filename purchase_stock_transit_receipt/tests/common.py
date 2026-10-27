# Copyright 2026 Akretion
# @author Guillaume MASSON <guillaume.masson@akretion.com>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo.tests.common import SavepointCase


class TransitReceiptCommon(SavepointCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env = cls.env(context=dict(cls.env.context, tracking_disable=True))
        cls.warehouse = cls.env["stock.warehouse"].create(
            {"name": "Transit Warehouse", "code": "TWH"}
        )
        cls.supplier = cls.env["res.partner"].create({"name": "Supplier"})
        cls.product = cls.env["product.product"].create(
            {
                "name": "Product",
                "type": "product",
                "standard_price": 10.0,
            }
        )

    def _create_purchase(self, picking_type=None, quantity=5.0):
        purchase = self.env["purchase.order"].create(
            {
                "partner_id": self.supplier.id,
                "picking_type_id": (
                    picking_type or self.warehouse.transit_in_type_id
                ).id,
                "order_line": [
                    (
                        0,
                        0,
                        {
                            "product_id": self.product.id,
                            "product_qty": quantity,
                            "price_unit": 10.0,
                        },
                    )
                ],
            }
        )
        purchase.button_confirm()
        return purchase

    def _validate(self, picking, quantity=None):
        picking.action_assign()
        for move in picking.move_lines:
            move.quantity_done = move.product_uom_qty if quantity is None else quantity
        picking._action_done()

    def _next_picking(self, picking):
        return picking.move_lines.move_dest_ids.picking_id
