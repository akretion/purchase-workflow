# Copyright (C) 2021 ForgeFlow S.L.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/lgpl.html)

from odoo import api, fields, models


class AccountPayment(models.Model):
    _inherit = "account.payment"

    purchase_id = fields.Many2one(
        "purchase.order",
        "Purchase",
        readonly=True,
        states={"draft": [("readonly", False)]},
    )

    def action_open(self):
        return {
            "view_type": "form",
            "view_mode": "form",
            "res_model": "account.payment",
            "res_id": self.id,
            "type": "ir.actions.act_window",
            "target": "current",
        }
