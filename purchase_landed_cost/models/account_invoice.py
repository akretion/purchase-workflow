# Copyright 2014-2015 Pedro M. Baeza <pedro.baeza@tecnativa.com>
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3

from odoo import fields, models, api


class AccountInvoice(models.Model):
    _inherit = 'account.invoice'

    expense_line_ids = fields.One2many(
        comodel_name="purchase.cost.distribution.expense",
        inverse_name="invoice_id", string="Landed costs")


class AccountInvoiceLine(models.Model):
    _inherit = 'account.invoice.line'

    expense_line_ids = fields.One2many(
        comodel_name="purchase.cost.distribution.expense",
        inverse_name="invoice_line", string="Landed costs")

    @api.multi
    def name_get(self):
        """Overwrite native name_get to be more explicit and allow to choose
        the right Invoice Line from a Cost Distribution Expense"""
        if self.env.context.get('show_invoice_number'):
            res = []
            for invoice_line in self:
                name = "%s - %s" % (invoice_line.invoice_id.number, invoice_line.name)
                res.append((invoice_line.id, name))
            return res
        return super(AccountInvoiceLine, self).name_get()
