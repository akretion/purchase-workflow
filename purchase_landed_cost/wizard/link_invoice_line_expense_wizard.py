# Copyright 2016 Pedro M. Baeza <pedro.baeza@tecnativa.com>
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3

from odoo import api, fields, models


class LinkInvoiceLineExpenseWizard(models.TransientModel):
    _name = "link.invoice.line.expense.wizard"
    _description = "Link an Invoice line with Cost Distribution Expenses"

    invoice_line_id = fields.Many2one(
        comodel_name="account.invoice.line", string="Invoice Line", required="True",
    )

    cost_distribution_id = fields.Many2one(
        comodel_name="purchase.cost.distribution",
        string="Cost Distribution",
        required="True",
    )

    expense_ids = fields.Many2many(
        comodel_name="purchase.cost.distribution.expense",
        relation="rel_link_wizard_cost_distrib_expense",
        column1="cost_distrib_expense_id",
        column2="link_wizard_id",
        string="Expenses",
    )

    @api.multi
    def button_import(self):
        self.ensure_one()
        invoice_id = self.env.context["active_id"]
        expenses = self.env["purchase.cost.distribution.expense"].browse(
            self.expense_ids.ids
        )
        for expense in expenses:
            expense.write(
                {"invoice_id": invoice_id, "invoice_line": self.invoice_line_id.id}
            )
