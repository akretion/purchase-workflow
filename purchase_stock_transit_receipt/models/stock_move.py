# Copyright 2026 Akretion
# @author Guillaume MASSON <guillaume.masson@akretion.com>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import _, api, fields, models
from odoo.exceptions import UserError
from odoo.tools import float_compare


class StockMove(models.Model):
    _inherit = "stock.move"

    transit_move_dest_ids = fields.Many2many(
        comodel_name="stock.move",
        relation="stock_move_transit_move_rel",
        column1="transit_move_orig_id",
        column2="transit_move_dest_id",
        string="Destination Moves after Transit",
        copy=False,
    )
    transit_move_orig_ids = fields.Many2many(
        comodel_name="stock.move",
        relation="stock_move_transit_move_rel",
        column1="transit_move_dest_id",
        column2="transit_move_orig_id",
        string="Original Transit Moves",
        copy=False,
    )

    @api.depends("transit_move_orig_ids.date", "transit_move_orig_ids.state")
    def _compute_delay_alert_date(self):
        res = super()._compute_delay_alert_date()
        for move in self.filtered(lambda m: m.state not in ("done", "cancel")):
            transit_date = max(
                move.transit_move_orig_ids.filtered(
                    lambda m: m.state not in ("done", "cancel") and m.date
                ).mapped("date"),
                default=False,
            )
            if transit_date and transit_date > (move.delay_alert_date or move.date):
                move.delay_alert_date = transit_date
        return res

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

    def _action_cancel(self):
        physical_moves = self._get_physical_moves_left_without_transit()
        res = super()._action_cancel()
        physical_moves = physical_moves.filtered(lambda move: move.state != "cancel")
        if physical_moves:
            move_dests = physical_moves.move_dest_ids
            physical_moves._action_cancel()
            move_dests.filtered(
                lambda move: move.state not in ("done", "cancel")
            )._recompute_state()
        return res

    def _get_physical_moves_left_without_transit(self):
        transit_locations = self.env[
            "stock.warehouse"
        ]._get_incoming_transit_locations()
        transit_moves = self.filtered(
            lambda move: move.state != "cancel"
            and move.location_dest_id in transit_locations
        )
        return transit_moves.move_dest_ids.filtered(
            lambda move: move.state not in ("done", "cancel")
            and move.location_id in transit_locations
            and all(
                state == "cancel"
                for state in (move.move_orig_ids - transit_moves).mapped("state")
            )
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

    def _get_open_transit_move_dests(self):
        return self.transit_move_dest_ids.filtered(
            lambda move: move.state not in ("done", "cancel")
        )

    def _prepare_move_split_vals(self, qty):
        values = super()._prepare_move_split_vals(qty)
        move_dests = self._get_open_transit_move_dests()
        if move_dests:
            values["transit_move_dest_ids"] = [(6, 0, move_dests.ids)]
        return values

    def _merge_moves_fields(self):
        values = super()._merge_moves_fields()
        if self.transit_move_dest_ids:
            values["transit_move_dest_ids"] = [
                (4, move.id) for move in self.transit_move_dest_ids
            ]
        return values
