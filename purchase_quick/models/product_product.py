# © 2014 Today Akretion
# @author Sébastien BEAU <sebastien.beau@akretion.com>
# @author Mourad EL HADJ MIMOUNE <mourad.elhadj.mimoune@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).


from odoo import api, fields, models, _
from odoo.tests.common import Form


class ProductProduct(models.Model):
    _inherit = 'product.product'

    qty_to_purchase = fields.Float(
        compute='_compute_purchase_qty',
        inverse='_inverse_set_purchase_qty',
        oldname='purchase_qty',
        help="Set this quantity to create a new purchase line "
             "for this product or update the existing one."
    )
    po_line_ids = fields.One2many(
        comodel_name='purchase.order.line', inverse_name='product_id',
        help='Technical: used to compute quantities to purchase.',
    )

    def _prepare_purchase_line(self, purchase):
        return {
            'product_id': self.id,
            'product_qty': self.qty_to_purchase,
            'order_id': purchase.id,
        }

    def _get_purchase_line(self, purchase):
        return self.env['purchase.order.line'].search([
            ('product_id', '=', self.id),
            ('order_id', '=', purchase.id),
        ], limit=1)

    def _add_purchase_line(self, purchase):
        vals = self._prepare_purchase_line(purchase)
        # line = self.env['purchase.order.line'].new(vals)
        vals = self._complete_purchase_line_vals(False, vals)
        if not vals.get('price_unit'):
            vals['price_unit'] = 0.0
        self.env['purchase.order.line'].create(vals)

    def _update_purchase_line(self, purchase_line):
        if self.qty_to_purchase:
            # apply the on change to update price unit if depends on qty
            vals = {'product_qty': self.qty_to_purchase}
            self._complete_purchase_line_vals(purchase_line, vals)
            purchase_line.write(vals)
        else:
            purchase_line.unlink()

    def _complete_purchase_line_vals(self, line, vals):
        form_line = None
        line_view = 'purchase.purchase_order_line_form2'
        if line:
            form_line = Form(line, view=line_view)
        else:
            form_line = Form(self.env['purchase.order.line'], view=line_view)
        init_keys = ['product_id', 'order_id']
        init_vals = [(key, val) for key, val in vals.items()
                     if key in init_keys]
        form_line._values.update(init_vals)
        form_line._perform_onchange(init_keys)
        update_keys = [key for key in vals.keys() if key not in init_keys]
        update_vals = [(key, val) for key, val in vals.items()
                       if key not in init_keys]
        form_line._values.update(update_vals)
        form_line._perform_onchange(update_keys)
        if form_line.taxes_id:
            form_line.taxes_id = [(6, 0, form_line.taxes_id)]
        return form_line._values

    def _inverse_set_purchase_qty(self):
        purchase = self.env['purchase.order'].browse(
            self.env.context.get('purchase_id'))
        for product in self:
            purchase_line = self._get_purchase_line(purchase)
            if purchase_line:
                product._update_purchase_line(purchase_line)
            else:
                product._add_purchase_line(purchase)

    @api.depends('po_line_ids')
    def _compute_purchase_qty(self):
        if not self.env.context.get('purchase_id'):
            return
        for product in self:
            po_lines = self.env['purchase.order.line'].search([
                ('order_id', '=', self.env.context.get('purchase_id')),
                ('product_id', '=', product.id),
            ])
            for po_line in po_lines:
                product.qty_to_purchase += po_line.product_qty
        return

    @api.model
    def search(self, args, offset=0, limit=None, order=None, count=False):
        purchase = self.env['purchase.order'].browse(
            self.env.context.get('purchase_id'))
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

    @api.multi
    def button_return_purchase(self):
        self.ensure_one()
        purchase_id = self.env.context.get('purchase_id')
        if purchase_id:
            return {
                'name': _('Purchase'),
                'type': 'ir.actions.act_window',
                'res_model': 'purchase.order',
                'view_mode': 'form',
                'res_id': purchase_id,
            }
