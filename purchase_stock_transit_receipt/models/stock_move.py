# Copyright 2026 Akretion
# @author Guillaume MASSON <guillaume.masson@akretion.com>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import _, models
from odoo.exceptions import UserError
from odoo.tools import float_compare


class StockMove(models.Model):
    _inherit = "stock.move"

    def _is_purchase_return(self):
        if super()._is_purchase_return():
            return True
        physical_move = self.origin_returned_move_id
        if not (
            self.location_dest_id.usage == "transit"
            and physical_move.location_id.usage == "transit"
            and physical_move.location_dest_id.usage == "internal"
        ):
            return False
        transit_locations = self.env[
            "stock.warehouse"
        ]._get_incoming_transit_locations()
        return (
            self.location_dest_id in transit_locations
            and physical_move.location_id in transit_locations
        )

    def _action_done(self, cancel_backorder=False):
        self._check_quantity_in_transit()
        return super()._action_done(cancel_backorder=cancel_backorder)

    def _check_quantity_in_transit(self):
        transit_locations = self.env[
            "stock.warehouse"
        ]._get_incoming_transit_locations()
        for move in self.filtered(
            lambda m: m.location_id in transit_locations and m.move_orig_ids
        ):
            arrived_moves = move.move_orig_ids.filtered(lambda m: m.state == "done")
            left_moves = (arrived_moves.move_dest_ids - move).filtered(
                lambda m: m.state == "done"
            )
            quantity_in_transit = sum(arrived_moves.mapped("product_qty")) - sum(
                left_moves.mapped("product_qty")
            )
            quantity_done = move.product_uom._compute_quantity(
                move.quantity_done, move.product_id.uom_id
            )
            if (
                float_compare(
                    quantity_done,
                    quantity_in_transit,
                    precision_rounding=move.product_id.uom_id.rounding,
                )
                > 0
            ):
                raise UserError(
                    _(
                        "Only %(quantity)s %(product)s arrived in transit: "
                        "validate the Transit receipt first."
                    )
                    % {
                        "quantity": quantity_in_transit,
                        "product": move.product_id.display_name,
                    }
                )
