# Copyright 2020 Akretion
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    "name": "Purchase Requisition Selection",
    "summary": """Help selecting the best order lines from your suppliers bids""",
    "version": "16.0.1.0.0",
    "license": "AGPL-3",
    "author": "Akretion,Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/purchase-workflow",
    "depends": ["purchase_requisition"],
    "data": [
        # Security
        "security/ir.model.access.csv",
        # Views
        "views/purchase_order.xml",
        "views/purchase_order_line.xml",
        "views/purchase_requisition.xml",
        # Wizard
        "wizard/bid_selection_wizard_views.xml",
    ],
}
