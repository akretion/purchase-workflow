# -*- coding: utf-8 -*-
from odoo import fields
from odoo.tests import common, tagged
from odoo.exceptions import UserError

@tagged('post_install', '-at_install')
class TestBillMatching(common.TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env = cls.env(context=dict(cls.env.context, tracking_disable=True))
        cls.partner_a = cls.env['res.partner'].create({'name': 'Test Vendor Partner'})
        uom_unit = cls.env.ref('uom.product_uom_unit')

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
                    'date_planned': fields.Datetime.now(),
                }) for product in products or []
            ]
        })
        if confirm:
            po.button_confirm()
        return po

    def init_bill(self, products=None, post=False):
        bill_vals = {
            'partner_id': self.partner_a.id,
            'move_type': 'in_invoice',
            'invoice_date': fields.Date.today(),
            'invoice_line_ids': [
                (0, 0, {
                    'product_id': product.id,
                    'price_unit': product.list_price,
                    'quantity': 1,
                }) for product in products or []
            ]
        }
        bill = self.env['account.move'].create(bill_vals)
        if post:
            bill.action_post()
        return bill

    def test_manual_matching(self):
        po = self.init_purchase(confirm=True, products=[self.product_order])
        bill = self.init_bill(products=[self.product_order])
        self.env.flush_all()

        match_lines = self.env['purchase.bill.line.match'].search([('partner_id', '=', self.partner_a.id)])
        self.assertEqual(len(match_lines), 2)
        match_lines.action_match_lines()
        self.assertEqual(bill.invoice_line_ids.purchase_line_id, po.order_line)
        self.assertEqual(po.order_line.qty_invoiced, bill.invoice_line_ids.quantity)

    def test_manual_matching_create_bill(self):
        self.init_purchase(confirm=True, products=[self.product_order, self.product_order_var_name])
        self.env.flush_all()

        match_lines = self.env['purchase.bill.line.match'].search([('partner_id', '=', self.partner_a.id), ('aml_id', '=', False)])
        self.assertEqual(len(match_lines), 2, "Should find the two PO lines ready to be billed.")

    def test_add_bill_to_po_downpayment(self):
        po = self.init_purchase(confirm=True, products=[self.product_order])

        dp_bill_vals = {
            'partner_id': self.partner_a.id,
            'move_type': 'in_invoice',
            'invoice_date': fields.Date.today(),
            'invoice_line_ids': [(0, 0, {'name': 'Down payment', 'quantity': 1, 'price_unit': 69.00})]
        }
        dp_bill = self.env['account.move'].create(dp_bill_vals)
        dp_bill.action_post()
        self.env.flush_all()

        match_lines = self.env['purchase.bill.line.match'].search([('aml_id', '=', dp_bill.invoice_line_ids.id)])
        action = match_lines.action_add_to_po()
        context = dict(action['context'], active_ids=match_lines.ids)

        wizard = self.env['bill.to.po.wizard'].with_context(context).create({'purchase_order_id': po.id})
        wizard.action_add_downpayment()

        po_dp_section_line = po.order_line.filtered(lambda l: l.display_type == 'line_section' and l.is_downpayment)
        self.assertEqual(len(po_dp_section_line), 1, "A down payment section should be created.")
        po_dp_line = po.order_line.filtered(lambda l: not l.display_type and l.is_downpayment)
        self.assertTrue(po_dp_line.is_downpayment)
        self.assertEqual(po_dp_line.price_unit, -69.00) # Asserting the correct negative value
        self.assertEqual(po_dp_line.product_qty, 1) # Quantity should be positive

        po.order_line.filtered(lambda l: not l.is_downpayment)[0].qty_received = 1
        action_view_bill = po.action_create_invoice()
        generated_bill = self.env['account.move'].browse(action_view_bill['res_id'])

        self.assertEqual(len(generated_bill.invoice_line_ids), 2) # Product line and down payment line
        self.assertIn(-69.00, generated_bill.invoice_line_ids.mapped('price_unit'))
        self.assertAlmostEqual(generated_bill.amount_total, self.product_order.list_price - 69.00)
