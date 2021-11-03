# Copyright (C) 2021 ForgeFlow S.L.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/lgpl.html)

from odoo import _, api, exceptions, fields, models
from odoo.tools import float_compare


class AccountVoucherWizardPurchase(models.TransientModel):

    _name = "account.voucher.wizard.purchase"
    _description = "Account Voucher Wizard Purchase"

    order_id = fields.Many2one("purchase.order", required=True)
    amount_total = fields.Monetary(related="order_id.amount_total")
    currency_id = fields.Many2one(related="order_id.currency_id")
    left_to_alloc = fields.Monetary(related="order_id.left_to_alloc")

    payment_ref = fields.Char("Ref.")
    journal_id = fields.Many2one(
        "account.journal",
        "Journal",
        required=True,
        domain=[("type", "in", ("bank", "cash"))],
    )
    journal_currency_id = fields.Many2one(
        "res.currency",
        "Journal Currency",
        store=True,
        readonly=False,
        compute="_compute_get_journal_currency",
    )
    compute_advance = fields.Selection(
        string="Compute Advance",
        selection=[
            ("percentage", "Percentage on Order Amount"),
            ("fixed", "Fixed Amount"),
            ("balance", "Balance"),
        ],
        default="percentage",
    )
    percent_advance = fields.Float(
        string="Advance Percentage",
        help="Compute Advance amount based on Order total Amount",
    )
    amount_advance = fields.Monetary(
        "Amount advanced", required=True, currency_field="journal_currency_id"
    )
    date = fields.Date("Date", required=True, default=fields.Date.context_today)
    currency_amount = fields.Monetary(
        "Curr. amount", readonly=True, currency_field="currency_id"
    )

    @api.depends("journal_id")
    def _compute_get_journal_currency(self):
        for wzd in self:
            wzd.journal_currency_id = (
                wzd.journal_id.currency_id.id or self.env.user.company_id.currency_id.id
            )

    @api.constrains("amount_advance")
    def check_amount(self):
        if self.amount_advance <= 0:
            raise exceptions.ValidationError(_("Amount of advance must be positive."))
        if self.order_id:
            self.onchange_date()
            if (
                float_compare(
                    self.currency_amount,
                    self.order_id.left_to_alloc,
                    precision_digits=2,
                )
                > 0
            ):
                raise exceptions.ValidationError(
                    _("Amount of advance is greater than residual amount on purchase")
                )

    @api.model
    def default_get(self, fields_list):
        res = super().default_get(fields_list)
        purchase_ids = self.env.context.get("active_ids", [])
        if not purchase_ids:
            return res
        purchase_id = fields.first(purchase_ids)
        purchase = self.env["purchase.order"].browse(purchase_id)

        # Default journal is the first Bank journal
        journal_id = self.env["account.journal"].search(
            [("type", "=", "bank")], limit=1
        )

        if "left_to_alloc" in fields_list:
            res.update({"order_id": purchase.id, "journal_id": journal_id.id})

        return res

    @api.onchange("journal_id", "date", "amount_advance")
    def onchange_date(self):
        if self.journal_currency_id != self.currency_id:
            amount_advance = self.journal_currency_id._convert(
                self.amount_advance,
                self.currency_id,
                self.order_id.company_id,
                self.date or fields.Date.today(),
            )
        else:
            amount_advance = self.amount_advance
        self.currency_amount = amount_advance

    @api.onchange("compute_advance")
    def _onchange_compute_advance(self):
        if self.compute_advance == "balance":
            # TODO : convert in good currency
            self.amount_advance = self.left_to_alloc
        if self.compute_advance != "percentage":
            self.percent_advance = 0
        if self.compute_advance == "percentage":
            self.journal_currency_id = self.currency_id

    @api.onchange("percent_advance")
    def _onchange_percent_advance(self):
        if self.percent_advance:
            # TODO : convert in good currency
            self.amount_advance = self.amount_total * self.percent_advance / 100

    def _prepare_payment_vals(self, order_id):
        method_id = self.env.ref("account.account_payment_method_manual_out")
        return {
            "date": self.date,
            "amount": self.amount_advance,
            "payment_type": "outbound",
            "partner_type": "supplier",
            "ref": self.payment_ref or order_id.name,
            "journal_id": self.journal_id.id,
            "currency_id": self.journal_currency_id.id,
            "partner_id": order_id.partner_id.id,
            "payment_method_id": method_id.id,
            "purchase_id": order_id.id,
        }

    def make_advance_payment(self):
        self.ensure_one()
        if self.order_id:
            payment_vals = self._prepare_payment_vals(self.order_id)
            self.env["account.payment"].create(payment_vals)

        return {"type": "ir.actions.act_window_close"}
