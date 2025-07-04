# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models
from odoo.tools.sql import SQL


class PurchaseBillUnion(models.Model):
    """
    This model is a transient model that allows to display purchase orders and
    vendor bills in the same list, to be used in the auto-complete field of
    the vendor bill.
    """
    _name = 'purchase.bill.union'
    _description = 'Purchase Bill Union'
    _auto = False

    name = fields.Char(string='Reference')
    partner_id = fields.Many2one('res.partner', string='Vendor')
    amount = fields.Monetary(string='Total', currency_field='currency_id')
    date = fields.Date(string='Date')
    currency_id = fields.Many2one('res.currency', string='Currency')
    company_id = fields.Many2one('res.company', string='Company')
    vendor_bill_id = fields.Many2one('account.move', string='Vendor Bill')
    purchase_order_id = fields.Many2one('purchase.order', string='Purchase Order')
    reference = fields.Char(string='Vendor Reference')

    @property
    def _table_query(self):
        return SQL('{po} UNION {bill}').format(
            po=self._po_query,
            bill=self._bill_query
        )

    @property
    def _po_query(self):
        return SQL("""
            SELECT
                po.id,
                po.name,
                po.partner_id,
                po.partner_ref as reference,
                po.amount_total as amount,
                po.date_order as date,
                po.currency_id,
                po.company_id,
                NULL as vendor_bill_id,
                po.id as purchase_order_id
            FROM purchase_order po
            WHERE po.state in ('purchase', 'done')
        """)

    @property
    def _bill_query(self):
        return SQL("""
            SELECT
                -am.id as id,
                am.name,
                am.partner_id,
                am.ref as reference,
                am.amount_total as amount,
                am.invoice_date as date,
                am.currency_id,
                am.company_id,
                am.id as vendor_bill_id,
                NULL as purchase_order_id
            FROM account_move am
            WHERE am.move_type = 'in_invoice'
        """)
