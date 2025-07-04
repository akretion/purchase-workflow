# -*- coding: utf-8 -*-
from collections import defaultdict
from odoo import api, fields, models, _
from odoo.exceptions import UserError

class PurchaseBillMatch(models.Model):
    _name = "purchase.bill.line.match"
    _description = "Purchase Line and Vendor Bill line matching view"
    _auto = False
    _order = 'product_id, aml_id, pol_id'

    pol_id = fields.Many2one(comodel_name='purchase.order.line', readonly=True)
    aml_id = fields.Many2one(comodel_name='account.move.line', readonly=True)
    company_id = fields.Many2one(comodel_name='res.company', readonly=True)
    partner_id = fields.Many2one(comodel_name='res.partner', readonly=True)
    product_id = fields.Many2one(comodel_name='product.product', readonly=True)
    line_qty = fields.Float(readonly=True)
    line_uom_id = fields.Many2one(comodel_name='uom.uom', readonly=True)
    qty_invoiced = fields.Float(readonly=True)
    purchase_order_id = fields.Many2one(comodel_name='purchase.order', readonly=True)
    account_move_id = fields.Many2one(comodel_name='account.move', readonly=True)
    line_amount_untaxed = fields.Monetary(readonly=True)
    currency_id = fields.Many2one(comodel_name='res.currency', readonly=True)
    state = fields.Char(readonly=True)

    product_uom_id = fields.Many2one(comodel_name='uom.uom', related='product_id.uom_id')
    product_uom_qty = fields.Float(compute='_compute_product_uom_qty', inverse='_inverse_product_uom_qty', readonly=False)
    product_uom_price = fields.Float(compute='_compute_product_uom_price', inverse='_inverse_product_uom_price', readonly=False)
    billed_amount_untaxed = fields.Monetary(compute='_compute_amount_untaxed_fields', currency_field='currency_id')
    purchase_amount_untaxed = fields.Monetary(compute='_compute_amount_untaxed_fields', currency_field='currency_id')
    reference = fields.Char(compute='_compute_reference')

    @api.onchange('product_uom_price')
    def _inverse_product_uom_price(self):
        for line in self:
            if line.aml_id:
                line.aml_id.price_unit = line.product_uom_price
            else:
                line.pol_id.price_unit = line.product_uom_price

    @api.onchange('product_uom_qty')
    def _inverse_product_uom_qty(self):
        for line in self:
            if line.aml_id:
                line.aml_id.quantity = line.product_uom_qty
            else:
                previous_price_unit = line.pol_id.price_unit
                line.pol_id.product_qty = line.product_uom_qty
                line.pol_id.price_unit = previous_price_unit

    def _compute_amount_untaxed_fields(self):
        for line in self:
            line.billed_amount_untaxed = line.line_amount_untaxed if line.account_move_id else False
            line.purchase_amount_untaxed = line.line_amount_untaxed if line.purchase_order_id else False

    def _compute_reference(self):
        for line in self:
            line.reference = line.purchase_order_id.name or line.account_move_id.name

    def _compute_display_name(self):
        for line in self:
            line.display_name = line.product_id.display_name or line.aml_id.name or line.pol_id.name

    def _compute_product_uom_qty(self):
        for line in self:
            if line.line_uom_id:
                line.product_uom_qty = line.line_uom_id._compute_quantity(line.line_qty, line.product_uom_id)
            else:
                line.product_uom_qty = 0.0

    @api.depends('aml_id.price_unit', 'pol_id.price_unit')
    def _compute_product_uom_price(self):
        for line in self:
            line.product_uom_price = line.aml_id.price_unit if line.aml_id else line.pol_id.price_unit

    @api.model
    def _select_po_line(self):
        return """
            SELECT pol.id,
                   pol.id as pol_id,
                   NULL as aml_id,
                   pol.company_id as company_id,
                   pol.partner_id as partner_id,
                   pol.product_id as product_id,
                   pol.product_qty as line_qty,
                   pol.product_uom as line_uom_id,
                   pol.qty_invoiced as qty_invoiced,
                   po.id as purchase_order_id,
                   NULL as account_move_id,
                   pol.price_subtotal as line_amount_untaxed,
                   pol.currency_id as currency_id,
                   po.state as state
              FROM purchase_order_line pol
         LEFT JOIN purchase_order po ON pol.order_id = po.id
             WHERE pol.state in ('purchase', 'done')
               AND (pol.product_qty > pol.qty_invoiced
                OR (pol.is_downpayment AND pol.qty_invoiced > 0))
        """

    @api.model
    def _select_am_line(self):
        return """
            SELECT -aml.id as id,
                   NULL as pol_id,
                   aml.id as aml_id,
                   aml.company_id as company_id,
                   aml.partner_id as partner_id,
                   aml.product_id as product_id,
                   aml.quantity as line_qty,
                   aml.product_uom_id as line_uom_id,
                   NULL as qty_invoiced,
                   NULL as purchase_order_id,
                   am.id as account_move_id,
                   aml.price_subtotal as line_amount_untaxed,
                   aml.currency_id as currency_id,
                   am.state as state
              FROM account_move_line aml
         LEFT JOIN account_move am on aml.move_id = am.id
             WHERE aml.display_type = 'product'
               AND am.move_type in ('in_invoice', 'in_refund')
               AND am.state in ('draft', 'posted')
               AND aml.purchase_line_id IS NULL
        """

    @property
    def _table_query(self):
        return '(%s) UNION ALL (%s)' % (self._select_po_line(), self._select_am_line())

    def action_open_line(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'account.move' if self.account_move_id else 'purchase.order',
            'view_mode': 'form',
            'res_id': self.account_move_id.id if self.account_move_id else self.purchase_order_id.id,
        }

    @api.model
    def _action_create_bill_from_po_lines(self, partner, po_lines):
        bill_vals = {
            'move_type': 'in_invoice',
            'partner_id': partner.id,
            'invoice_date': fields.Date.context_today(self),
        }
        bill = self.env['account.move'].with_context(default_move_type='in_invoice').create(bill_vals)
        for po_line in po_lines:
            bill.invoice_line_ids.create(po_line._prepare_account_move_line(bill))

        action = self.env["ir.actions.actions"]._for_xml_id("account.action_move_in_invoice_type")
        action.update({
            'view_mode': 'form',
            'res_id': bill.id,
            'views': [[self.env.ref('account.view_move_form').id, 'form']],
        })
        return action

    def action_match_lines(self):
        if not self.pol_id:
            raise UserError(_("You must select at least one Purchase Order line to match or create bill."))
        if not self.aml_id:
            return self._action_create_bill_from_po_lines(self.partner_id, self.pol_id)
        if len(self.aml_id.move_id) > 1:
            raise UserError(_("You can't select lines from multiple Vendor Bill to do the matching."))

        # Fix: Replace .grouped() with a defaultdict implementation
        pol_by_product = defaultdict(lambda: self.env['purchase.order.line'])
        for line in self.pol_id:
            pol_by_product[line.product_id] |= line

        aml_by_product = defaultdict(lambda: self.env['account.move.line'])
        for line in self.aml_id:
            aml_by_product[line.product_id] |= line

        residual_purchase_order_lines = self.pol_id
        residual_account_move_lines = self.aml_id
        residual_bill = self.aml_id.move_id

        for product, po_lines in pol_by_product.items():
            po_line = po_lines[0]
            matching_bill_lines = aml_by_product.get(product)
            if matching_bill_lines:
                matching_bill_lines.purchase_line_id = po_line.id
                residual_purchase_order_lines -= po_line
                residual_account_move_lines -= matching_bill_lines

        if residual_account_move_lines:
            residual_account_move_lines.unlink()

        if residual_purchase_order_lines:
            residual_bill._add_purchase_order_lines(residual_purchase_order_lines)

    def action_add_to_po(self):
        if not self or not self.aml_id:
            raise UserError(_("Select Vendor Bill lines to add to a Purchase Order"))
        context = {
            'default_partner_id': self.partner_id.id,
            'dialog_size': 'medium',
            'has_products': bool(self.aml_id.product_id),
            'active_model': 'purchase.bill.line.match',
            'active_ids': self.ids,
        }
        if len(self.purchase_order_id) > 1:
            raise UserError(_("Vendor Bill lines can only be added to one Purchase Order."))
        elif self.purchase_order_id:
            context['default_purchase_order_id'] = self.purchase_order_id.id

        return {
            'type': 'ir.actions.act_window',
            'name': _("Add to Purchase Order"),
            'res_model': 'bill.to.po.wizard',
            'target': 'new',
            'view_mode': 'form',
            'context': context,
        }
