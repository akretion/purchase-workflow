# Copyright 2026 Akretion
# @author Guillaume MASSON <guillaume.masson@akretion.com>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class PurchaseOrder(models.Model):
    _inherit = "purchase.order"

    picking_type_id = fields.Many2one(
        compute="_compute_picking_type_id",
        store=True,
        readonly=False,
    )

    @api.depends("partner_id", "incoterm_id")
    def _compute_picking_type_id(self):
        for order in self:
            order.picking_type_id = order._get_receipt_picking_type(
                order.picking_type_id or order._get_picking_type(order.company_id.id)
            )

    @api.model
    def create(self, vals):
        order = super().create(vals)
        if (
            "default_picking_type_id" not in self.env.context
            and "picking_type_id" not in vals
        ):
            order._compute_picking_type_id()
        return order

    def _get_receipt_picking_type(self, picking_type):
        self.ensure_one()
        warehouse = picking_type.warehouse_id
        if self._requires_transit_receipt():
            return warehouse.transit_in_type_id or picking_type
        if picking_type == warehouse.transit_in_type_id:
            return warehouse.in_type_id
        return picking_type

    def _requires_transit_receipt(self):
        self.ensure_one()
        return self.incoterm_id.transit_receipt

    def _is_transit_purchase(self):
        self.ensure_one()
        return (
            self.picking_type_id == self.picking_type_id.warehouse_id.transit_in_type_id
        )
