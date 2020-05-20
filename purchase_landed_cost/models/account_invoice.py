# Copyright 2014-2015 Pedro M. Baeza <pedro.baeza@tecnativa.com>
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3

from odoo import api, fields, models


class AccountInvoice(models.Model):
    _inherit = "account.invoice"

    expense_ids = fields.One2many(
        comodel_name="purchase.cost.distribution.expense",
        inverse_name="invoice_id",
        string="Cost Distribution Expenses",
        compute="_compute_expense_ids",
        readonly=False,
    )

    @api.multi
    @api.depends("invoice_line_ids")
    def _compute_expense_ids(self):
        for invoice in self:
            expense_ids = []
            for line in invoice.invoice_line_ids:
                if line.expense_ids:
                    expense_ids += line.expense_ids.ids
            invoice.expense_ids = [(6, 0, set(expense_ids))]

    @api.multi
    def write(self, vals):
        """Update expenses in Invoice lines when changing expense_ids in the Invoice"""
        res = super().write(vals)
        if vals.get("expense_ids"):
            for invoice in self:
                for line in invoice.invoice_line_ids:
                    line.expense_ids = vals.get("expense_ids")
        return res


class AccountInvoiceLine(models.Model):
    _inherit = "account.invoice.line"

    expense_ids = fields.One2many(
        comodel_name="purchase.cost.distribution.expense",
        inverse_name="invoice_line",
        string="Cost Distribution Expenses",
    )
