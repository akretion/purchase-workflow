{
    'name': 'Purchase Bill Matching',
    'version': '16.0.1.0.0',
    'category': 'Inventory/Purchase',
    'summary': 'Backport of the v18 Bill Matching feature to Odoo 16.',
    'description': """
This module backports the bill matching feature from Odoo v18 to v16.
It introduces:
- A dedicated view to match vendor bill lines with purchase order lines.
- The ability to create down payment bills and link them to purchase orders.
- An improved autocomplete mechanism on vendor bills to fetch lines from purchase orders.
    """,
    'author': 'Gemini',
    'website': 'https://www.google.com',
    'depends': ['purchase', 'account'],
    'data': [
        'security/ir.model.access.csv',
        'views/account_move_views.xml',
        'views/purchase_views.xml',
        #'views/purchase_bill_line_match_views.xml',
        #'wizard/bill_to_po_wizard_views.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
    'license': 'LGPL-3',
}
