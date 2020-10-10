# Copyright 2020 Akretion LTDA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import _, models, fields


class PurchaseRequisition(models.Model):
    _inherit = "purchase.requisition"

    def _detect_lowest_price_line(self):
        """For each product, set `is_lowest_price_line` to True for the order_line with
        the lowest price_unit"""
        line_ids = self.env["purchase.order.line"].search(
            [
                ("order_id", "in", self.purchase_ids.ids),
                ("state", "not in", ["done", "cancel"]),
            ]
        )
        product_ids = line_ids.mapped("product_id")

        for prod in product_ids:
            prod_line_ids = line_ids.filtered(lambda l: l.product_id == prod)

            lowest_price_line_id = prod_line_ids.sorted(key=lambda l: l.price_unit)[0]
            lowest_price_line_id.is_lowest_price_line = True

            other_line_ids = prod_line_ids - lowest_price_line_id
            other_line_ids.write({"is_lowest_price_line": False})

    def action_select_bids(self):
        self.ensure_one()
        self._detect_lowest_price_line()

        tree_view_id = self.env.ref(
            "purchase_requisition_selection.purchase_order_line_bid_selection_view_tree"
        )
        search_view_id = self.env.ref(
            "purchase_requisition_selection.purchase_order_line_search"
        )

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
            line_ids = self.env["purchase.order.line"].search(
                [
                    ("order_id.requisition_id", "=", req.id),
                    ("active", "in", [True, False]),
                ]
            )
            line_ids.write({"active": True, "bid_selection": "unselected"})
        self.write({"state": "open"})
