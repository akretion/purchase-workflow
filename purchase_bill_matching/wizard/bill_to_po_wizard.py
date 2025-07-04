# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import UserError

class BillToPoWizard(models.TransientModel):
    _name = 'bill.to.po.wizard'
    _description = "Wizard to add bill lines to PO"

    purchase_order_id = fields.Many2one('purchase.order', string="Purchase Order")
    partner_id = fields.Many2one('res.partner', string="Vendor", required=True)
    has_products = fields.Boolean()

    def _get_active_lines(self):
        active_ids = self.env.context.get('active_ids', [])
        return self.env['purchase.bill.line.match'].browse(active_ids)

    def _get_downpayment_product(self):
        """Finds or creates a default 'Down Payment' product."""
        dp_product = self.env['product.product'].search([('name', '=', 'Down Payment'), ('type', '=', 'service')], limit=1)
        if not dp_product:
            dp_product = self.env['product.product'].create({
                'name': 'Down Payment',
                'type': 'service',
                'purchase_ok': True,
                'sale_ok': False,
                # In v16, for a service product, purchase_method defaults to 'purchase', which is correct for down payments.
                'taxes_id': False,
            })
        return dp_product

    def action_add_to_po(self):
        self.ensure_one()
        lines = self._get_active_lines()
        aml_ids = lines.mapped('aml_id')

        if not self.purchase_order_id:
            self.purchase_order_id = self.env['purchase.order'].create({'partner_id': self.partner_id.id})

        po_lines_vals = aml_ids._prepare_line_values_for_purchase()
        for vals in po_lines_vals:
            vals['order_id'] = self.purchase_order_id.id
            self.env['purchase.order.line'].create(vals)

        aml_ids.unlink()

        action = self.env["ir.actions.actions"]._for_xml_id("purchase.purchase_form_action")
        action['views'] = [(self.env.ref('purchase.purchase_order_form').id, 'form')]
        action['res_id'] = self.purchase_order_id.id
        return action

    def action_add_downpayment(self):
        self.ensure_one()
        lines = self._get_active_lines()
        aml_ids = lines.mapped('aml_id')

        if not self.purchase_order_id:
            self.purchase_order_id = self.env['purchase.order'].create({'partner_id': self.partner_id.id})

        dp_product = self._get_downpayment_product()

        po_lines_vals = [
            {
                'name': _("Down Payment: %s", line.move_id.name or line.name),
                'product_id': dp_product.id,
                'product_qty': 1,
                'price_unit': -line.price_subtotal,  # Negative price to represent a deduction
                'is_downpayment': True,
                'order_id': self.purchase_order_id.id,
                'product_uom': dp_product.uom_po_id.id,
                'date_planned': self.purchase_order_id.date_planned or fields.Date.today(),
            }
            for line in aml_ids
        ]

        dp_lines = self.purchase_order_id._create_downpayments(po_lines_vals)
        for i, line in enumerate(aml_ids):
            line.purchase_line_id = dp_lines[i]

        action = self.env["ir.actions.actions"]._for_xml_id("purchase.purchase_form_action")
        action['views'] = [(self.env.ref('purchase.purchase_order_form').id, 'form')]
        action['res_id'] = self.purchase_order_id.id
        return action
