# Copyright 2020 Akretion
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    'name': 'Purchase Tender Management',
    'description': """
        Help selecting the best order lines from your suppliers bids""",
    'version': '12.0.1.0.0',
    'license': 'AGPL-3',
    'author': 'Akretion,Odoo Community Association (OCA)',
    'website': 'https://akretion.com/',
    'depends': [
        "purchase_requisition"
    ],
    "data": [
        "views/purchase_order_views.xml",
        "views/purchase_requisition_views.xml",
        "wizard/bid_selection_wizard_views.xml",
    ],
}
