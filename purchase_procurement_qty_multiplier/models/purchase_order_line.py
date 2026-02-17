from math import ceil
from odoo import _, models


class PurchaseOrderLine(models.Model):
    _inherit = "purchase.order.line"

    def _prepare_purchase_order_line_from_procurement(
        self,
        product_id,
        product_qty,
        product_uom,
        location_dest_id,
        name,
        origin,
        company_id,
        values,
        po,
    ):
        vals = super()._prepare_purchase_order_line_from_procurement(
            product_id,
            product_qty,
            product_uom,
            location_dest_id,
            name,
            origin,
            company_id,
            values,
            po,
        )
        seller = values["supplier"]

        if (
            seller
            and seller.multiplier_qty
            and vals["product_qty"] % seller.multiplier_qty
        ):
            vals["product_qty"] = (
                ceil(vals["product_qty"] / seller.multiplier_qty)
                * seller.multiplier_qty
            )
            self.env.user.notify_warning(
                title=_("Warning"),
                message=_(
                    "The selected supplier only sells this product"
                    " by %(multiplier_qty)s %(uom_name)s.\n"
                    "The quantity has been automatically changed"
                    " to %(new_product_qty)s %(uom_name)s."
                )
                % (
                    {
                        "multiplier_qty": seller.multiplier_qty,
                        "uom_name": seller.product_uom.name,
                        "new_product_qty": self.product_qty,
                    }
                ),
            )

        return vals
