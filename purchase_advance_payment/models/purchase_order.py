# Copyright (C) 2021 ForgeFlow S.L.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/lgpl.html)

from odoo import api, fields, models
from odoo.tools import float_compare


class PurchaseOrder(models.Model):

    _inherit = "purchase.order"

    account_payment_ids = fields.One2many(
        "account.payment",
        "purchase_id",
        string="Pay purchase advanced",
    )
    residual_draft = fields.Monetary(
        "Residual (draft)",
        readonly=True,
        compute="_compute_purchase_advance_payment",
        store=True,
        currency_field="currency_id",
    )
    residual_posted = fields.Monetary(
        "Residual (posted)",
        readonly=True,
        compute="_compute_purchase_advance_payment",
        store=True,
        currency_field="currency_id",
    )
    payment_line_ids = fields.Many2many(
        "account.move.line",
        string="Payment move lines",
        compute="_compute_purchase_advance_payment",
        store=True,
    )
    advance_payment_status = fields.Selection(
        selection=[
            ("not_paid", "Not Paid"),
            ("paid", "Paid"),
            ("partial", "Partially Paid"),
        ],
        string="Advance Payment Status",
        store=True,
        readonly=True,
        copy=False,
        tracking=True,
        compute="_compute_purchase_advance_payment",
    )

    @api.depends(
        "currency_id",
        "company_id",
        "amount_total",
        "account_payment_ids",
        "account_payment_ids.state",
        "account_payment_ids.move_id",
        "account_payment_ids.move_id.line_ids",
        "account_payment_ids.move_id.line_ids.date",
        "account_payment_ids.move_id.line_ids.debit",
        "account_payment_ids.move_id.line_ids.credit",
        "account_payment_ids.move_id.line_ids.currency_id",
        "account_payment_ids.move_id.line_ids.amount_currency",
    )
    def _compute_purchase_advance_payment(self):
        for order in self:
            mls = order.account_payment_ids.mapped("move_id.line_ids").filtered(
                lambda x: x.account_id.internal_type == "payable"
            )
            advance_draft = 0.0
            advance_posted = 0.0
            for line in mls:
                line_currency = line.currency_id or line.company_id.currency_id
                line_amount = line.amount_currency if line.currency_id else line.balance
                if line_currency != order.currency_id:
                    line_amount = line.currency_id._convert(
                        line_amount,
                        order.currency_id,
                        order.company_id,
                        line.date or fields.Date.today(),
                    )
                if line.parent_state == "posted":
                    advance_posted += line_amount
                    advance_draft += line_amount
                elif line.parent_state == "draft":
                    advance_draft += line_amount

            residual_draft = order.amount_total - advance_draft
            residual_posted = order.amount_total - advance_posted

            payment_state = "not_paid"
            if mls:
                has_due_amount = float_compare(
                    residual_posted, 0.0, precision_rounding=order.currency_id.rounding
                )
                if has_due_amount <= 0:
                    payment_state = "paid"
                elif has_due_amount > 0:
                    payment_state = "partial"

            order.payment_line_ids = mls
            order.residual_draft = residual_draft
            order.residual_posted = residual_posted
            order.advance_payment_status = payment_state

            # TODO : distinguish Residual draft from Residual posted
            # and add related invoices matched payments to "Residual posted" with :
            # order.line_ids.matched_debit_ids.debit_move_id.move_id.payment_id
