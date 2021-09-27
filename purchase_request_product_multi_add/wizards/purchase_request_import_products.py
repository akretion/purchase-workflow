from odoo import api, fields, models


class PurchaseRequestImportProducts(models.TransientModel):
    _name = "purchase.request.import.products"
    _description = "Purchase Request Import Products"

    products = fields.Many2many(comodel_name="product.product")
    items = fields.One2many(
        comodel_name="purchase.request.import.products.items",
        inverse_name="wizard_id",
    )

    def create_items(self):
        for wizard in self:
            for product in wizard.products:
                self.env["purchase.request.import.products.items"].create(
                    {"wizard_id": wizard.id, "product_id": product.id}
                )
        view = self.env.ref(
            "purchase_request_product_multi_add.view_import_product_to_purchase_request2"
        )
        return {
            "type": "ir.actions.act_window",
            "res_model": self._name,
            "view_type": "form",
            "view_mode": "form",
            "views": [(view.id, "form")],
            "target": "new",
            "res_id": self.id,
            "context": self.env.context,
        }

    @api.model
    def _get_line_values(self, purchase_request, item):
        purchase_request_line = self.env["purchase.request.line"].new(
            {
                "request_id": purchase_request.id,
                "name": item.product_id.name,
                "product_id": item.product_id.id,
                "product_qty": item.quantity,
                "product_uom_id": item.product_id.uom_id.id,
            }
        )
        purchase_request_line.onchange_product_id()  # ?
        line_values = purchase_request_line._convert_to_write(
            purchase_request_line._cache
        )
        return line_values

    def select_products(self):
        pr_obj = self.env["purchase.request"]
        for wizard in self:
            purchase_request = pr_obj.browse(self.env.context.get("active_id", False))

            if purchase_request:
                for item in wizard.items:
                    vals = self._get_line_values(purchase_request, item)
                    if vals:
                        self.env["purchase.request.line"].create(vals)

        return {"type": "ir.actions.act_window_close"}


class PurchaseRequestImportProductsItem(models.TransientModel):
    _name = "purchase.request.import.products.items"
    _description = "PurchaseRequest Import Products Items"

    wizard_id = fields.Many2one(
        string="Wizard", comodel_name="purchase.request.import.products"
    )
    product_id = fields.Many2one(
        string="Product", comodel_name="product.product", required=True
    )
    quantity = fields.Float(
        digits="Product Unit of Measure", default=1.0, required=True
    )
