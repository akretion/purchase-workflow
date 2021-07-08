# Copyright 2020 Akretion
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class BidSelectionWizard(models.TransientModel):
    _name = "bid.selection.wizard"
    _rec_name = "requisition_id"
    _description = "Confirm Bid Selection"

    requisition_id = fields.Many2one(
        string="Purchase Agreement",
        comodel_name="purchase.requisition",
        ondelete="set null",
        help="Related Purchase agreement to this Bid Selection",
    )

    selected_line_ids = fields.Many2many(
        string="Selected lines",
        comodel_name="purchase.order.line",
        relation="bid_wiz_selected_po_lines_ids",
        column1="bid_selection_wizard_id",
        column2="purchase_order_line_id",
        help="Selected purchase order lines",
    )

    # Technical field with all the order_lines related to requisition_id
    line_ids = fields.Many2many(
        string="All the Purchase Requisition lines",
        comodel_name="purchase.order.line",
        relation="bid_wiz_all_po_lines_ids",
        column1="bid_selection_wizard_id",
        column2="purchase_order_line_id",
    )

    def action_confirm_selected_lines(self):
        """
        - Confirm Purchase Orders with selected order_lines
        - Cancel Purchase Orders with no selected order_lines
        - Deactivate unselected order_lines (only in confirmed Purchase Orders)
        """
        po_to_confirm_ids = self.selected_line_ids.mapped("order_id")

        unselected_line_ids = self.line_ids - self.selected_line_ids
        po_with_unselected_line_ids = unselected_line_ids.mapped("order_id")
        po_to_cancel_ids = po_with_unselected_line_ids - po_to_confirm_ids

        # 1. Deactivate lines
        line_to_desactive_ids = unselected_line_ids.filtered(
            lambda l: l.state not in ("done", "cancel")
        )
        line_to_desactive_ids.unlink()

        # 2. Confirm - Cancel PO
        po_to_confirm_ids.button_confirm()
        po_to_cancel_ids.button_cancel()

        # 3. Put unselected requisition lines in a new remainder requisition:
        line_remove_keys = set()
        for line in self.selected_line_ids:
            key = False
            if line.requisition_line_id and line.state == 'purchase':
                key = (
                    line.requisition_line_id.product_id.id,
                    line.requisition_line_id.product_qty,
                    line.requisition_line_id.origin or False
                )
            if key:
                line_remove_keys.add(key)

        remainder_req = self.requisition_id.copy(
            {'origin': 'remainder of %s' % (self.requisition_id.name,)}
        )
        to_unlink_remainder_lines = self.env['purchase.requisition.line']
        for req_line in remainder_req.line_ids:
            key = (
                    req_line.product_id.id,
                    req_line.product_qty,
                    req_line.origin or False
                  )
            
            if key in line_remove_keys:
                to_unlink_remainder_lines |= req_line

        if len(to_unlink_remainder_lines) == len(remainder_req.line_ids):
            remainder_req.unlink()
        else:
            to_unlink_remainder_lines.unlink()

        # 4. Close Purchase Agreement and back to purchase.requisition form view
        self.requisition_id.action_done()

        req_form_xmlid = "purchase_requisition_selection.view_purchase_requisition_form"
        return {
            "type": "ir.actions.act_window",
            "view_id": self.env.ref(req_form_xmlid).id,
            "view_mode": "form",
            "res_model": "purchase.requisition",
            "res_id": self.requisition_id.id,
            "target": "current",
        }
