# Copyright 2025 Mathieu DElVA @ Akretion
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo.tests import Form, SavepointCase


class TestPurchaseManualAddSupplierinfo(SavepointCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.purchase = cls.env.ref("purchase_stock.purchase_order_8")
        product = cls.env.ref("product.product_product_25_product_template")
        vendor = cls.env.ref("base.res_partner_4")

        cls.supplierinfo = cls.env["product.supplierinfo"].search(
            [("product_tmpl_id", "=", product.id), ("name", "=", vendor.id)]
        )

    def test_update_supplierinfo_price(self):
        self.purchase.order_line.price_unit = 3000
        self.assertFalse(self.purchase.order_line.supplierinfo_price_ok)
        self.assertNotEqual(
            self.supplierinfo.price, self.purchase.order_line.price_unit
        )
        self.assertEqual(self.supplierinfo.price, 2864.80)
        action = self.purchase.supplierinfo_update_price()
        self.assertEqual(action["res_model"], "wizard.update.purchase.supplierinfo")
        wizard = Form(
            self.env["wizard.update.purchase.supplierinfo"].with_context(
                action["context"]
            )
        ).save()
        wizard.update_supplierinfo()
        self.assertEqual(self.supplierinfo.price, 3000)
        self.assertEqual(self.supplierinfo.price, self.purchase.order_line.price_unit)
