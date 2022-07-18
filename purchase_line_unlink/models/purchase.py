# Copyright 2022 Akretion
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from collections import defaultdict
from odoo import api, fields, models, _
from odoo.exceptions import UserError


MESSAGE = "Cannot delete a purchase order line which is in state"


class PurchaseOrderLine(models.Model):
    _inherit = "purchase.order.line"

    def _get_invoice_policy(self):
        self.ensure_one()
        if self.product_id:
            return self.product_id.purchase_method
        elif self.display_type:
            return "no"

    def _remove_dependency_lines_before_unlink(self):
        """lines => {"po_id purchase.order": {
            "purchase": [po_line_id purchase.order.line],
            "receive": [po_line_id purchase.order.line],
            "no": [po_line_id purchase.order.line],
        }
        """
        unlinkable = {}
        lines = defaultdict(dict)
        for rec in self:
            # if rec.order_id and rec.order_id.state in ("draft", "sent", "to approve"):
            if rec.order_id:
                policy = rec._get_invoice_policy()
                if policy not in lines:
                    lines[rec.order_id][policy] = []
                lines[rec.order_id][policy].append(rec.id)
        for po, policy_data in lines.items():
            # if "receive" in policy_data:
            if "purchase" in policy_data.keys():
                unlinkable.update(
                    self.browse(policy_data["purchase"])._unlinkable_move_lines()
                )
                import pdb; pdb.set_trace()
                unlinkable.update(
                    self.browse(policy_data["purchase"])._unlinkable_stock_moves()
                )
            # if "no" in policy_data:
            #     unlinkable[po]
            #     pol2unlink.extend(policy_data["no"])
            return unlinkable

    def _unlinkable_stock_moves(self):
        self.ensure_one()
        unlinkable = defaultdict(dict)
        for pol in self:
            relevant_state = pol.move_ids._get_relevant_state_among_moves()
            if relevant_state == "assigned":
                pol.move_ids.filtered(lambda s: s.state == "assigned")._do_unreserve()
            pol.move_ids._action_cancel()
            moves = pol.move_ids
            states = pol.move_ids.mapped("state")
            if sorted(states) == ["cancel", "draft"]:
                import pdb; pdb.set_trace()
                unlinkable[pol.id]["stk"] = moves.ids
        return unlinkable

    def _unlinkable_move_lines(self):
        self.ensure_one()
        unlinkable = defaultdict(dict)
        # pol2unlink = []
        for pol in self:
            lines = pol.invoice_lines
            state = lines.mapped("parent_state")
            if len(state) == 1 and state[0] == "draft":
                line_ids = []
                for move in lines.mapped("move_id"):
                    line_ids.extend(move.line_ids.ids)
                unlinkable[pol.id]["inv"] = line_ids
                # pol2unlink.append(pol.id)
        return unlinkable

    def unlink(self):
        """We need to catch raise behavior when"""
        pol2unlink = self._remove_dependency_lines_before_unlink()
        if pol2unlink:
            pol2unlink = self.browse(pol2unlink)
            unlinkable_lines = self - pol2unlink
            self = pol2unlink
        # try:
        # except UserError as err:
        # if len(self) == 1:
        # import pdb; pdb.set_trace()
        res = super().unlink()
        return res
        # if self._bypass_unlink_alert():
        #     return True
        # else:
        #     return super().unlink()

        # import pdb; pdb.set_trace()
        # if self.order_id.state in ["purchase"]:
        #     # if hasattr(err, "name") and err.name[:53] == _(MESSAGE):
        #             # if self._bypass_unlink_alert():
        #             #     return True
        #             # else:
        #             #     return super().unlink()
        # # raise err
        # else:
        #     return super().unlink()

    # def _bypass_unlink_alert(self):
    #     moves = self.move_ids
    #     moves._action_cancel()
    #     ppg_cancel_lines = self.filtered(lambda line: line.propagate_cancel)
    #     ppg_cancel_lines.move_dest_ids._action_cancel()
    #     not_ppg_cancel_lines = self.filtered(
    #         lambda line: not line.propagate_cancel
    #     )
    #     not_ppg_cancel_lines.move_dest_ids.write(
    #         {"procure_method": "make_to_stock"}
    #     )
    #     not_ppg_cancel_lines.move_dest_ids._recompute_state()
    #     return True
