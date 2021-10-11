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
        compute="_compute_account_payment_ids",
        inverse="_inverse_account_payment_ids",
        store=True,
    )
    left_to_alloc = fields.Monetary(
        "Leftover to allocate",
        readonly=True,
        compute="_compute_purchase_advance_payment",
        store=True,
        currency_field="currency_id",
    )
    left_to_pay = fields.Monetary(
        "Leftover to pay",
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
    is_allocated = fields.Boolean(
        string="Is allocated",
        help="True if the Order's payments (draft or posted) equals the Order's "
        "total amount",
        store=True,
        copy=False,
        tracking=True,
        default=False,
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

            left_to_alloc = order.amount_total - advance_draft
            left_to_pay = order.amount_total - advance_posted

            payment_state = "not_paid"
            is_allocated = False
            if mls:
                has_amount_to_pay = float_compare(
                    left_to_pay, 0.0, precision_rounding=order.currency_id.rounding
                )
                has_amount_to_allocate = float_compare(
                    left_to_alloc, 0.0, precision_rounding=order.currency_id.rounding
                )
                if has_amount_to_allocate <= 0:
                    is_allocated = True
                if has_amount_to_pay <= 0:
                    payment_state = "paid"
                elif has_amount_to_pay > 0:
                    payment_state = "partial"

            order.payment_line_ids = mls
            order.left_to_alloc = left_to_alloc
            order.left_to_pay = left_to_pay
            order.advance_payment_status = payment_state
            order.is_allocated = is_allocated

    @api.depends("invoice_ids.line_ids.matched_debit_ids")
    def _compute_account_payment_ids(self):
        """Add payments 'matched with the order's invoices' to the order's payments"""
        for order in self:
            matched_ids = order.invoice_ids.line_ids.matched_debit_ids
            order.account_payment_ids |= matched_ids.debit_move_id.move_id.payment_id

    def _inverse_account_payment_ids(self):
        for order in self:
            order.account_payment_ids.write({"purchase_id": order.id})

    def _cancel_unlink_unposted_payments(self):
        """Cancel draft payments and delete them"""
        for order in self:
            pay_ids = order.account_payment_ids.filtered(
                lambda p: p.state in ["draft", "cancel"]
            )
            pay_ids.action_cancel()
            pay_ids.unlink()

    def action_create_invoice(self):
        self._cancel_unlink_unposted_payments()
        return super().action_create_invoice()

    def write(self, vals):
        if vals.get("state") == "cancel":
            self._cancel_unlink_unposted_payments()
        return super().write(vals)
