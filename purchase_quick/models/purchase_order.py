# © 2014 Today Akretion
# @author Sébastien BEAU <sebastien.beau@akretion.com>
# @author Mourad EL HADJ MIMOUNE <mourad.elhadj.mimoune@akretion.com>
# @author Pierrick Brun <pierrick.brun@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import api, models, _


class PurchaseOrder(models.Model):
    _name = 'purchase.order'
    _inherit = ['purchase.order', 'product.mass.addition']

    @api.multi
    def add_product(self):
        self.ensure_one()
        context = {
            'search_default_filter_to_purchase': 1,
            'search_default_filter_for_current_supplier': 1,
            'parent_id': self.id,
            'parent_model': 'purchase.order',
        }
        commercial = self.partner_id.commercial_partner_id.name
        name = "🔙 %s (%s)" % (_('Product Variants'), commercial)
        return {
            'name': name,
            'type': 'ir.actions.act_window',
            'res_model': 'product.product',
            'target': 'current',
            'context': context,
            'view_mode': 'tree',
            'view_id': self.env.ref(
                'base_product_mass_addition.product_product_tree_view').id,
        }

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
