# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo.addons.account.tests.common import AccountTestInvoicingCommon
from odoo.exceptions import UserError
from odoo.tests import Form, tagged


@tagged('post_install', '-at_install')
class TestBillMatching(AccountTestInvoicingCommon):

    @classmethod
    def setUpClass(cls, chart_template_ref=None):
        super().setUpClass(chart_template_ref=chart_template_ref)

        uom_unit = cls.env.ref('uom.product_uom_unit')
        uom_hour = cls.env.ref('uom.product_uom_hour')

        cls.product_order = cls.env['product.product'].create({
            'name': "Test Product Ordered",
            'standard_price': 235.0,
            'list_price': 280.0,
            'type': 'consu',
            'uom_id': uom_unit.id,
            'uom_po_id': uom_unit.id,
            'purchase_method': 'purchase',
            'taxes_id': False,
        })
        cls.product_order_var_name = cls.env['product.product'].create({
            'name': "Test Product Ordered Var Name",
            'standard_price': 235.0,
            'list_price': 280.0,
            'type': 'consu',
            'uom_id': uom_unit.id,
            'uom_po_id': uom_unit.id,
            'purchase_method': 'purchase',
            'taxes_id': False,
        })
        cls.service_deliver = cls.env['product.product'].create({
            'name': "Test Service Delivered",
            'standard_price': 200.0,
            'list_price': 180.0,
            'type': 'service',
            'uom_id': uom_unit.id,
            'uom_po_id': uom_unit.id,
            'purchase_method': 'receive',
            'taxes_id': False,
        })
        cls.service_order = cls.env['product.product'].create({
            'name': "Test Service Ordered",
            'standard_price': 40.0,
            'list_price': 90.0,
            'type': 'service',
            'uom_id': uom_hour.id,
            'uom_po_id': uom_hour.id,
            'purchase_method': 'purchase',
            'taxes_id': False,
        })
        cls.product_deliver = cls.env['product.product'].create({
            'name': "Test Product Delivered",
            'standard_price': 55.0,
            'list_price': 70.0,
            'type': 'consu',
            'uom_id': uom_unit.id,
            'uom_po_id': uom_unit.id,
            'purchase_method': 'receive',
            'taxes_id': False,
        })

    def init_purchase(self, confirm=False, products=None):
        po = self.env['purchase.order'].create({
            'partner_id': self.partner_a.id,
            'order_line': [
                (0, 0, {
                    'name': product.name,
                    'product_id': product.id,
                    'product_qty': 1,
                    'product_uom': product.uom_id.id,
                    'price_unit': product.list_price,
                    'taxes_id': False,
                }) for product in products
            ]
        })
        if confirm:
            po.button_confirm()
        return po

    def init_bill(self, products=None, post=False):
        move_form = Form(self.env['account.move'].with_context(default_move_type='in_invoice'))
        move_form.partner_id = self.partner_a
        for product in products:
            with move_form.invoice_line_ids.new() as line_form:
                line_form.product_id = product
                line_form.price_unit = product.list_price
        bill = move_form.save()
        if post:
            bill.action_post()
        return bill

    def test_manual_matching(self):
        po = self.init_purchase(confirm=True, products=[self.product_order])
        bill = self.init_bill(products=[self.product_order])

        match_lines = self.env['purchase.bill.line.match'].search([('partner_id', '=', self.partner_a.id)])
        self.assertEqual(len(match_lines), 2)
        match_lines.action_match_lines()
        self.assertEqual(bill.invoice_line_ids.purchase_line_id, po.order_line)
        self.assertEqual(po.order_line.qty_invoiced, bill.invoice_line_ids.quantity)

    def test_manual_matching_create_bill(self):
        prev_moves_count = self.env['account.move'].search_count([])
        po = self.init_purchase(confirm=True, products=[self.product_order, self.product_order_var_name])

        match_lines = self.env['purchase.bill.line.match'].search([('partner_id', '=', self.partner_a.id)])
        match_lines.action_match_lines()

        new_move_count = self.env['account.move'].search_count([])
        self.assertEqual(new_move_count, prev_moves_count + 1)
        new_move = self.env['account.move'].search([], order='id desc', limit=1)
        self.assertEqual(new_move.partner_id, self.partner_a)
        self.assertEqual(len(new_move.invoice_line_ids), 2)

    def test_add_bill_to_po_downpayment(self):
        po = self.init_purchase(confirm=True, products=[self.product_order])
        bill = self.init_bill(products=[self.service_order], post=True)

        match_lines = self.env['purchase.bill.line.match'].search([('partner_id', '=', self.partner_a.id), ('aml_id', '!=', False)])

        action = match_lines.action_add_to_po()
        wizard = self.env['bill.to.po.wizard'].with_context(action['context']).create({'purchase_order_id': po.id})
        wizard.action_add_downpayment()

        po_dp_section_line = po.order_line.filtered(lambda l: l.display_type == 'line_section' and l.is_downpayment)
        self.assertEqual(len(po_dp_section_line), 1)
        po_dp_line = po.order_line.filtered(lambda l: not l.display_type and l.is_downpayment)
        self.assertTrue(po_dp_line.is_downpayment)
        self.assertEqual(po_dp_line.price_unit, bill.invoice_line_ids.price_unit)

        action_view_bill = po.action_create_invoice()
        generated_bill = self.env['account.move'].browse(action_view_bill['res_id'])
        self.assertEqual(len(generated_bill.invoice_line_ids), 3) # product line, dp section, dp line
        self.assertIn(-po_dp_line.price_unit, generated_bill.invoice_line_ids.mapped('price_unit'))
