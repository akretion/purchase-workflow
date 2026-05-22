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

    def _prepare_supplierinfo_update(self):
        self.ensure_one()
        res = {
            "price": self.new_price,
        }
        return res
