# Copyright 2025 Mathieu DElVA @ Akretion
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import fields, models
from odoo.tools import float_compare


class PurchaseOrderLine(models.Model):
    _inherit = "purchase.order.line"

    supplierinfo_price_exist = fields.Boolean(compute="_compute_supplierinfo_price")
    supplierinfo_price_ok = fields.Boolean(compute="_compute_supplierinfo_price")

    def _compute_supplierinfo_price(self):
        for line in self:
            line.supplierinfo_price_exist = False
            line.supplierinfo_price_ok = False
            if not line.product_id:
                continue
            supplierinfos = line.product_id._select_seller(
                line.order_id.partner_id.commercial_partner_id,
                quantity=None,
            )
            if supplierinfos:
                line.supplierinfo_price_exist = True
                line.supplierinfo_price_ok = line._is_matching_supplierinfo(
                    supplierinfos
                )

    def _is_matching_supplierinfo(self, supplierinfo):
        """Return True if the partner information matches with line information"""
        self.ensure_one()
        res = (
            not self.product_uom or self.product_uom == supplierinfo.product_uom
        ) and not float_compare(
            self.price_unit,
            supplierinfo.price,
            precision_rounding=self.currency_id.rounding,
        )
        return res

    def _prepare_supplier_wizard_line(self, supplierinfo):
        """Prepare the value that will proposed to user in the wizard
        to update supplierinfo"""
        self.ensure_one()
        return {
            "product_id": self.product_id.id,
            "supplierinfo_id": supplierinfo and supplierinfo.id or False,
            "current_price": supplierinfo and supplierinfo.price or False,
            "new_price": self.price_unit,
        }
