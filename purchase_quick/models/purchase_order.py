# © 2014 Today Akretion
# @author Sébastien BEAU <sebastien.beau@akretion.com>
# @author Mourad EL HADJ MIMOUNE <mourad.elhadj.mimoune@akretion.com>
# @author Pierrick Brun <pierrick.brun@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import ast
from odoo import api, models


class PurchaseOrder(models.Model):
    _name = 'purchase.order'
    _inherit = ['purchase.order', 'product.mass.addition']

    @api.multi
    def add_product(self):
        self.ensure_one()
        action = self.env.ref('purchase.product_product_action')
        context = ast.literal_eval(action.context or "{}").copy()
        context.update({
            'parent_id': self.id,
            'parent_model': 'purchase.order'})
        result = action.read()[0]
        name = action.name + " (%s)" % self.partner_id.name
        result.update(
            {'target': 'current', 'context': context,
             'view_mode': 'tree', 'name': name})
        return result

    def _get_quick_line(self, product):
        return self.env['purchase.order.line'].search([
            ('product_id', '=', product.id),
            ('order_id', '=', self.id),
        ], limit=1)

    def _get_quick_line_qty_vals(self, product):
        return {'product_qty': product.qty_to_process}

    def _complete_quick_line_vals(self, vals, lines_key=''):
        return super(PurchaseOrder, self)._complete_quick_line_vals(
            vals, lines_key='order_line')

    def _add_quick_line(self, product, lines_key=''):
        return super(PurchaseOrder, self)._add_quick_line(
            product, lines_key='order_line')
