from math import ceil
from odoo import _, models


class StockRule(models.Model):
    _inherit = "stock.rule"

    def _update_purchase_order_line(
        self, product_id, qty, uom, company_id, procurement_values, po_line
    ):
        vals = super()._update_purchase_order_line(
            product_id, qty, uom, company_id, procurement_values, po_line
        )

        seller = procurement_values.get("supplier")

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
