from odoo import fields, models


class PurchaseRequestImportProducts(models.TransientModel):
    _name = "purchase.request.import.products"
    _description = "Purchase Request Import Products"

    products = fields.Many2many(comodel_name="product.product")

    def create_items(self):
        purchase_request = self.env["purchase.request"].browse(
            self.env.context.get("active_id", False)
        )
        purchase_request_lines = [
            self.env["purchase.request.line"].create(
                {
                    "request_id": purchase_request.id,
                    "name": product.name,
                    "product_id": product.id,
                    "product_uom_id": product.uom_id.id,
                }
            )
            for wizard in self
            for product in wizard.products
        ]

        return {
            "name": "Set Products Informations",
            "type": "ir.actions.act_window",
            "res_model": "purchase.request.line",
            "view_mode": "tree",
            "views": [
                (
                    self.env.ref(
                        "purchase_request_product_multi_add.view_edit_new_purchase_request_lines"
                    ).id,
                    "tree",
                )
            ],
            "domain": [
                ("request_id", "=", purchase_request.id),
                (
                    "id",
                    "in",
                    [prl.id for prl in purchase_request_lines],
                ),
            ],
            "target": "new",
            "context": self.env.context,
        }
