# coding: utf-8
# © 2014 Sébastien Beau @ Akretion
# © 2014 Florian Da Costa @ Akretion
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).


{
    'name': 'Purchase Lot',
    'version': '10.0.1.0.0',
    'category': 'Purchase',
    'description': """
        Purchase a specific lot number linked to the lot sold
    """,
    'author': 'Akretion',
    'website': '',
    'depends': [
        'purchase',
        'sale_order_lot_selection',
        ],
    'data': [
        'views/purchase_view.xml',
        ],
    'installable': True,
}
