# Copyright 2020 Akretion LTDA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import _, fields, models


class PurchaseOrderLine(models.Model):
    _inherit = "purchase.order.line"

    # Technical field in order to hide unwanted order_line
    active = fields.Boolean(default=True)

    is_lowest_price_line = fields.Boolean(default=False)

    bid_selection = fields.Selection(
        string="Bid Selection",
        selection=[
            ("unselected", "Unselected"),
            ("selected", "Selected"),
            ("rejected", "Rejected"),
        ],
        default="unselected",
    )

    def action_select_bid(self):
        for line in self:
            line.bid_selection = "selected"

    def action_reject_bid(self):
        for line in self:
            line.bid_selection = "rejected"

    def action_bid_selection(self):
        """Action triggered by server action in Bid Selection tree view
        It is assumed that all the order_line (gathered in self) are related to a
        purchase_order with all the same requisition_id"""
        requisition_id = self[0].order_id.requisition_id
        line_ids = self.env["purchase.order.line"].search(
            [
                ("order_id.requisition_id", "=", requisition_id.id),
                ("state", "not in", ["done", "cancel"]),
            ]
        )
        selected_line_ids = line_ids.filtered(lambda l: l.bid_selection == "selected")

        return {
            "name": _("Confirm Bid Selection"),
            "type": "ir.actions.act_window",
            "view_id": self.env.ref("purchase_requisition_selection.bid_selection_wizard_view_form").id,
            "view_mode": "form",
            "res_model": "bid.selection.wizard",
            "target": "new",
            "context": {
                "default_requisition_id": requisition_id.id,
                "default_line_ids": line_ids.ids,
                "default_selected_line_ids": selected_line_ids.ids,
            },
        }
