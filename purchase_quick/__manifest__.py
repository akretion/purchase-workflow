# coding: utf-8
# © 2014 Today Akretion
# @author Sébastien BEAU <sebastien.beau@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

{
    'name': 'Quick Purchase order',
    'version': '12.0.1.0.0',
    'author': 'Akretion, Odoo Community Association (OCA)',
    'website': 'https://github.com/OCA/purchase-workflow',
    'license': 'AGPL-3',
    'category': 'Purchase',
    'depends': [
        'purchase',
        'onchange_helper',
        'stock',
    ],
    'data': [
        'views/purchase_view.xml',
        'views/product_view.xml',
    ],
    'installable': True,
}
