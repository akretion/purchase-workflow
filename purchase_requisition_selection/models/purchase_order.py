# Copyright 2020 Akretion LTDA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class PurchaseOrder(models.Model):
    _inherit = "purchase.order"

    # True if supplier set price once
    is_filled = fields.Boolean(
        compute="_compute_is_filled",
        default=False,
        store=True,
    )

    @api.depends("order_line.is_filled")
    def _compute_is_filled(self):
        for po in self:
            po.is_filled = any(l.is_filled for l in po.order_line)
