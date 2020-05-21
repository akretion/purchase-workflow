# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from openupgradelib import openupgrade

field_renames = [
    (
        "purchase.cost.distribution",
        "purchase_cost_distribution",
        "cost_lines",
        "distrib_line_ids",
    ),
    (
        "purchase.cost.distribution.line",
        "purchase_cost_distribution_line",
        "distribution",
        "distrib_id",
    ),
    (
        "purchase.cost.distribution.line.expense",
        "purchase_cost_distribution_line_expense",
        "distribution_line",
        "distrib_line_id",
    ),
    (
        "purchase.cost.distribution.expense",
        "purchase_cost_distribution_expense",
        "imported_lines",
        "distrib_line_ids",
    ),
    (
        "purchase.cost.distribution.expense",
        "purchase_cost_distribution_expense",
        "affected_lines",
        "affected_line_ids",
    ),
    (
        "purchase.cost.distribution.expense",
        "purchase_cost_distribution_expense",
        "distribution",
        "distrib_id",
    ),
]


@openupgrade.migrate()
def migrate(env, version):
    cr = env.cr
    openupgrade.rename_fields(env, field_renames)
