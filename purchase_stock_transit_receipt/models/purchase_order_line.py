# Copyright 2026 Akretion
# @author Guillaume MASSON <guillaume.masson@akretion.com>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, models


class PurchaseOrderLine(models.Model):
    _inherit = "purchase.order.line"

    @api.depends(
        "move_ids.move_dest_ids.state",
        "move_ids.move_dest_ids.product_uom_qty",
        "move_ids.move_dest_ids.returned_move_ids.state",
        "move_ids.move_dest_ids.returned_move_ids.product_uom_qty",
        "move_ids.move_dest_ids.returned_move_ids.returned_move_ids.state",
        "move_ids.move_dest_ids.returned_move_ids.returned_move_ids.product_uom_qty",
    )
    def _compute_qty_received(self):
        transit_locations = self.env[
            "stock.warehouse"
        ]._get_incoming_transit_locations()
        transit_lines = self.filtered(
            lambda line: line.qty_received_method == "stock_moves"
            and line._get_transit_moves(transit_locations)
        )
        res = super(PurchaseOrderLine, self - transit_lines)._compute_qty_received()
        for line in transit_lines:
            total = 0.0
            for move in line._get_qty_received_moves(transit_locations).filtered(
                lambda move: move.state == "done" and move.product_id == line.product_id
            ):
                quantity = move.product_uom._compute_quantity(
                    move.product_uom_qty, line.product_uom, rounding_method="HALF-UP"
                )
                if not move._is_purchase_return():
                    total += quantity
                elif move.to_refund:
                    total -= quantity
            line._track_qty_received(total)
            line.qty_received = total
        return res

    def _get_transit_moves(self, transit_locations):
        return self.move_ids.filtered(
            lambda move: move.location_id in transit_locations
            or move.location_dest_id in transit_locations
        )

    def _get_qty_received_moves(self, transit_locations):
        transit_moves = self._get_transit_moves(transit_locations)
        physical_moves = transit_moves.move_dest_ids.filtered(
            lambda move: not move.origin_returned_move_id
            and move.location_id in transit_locations
        )
        returns = physical_moves.returned_move_ids
        return (
            (self.move_ids - transit_moves)
            | physical_moves
            | returns
            | returns.returned_move_ids
        )
