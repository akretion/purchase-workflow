# © 2026 Mathieu DELVA @ Akretion
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

{
    "name": "Purchase Order Supplierinfo Update",
    "summary": "Update product supplierinfo with the last purchase price",
    "version": "14.0.1.0.0",
    "category": "Purchase",
    "website": "https://github.com/OCA/purchase-workflow",
    "author": "Akretion, Odoo Community Association (OCA)",
    "license": "AGPL-3",
    "depends": ["purchase"],
    "data": [
        "security/ir.model.access.csv",
        "views/purchase_order.xml",
        "wizard/wizard_update_purchase_supplierinfo.xml",
    ],
}
