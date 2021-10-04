# Copyright 2019 ForgeFlow S.L.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models
from odoo.tools import float_compare

from odoo.addons import decimal_precision as dp


class PurchaseOrder(models.Model):
    _inherit = "purchase.order"

    pending_to_receive = fields.Boolean(compute="_compute_pending_to_receive")

    def _compute_pending_to_receive(self):
        for order in self:
            order.pending_to_receive = True
            if all(
                val is False for val in order.mapped("order_line.pending_to_receive")
            ):
                order.pending_to_receive = False

    def button_confirm_manual(self):
        super(PurchaseOrder, self.with_context(manual_delivery=True)).button_confirm()

    def _create_picking(self):
        if self.env.context.get("manual_delivery", False):
            # We do not want to create the picking when confirming the order
            # if it comes from manual confirmation
            return
        return super()._create_picking()

    def _get_destination_location(self):
        """Override in order to avoid using PO's original picking type and dropship
        address"""
        res = super()._get_destination_location()
        manual_picking = self.env.context.get("manual_picking")

        if manual_picking:
            if manual_picking.dest_address_id:
                res = manual_picking.dest_address_id.property_stock_customer.id
            elif manual_picking.picking_type_id:
                res = manual_picking.picking_type_id.default_location_dest_id.id
        return res

    def _prepare_picking(self):
        """Override in order to avoid using PO's original picking type"""
        res = super()._prepare_picking()
        manual_picking = self.env.context.get("manual_picking")
        if manual_picking:
            res["picking_type_id"] = manual_picking.picking_type_id.id
        return res


class PurchaseOrderLine(models.Model):
    _inherit = "purchase.order.line"

    qty_in_receipt = fields.Float(
        compute="_compute_qty_in_receipt",
        string="In Receipt Qty",
        compute_sudo=True,
        store=True,
        digits="Product Unit of Measure",
        help="Quantity already planned to receive",
    )
    pending_to_receive = fields.Boolean(
        compute="_compute_qty_in_receipt",
        compute_sudo=True,
        store=True,
        string="Pending Qty to Receive",
        help="There is pending quantity to receive not yet planned",
    )

    @api.depends(
        "move_ids",
        "move_ids.state",
        "move_ids.location_id",
        "move_ids.location_dest_id",
    )
    def _compute_qty_in_receipt(self):
        for line in self:
            rounding = line.company_id.currency_id.rounding
            total = 0.0
            for move in line.move_ids:
                if move.state not in ["done", "cancel"]:
                    if move.location_dest_id.usage == "supplier":
                        if move.to_refund:
                            total -= move.product_uom._compute_quantity(
                                move.product_uom_qty, line.product_uom
                            )
                    elif (
                        move.origin_returned_move_id
                        and move.origin_returned_move_id._is_dropshipped()
                        and not move._is_dropshipped_returned()
                    ):
                        # Edge case: the dropship is returned to the stock,
                        # no to the supplier.
                        # In this case, the received quantity on the PO is
                        # set although we didn't receive the product
                        # physically in our stock. To avoid counting the
                        # quantity twice, we do nothing.
                        pass
                    else:
                        total += move.product_uom._compute_quantity(
                            move.product_uom_qty, line.product_uom
                        )
            line.qty_in_receipt = total
            if float_compare(
                line.product_uom_qty - line.qty_received,
                line.qty_in_receipt,
                precision_rounding=rounding,
            ):
                line.pending_to_receive = True
            else:
                line.pending_to_receive = False

    def _prepare_stock_move_vals(
        self, picking, price_unit, product_uom_qty, product_uom
    ):
        """Override in order to avoid using PO's original picking type and dropship
        address"""
        # TODO: override also '_check_orderpoint_picking_type' as it is based
        # on order_id's picking_type_id too

        res = super()._prepare_stock_move_vals(
            picking, price_unit, product_uom_qty, product_uom
        )
        manual_picking = self.env.context.get("manual_picking")

        if manual_picking:
            picking_type_id = manual_picking.picking_type_id
            dest_address_id = manual_picking.dest_address_id
            # New description_picking
            product = self.product_id.with_context(
                lang=dest_address_id.lang or self.env.user.lang
            )
            description_picking = product._get_description(picking_type_id)
            if self.product_description_variants:
                description_picking += "\n" + self.product_description_variants

            # Update pickint_type and warehouse
            res.update(
                {
                    "partner_id": dest_address_id.id,
                    "picking_type_id": picking_type_id.id,
                    "warehouse_id": picking_type_id.warehouse_id.id,
                }
            )

        return res
