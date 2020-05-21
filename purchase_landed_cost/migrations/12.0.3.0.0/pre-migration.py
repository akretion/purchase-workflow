# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from openupgradelib import openupgrade


@openupgrade.migrate()
def migrate(env, version):

    openupgrade.rename_fields(
        env,
        [
            (
                "account.invoice",
                "account_invoice",
                "expense_line_ids",
                "expense_ids",
            ),
            (
                "account.invoice.line",
                "account_invoice_line",
                "expense_line_ids",
                "expense_ids",
            ),
            (
                "purchase.cost.distribution",
                "purchase_cost_distribution",
                "expense_lines",
                "expense_ids",
            ),
            (
                "purchase.cost.distribution.line",
                "purchase_cost_distribution_line",
                "expense_lines",
                "line_expense_ids",
            ),
        ],
    )
