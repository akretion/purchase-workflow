# © 2014 Today Akretion
# @author Sébastien BEAU <sebastien.beau@akretion.com>
# @author Mourad EL HADJ MIMOUNE <mourad.elhadj.mimoune@akretion.com>
# @author Pierrick Brun <pierrick.brun@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).


from odoo import api, fields, models


class ProductProduct(models.Model):
    _inherit = 'product.product'

    po_line_ids = fields.One2many(
        comodel_name='purchase.order.line', inverse_name='product_id',
        help='Technical: used to compute quantities to purchase.',
    )

    def _get_quick_line(self, parent):
        if self.env.context['parent_model'] == 'purchase.order':
            return self.env['purchase.order.line'].search([
                ('product_id', '=', self.id),
                ('order_id', '=', parent.id),
            ], limit=1)

    def _get_quick_line_qty_vals(self):
        if self.env.context['parent_model'] == 'purchase.order':
            return {'product_qty': self.qty_to_process}

    def _complete_quick_line_vals(self, parent, vals,
                                  parent_key='', lines_key=''):
        if self.env.context['parent_model'] == 'purchase.order':
            lines_key = 'order_line'
            parent_key = 'order_id'
        return super(ProductProduct, self)._complete_quick_line_vals(
            parent, vals, parent_key=parent_key, lines_key=lines_key)

    @api.depends('po_line_ids')
    def _compute_process_qty(self):
        res = super(ProductProduct, self)._compute_process_qty()
        if self.env.context['parent_model'] == 'purchase.order':
            for product in self:
                po_lines = self.env['purchase.order.line'].search([
                    ('order_id', '=', self.env.context.get('parent_id')),
                    ('product_id', '=', product.id),
                ])
                for po_line in po_lines:
                    product.qty_to_process += po_line.product_qty
        return res

    @api.model
    def search(self, args, offset=0, limit=None, order=None, count=False):
        purchase = self.env['purchase.order'].browse(
            self.env.context.get('parent_id'))
        if self.env.context.get('in_current_purchase') and purchase:
            po_lines = self.env['purchase.order.line'].search(
                [('order_id', '=', purchase.id)])
            args.append(
                (('id', 'in', po_lines.mapped('product_id').ids)))
        if self.env.context.get('use_only_supplied_product') and purchase:
            seller = purchase.partner_id
            seller = seller.commercial_partner_id or seller
            supplierinfos = self.env['product.supplierinfo'].search(
                [('name', '=', seller.id)])
            args += [
                '|',
                ('product_tmpl_id', 'in',
                    [x.product_tmpl_id.id for x in supplierinfos]),
                ('id', 'in',
                    [x.product_id.id for x in supplierinfos])]
        return super(ProductProduct, self).search(
            args, offset=offset, limit=limit, order=order, count=count)
