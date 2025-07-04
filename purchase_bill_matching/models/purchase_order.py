# -*- coding: utf-8 -*-
from odoo import models, fields, _, Command

class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    def action_bill_matching(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _("Bill Matching"),
            'res_model': 'purchase.bill.line.match',
            'domain': [
                ('partner_id', '=', self.partner_id.id),
                ('company_id', '=', self.company_id.id),
                ('purchase_order_id', 'in', [self.id, False]),
            ],
            'views': [(self.env.ref('purchase_bill_matching.purchase_bill_line_match_tree').id, 'list')],
            'context': self.env.context,
        }

    def _prepare_down_payment_section_values(self):
        self.ensure_one()
        return {
            'product_qty': 0.0,
            'order_id': self.id,
            'display_type': 'line_section',
            'is_downpayment': True,
            'sequence': (self.order_line[-1:].sequence or 9) + 1,
            'name': _("Down Payments"),
        }

    def _create_downpayments(self, line_vals):
        self.ensure_one()
        if not any(line.display_type and line.is_downpayment for line in self.order_line):
            self.env['purchase.order.line'].create(self._prepare_down_payment_section_values())

        # The lines are automatically linked to the PO via 'order_id' in their values.
        # No need to re-assign to self.order_line.
        downpayment_lines = self.env['purchase.order.line'].create(line_vals)
        return downpayment_lines

class PurchaseOrderLine(models.Model):
    _inherit = 'purchase.order.line'

    is_downpayment = fields.Boolean()

    def _prepare_account_move_line(self, move=False):
        res = super(PurchaseOrderLine, self)._prepare_account_move_line(move)
        res.update({'is_downpayment': self.is_downpayment})
        return res
