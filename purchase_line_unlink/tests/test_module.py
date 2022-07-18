# Copyright 2022 Akretion
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo.exceptions import ValidationError
from odoo.tests.common import Form, SavepointCase


class Test(SavepointCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.prd_purchase = cls.env["product.product"].create(
            {
                "name": "control policy: on ordered qties",
                "type": "product",
                "purchase_method": "purchase",
                "purchase_ok": True,
                "default_code": "purchase",
            }
        )
        cls.prd_receive = cls.env["product.product"].create(
            {
                "name": "control policy: on received qties",
                "type": "product",
                "purchase_method": "receive",
                "purchase_ok": True,
                "default_code": "receive",
            }
        )
        vals = cls.get_purchase_order_vals(cls)
        cls.product_line = vals.pop("product_line")
        cls.po = cls.env["purchase.order"].create(vals)
        cls.po.name = str(cls.po.id)

    def test_unlink_with_purchase_policy(self):
        po = self.po
        po.button_confirm()
        assert len(po.order_line) == 1
        pol = po.order_line
        po.action_create_invoice()
        assert pol.product_id.purchase_method == "purchase"
        # import pdb; pdb.set_trace()
        res = pol.unlink()
        assert res is True

    def test_unlink_when_draft_account_move(self):
        po = self.po
        po.button_confirm()
        assert len(po.order_line) == 2
        po.action_create_invoice()
        assert len(po.invoice_ids[0].invoice_line_ids) == 1
        po.invoice_ids[0].state == "draft"
        res = po.invoice_ids[0].line_ids.unlink()
        assert res == True
        assert not po.invoice_ids
        line = po.order_line.filtered(
            lambda s: s.product_id.purchase_method == "purchase"
        )
        assert line.product_id.purchase_method == "purchase"
        res = line.unlink()
        assert res is True
        assert len(po.order_line) == 1

    def test_unlink_stock_move(self):
        po = self.po
        po.button_confirm()
        # assert len(po.picking_ids[0].move_ids_without_package) == 1
        # self.po.state == "purchase"
        # self.po.order_line[0].unlink()
        # assert len(self.po.order_line) == 0
        # self.assertEqual(self.purchase_order.custom_rate, 0.0)
        # with Form(self.purchase_order) as p:
        #     p.currency_id = self.currency_usd
        #     p.manual_currency = True
        # self.assertNotEqual(self.purchase_order.custom_rate, 0.0)
        # # check function refresh
        # with self.assertRaises(ValidationError):
        #     self.purchase_order.action_refresh_currency()

    def make_account_move(self):
        self.po.order_line[0].product_id.purchase_method = "purchase"
        self.po.button_confirm()
        self.po.state == "purchase"
        self.po.action_create_invoice()

    def get_purchase_order_vals(self):
        return {
            "name": "any",
            # "pricelist_id": self.env.ref("product.list0").id,
            # "location_id": self.env.ref("stock.stock_location_stock").id,
            "partner_id": self.env.ref("base.res_partner_1").id,
            # "validator": self.env.ref("base.user_demo").id,
            "order_line": [
                (
                    0,
                    0,
                    {
                        "name": "purchase",
                        "product_id": self.prd_purchase.id,
                        "product_qty": 2,
                        "price_unit": 10.00,
                        "date_planned": "2024-07-21",
                    },
                ),
            ],
            "product_line":
                (
                    0,
                    0,
                    {
                        "name": "receive",
                        "product_id": self.prd_receive.id,
                        "product_qty": 2,
                        "price_unit": 15.00,
                        "date_planned": "2024-07-21",
                    },
                ),
        }
