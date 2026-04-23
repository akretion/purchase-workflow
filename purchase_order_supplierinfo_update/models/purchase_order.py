# Copyright 2025 Mathieu DElVA @ Akretion
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import _, fields, models
from odoo.exceptions import UserError


class PurchaseOrder(models.Model):
    _inherit = "purchase.order"

    all_supplierinfo_price_ok = fields.Boolean(
        compute="_compute_all_supplierinfo_price_ok",
    )

    def _compute_all_supplierinfo_price_ok(self):
        for purchase in self:
            order_line = purchase.order_line.filtered(
                lambda r: r.supplierinfo_price_exist
            )
            if not order_line:
                purchase.all_supplierinfo_price_ok = True
            else:
                purchase.all_supplierinfo_price_ok = all(
                    order_line.mapped("supplierinfo_price_ok")
                )

    def _get_update_supplierinfo_lines(self):
        self.ensure_one()
        lines = []
        product_ids = []
        for line in self.order_line.filtered(
            lambda r: r.product_id and not r.supplierinfo_price_ok
        ):

            supplierinfo = line.product_id._select_seller(
                partner_id=line.order_id.partner_id.commercial_partner_id,
                quantity=line.product_qty,
                date=line.order_id.date_order.date(),
                uom_id=line.product_uom,
            )
            if any(
                d["product_id"] == line.product_id.id
                and d["supp_info"] == supplierinfo.id
                for d in product_ids
            ):
                continue
            product_ids.append(
                {"supp_info": supplierinfo.id, "product_id": line.product_id.id}
            )

            if supplierinfo:
                if line._is_matching_supplierinfo(supplierinfo):
                    continue

                lines.append((0, 0, line._prepare_supplier_wizard_line(supplierinfo)))
        return lines

    def supplierinfo_update_price(self):
        self.ensure_one()
        lines_for_update = self._get_update_supplierinfo_lines()
        if not lines_for_update:
            raise UserError(_("No lines found to update."))
        else:
            ctx = {
                "default_line_ids": lines_for_update,
                "default_purchase_id": self.id,
            }

            view_form = self.env.ref(
                "purchase_order_supplierinfo_update."
                "view_wizard_update_purchase_supplierinfo_form"
            )
            return {
                "name": (_("Update supplier informations of products")),
                "type": "ir.actions.act_window",
                "view_mode": "form",
                "res_model": "wizard.update.purchase.supplierinfo",
                "views": [(view_form.id, "form")],
                "view_id": view_form.id,
                "target": "new",
                "context": ctx,
            }
