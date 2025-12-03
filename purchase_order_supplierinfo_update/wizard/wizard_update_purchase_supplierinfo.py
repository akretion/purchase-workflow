# Copyright 2025 Mathieu DElVA @ Akretion
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import fields, models


class WizardUpdatePurchaseSupplierinfo(models.TransientModel):
    _name = "wizard.update.purchase.supplierinfo"
    _description = "Wizard to update supplierinfo"

    line_ids = fields.One2many(
        comodel_name="wizard.update.purchase.supplierinfo.line",
        inverse_name="wizard_id",
        string="Lines",
    )

    purchase_id = fields.Many2one(
        comodel_name="purchase.order",
        required=True,
        readonly=True,
        ondelete="cascade",
    )

    state = fields.Selection(related="purchase_id.state", readonly=True)

    def update_supplierinfo(self):
        self.ensure_one()
        for line in self.line_ids:
            supplierinfo = line.supplierinfo_id
            vals = line._prepare_supplierinfo_update()
            supplierinfo.write(vals)
