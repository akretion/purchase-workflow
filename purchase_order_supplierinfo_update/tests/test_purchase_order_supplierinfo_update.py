# Copyright 2025 Mathieu DElVA @ Akretion
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from datetime import date, datetime

from dateutil.relativedelta import relativedelta

from odoo.exceptions import UserError
from odoo.tests import Form, SavepointCase


class TestPurchaseManualAddSupplierinfo(SavepointCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.product_tmpl_id = cls.env["product.template"].create(
            {
                "name": "Test Product",
            }
        )
        cls.vendor_id = cls.env.ref("base.res_partner_4")
        cls.uom = cls.env.ref("uom.product_uom_unit")
        cls.supplierinfo = cls.env["product.supplierinfo"].create(
            {
                "product_tmpl_id": cls.product_tmpl_id.id,
                "name": cls.vendor_id.id,
                "delay": 5,
                "min_qty": 1,
                "price": 100,
                "date_start": date.today() - relativedelta(months=12),
                "date_end": date.today(),
            }
        )
        cls.purchase = cls.env["purchase.order"].create(
            {
                "partner_id": cls.vendor_id.id,
                "date_order": datetime.today() - relativedelta(months=1),
                "date_planned": datetime.today() - relativedelta(months=1),
                "order_line": [
                    (
                        0,
                        0,
                        {
                            "product_id": cls.product_tmpl_id.product_variant_id.id,
                            "price_unit": 200,
                            "product_qty": 10,
                            "product_uom": cls.uom.id,
                            "date_planned": datetime.today() - relativedelta(months=2),
                        },
                    )
                ],
            }
        )
        cls.purchase.button_confirm()

    def test_update_supplierinfo_price(self):
        self.assertFalse(self.purchase.order_line.supplierinfo_price_ok)
        self.assertNotEqual(
            self.supplierinfo.price, self.purchase.order_line.price_unit
        )
        self.assertEqual(self.supplierinfo.price, 100)
        action = self.purchase.supplierinfo_update_price()
        self.assertEqual(action["res_model"], "wizard.update.purchase.supplierinfo")
        wizard = Form(
            self.env["wizard.update.purchase.supplierinfo"].with_context(
                action["context"]
            )
        ).save()
        wizard.update_supplierinfo()
        self.assertEqual(self.supplierinfo.price, 200)
        self.assertEqual(self.supplierinfo.price, self.purchase.order_line.price_unit)

    def test_update_product_with_several_supplierinfo(self):
        self.supplierinfo.date_end = date.today() - relativedelta(months=6)
        supplierinfo2 = self.env["product.supplierinfo"].create(
            {
                "product_tmpl_id": self.product_tmpl_id.id,
                "name": self.vendor_id.id,
                "delay": 5,
                "min_qty": 4,
                "price": 150,
                "date_start": date.today() - relativedelta(months=6),
                "date_end": date.today() - relativedelta(months=1),
            }
        )
        self.assertEqual(self.supplierinfo.price, 100)
        self.assertEqual(supplierinfo2.price, 150)
        action = self.purchase.supplierinfo_update_price()
        self.assertEqual(action["res_model"], "wizard.update.purchase.supplierinfo")
        wizard = Form(
            self.env["wizard.update.purchase.supplierinfo"].with_context(
                action["context"]
            )
        ).save()
        wizard.update_supplierinfo()
        self.assertEqual(self.supplierinfo.price, 100)
        self.assertEqual(supplierinfo2.price, 200)

    def test_update_product_without_supplierinfo(self):
        self.supplierinfo.unlink()
        with self.assertRaises(UserError):
            self.purchase.supplierinfo_update_price()
