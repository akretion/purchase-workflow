# Copyright 2020 Akretion LTDA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import _, models, fields


class PurchaseRequisition(models.Model):
    _inherit = "purchase.requisition"

    def action_select_bids(self):
        self.ensure_one()

        tree_view_id = self.env.ref("purchase_tender_management.purchase_order_line_tree")
        search_view_id = self.env.ref("purchase_tender_management.purchase_order_line_search")

        return {
            "type": "ir.actions.act_window",
            "name": _("Bid Selection"),
            "res_model": "purchase.order.line",
            "views": [[tree_view_id.id, "tree"], [False, "form"]],
            "search_view_id": (search_view_id.id, search_view_id.name),
            "domain": [
                ("order_id", "in", self.purchase_ids.ids),
                ("state", "not in", ["done", "cancel"]),
            ],
            "context": {"search_default_groupby_product": 1},
        }

    def action_reset(self):
        for req in self:
            # Set every related PO back to draft
            for po in req.purchase_ids:
                if po.state == "purchase":
                    po.button_cancel()
                if po.state == "cancel":
                    po.button_draft()
                # Reactivate all the order_lines
                po.order_line.write({"active": True, "bid_selection": "unselected"})
        self.write({"state": "open"})
