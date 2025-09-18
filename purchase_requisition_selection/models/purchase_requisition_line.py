# Copyright 2020 Akretion LTDA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models


class PurchaseRequisitionLine(models.Model):
    _inherit = "purchase.requisition.line"

    purchase_line_ids = fields.One2many(
        comodel_name="purchase.order.line",
        inverse_name="requisition_line_id",
    )

    def _prepare_purchase_order_line(
        self, name, product_qty=0.0, price_unit=0.0, taxes_ids=False
    ):
        values = super()._prepare_purchase_order_line(
            name=name,
            product_qty=product_qty,
            price_unit=price_unit,
            taxes_ids=taxes_ids,
        )
        values["requisition_line_id"] = self.id
        return values
