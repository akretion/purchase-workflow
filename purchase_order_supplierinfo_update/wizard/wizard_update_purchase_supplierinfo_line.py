# Copyright 2025 Mathieu DElVA @ Akretion
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
from odoo import fields, models


class WizardUpdatePurchaseSupplierinfoLine(models.TransientModel):
    _name = "wizard.update.purchase.supplierinfo.line"
    _description = "Wizard Line to update supplierinfo"

    wizard_id = fields.Many2one(
        comodel_name="wizard.update.purchase.supplierinfo",
        required=True,
        ondelete="cascade",
    )

    product_id = fields.Many2one("product.product", string="Product")

    supplierinfo_id = fields.Many2one(comodel_name="product.supplierinfo")

    current_price = fields.Float(
        related="supplierinfo_id.price",
        digits="Product Price",
        readonly=True,
    )

    new_price = fields.Float(
        string="New Unit Price",
        digits="Product Price",
        required=True,
    )

    current_min_qty = fields.Float(related="supplierinfo_id.min_qty", readonly=True)
    new_min_qty = fields.Float(string="New Quantity")
    current_date_start = fields.Date(
        related="supplierinfo_id.date_start", readonly=True
    )
    new_date_start = fields.Date()

    current_date_end = fields.Date(related="supplierinfo_id.date_end", readonly=True)
    new_date_end = fields.Date()

    current_delay = fields.Integer(related="supplierinfo_id.delay", readonly=True)
    new_delay = fields.Integer()

    def _prepare_supplierinfo_update(self):
        self.ensure_one()
        res = {
            "price": self.new_price,
            "min_qty": self.new_min_qty,
            "date_start": self.new_date_start,
            "date_end": self.new_date_end,
            "delay": self.new_delay,
        }
        return res
