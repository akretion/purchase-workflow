# -*- coding: utf-8 -*-
# Copyright 2018 Akretion (http://www.akretion.com).
# @author Raphaël Reverdy <raphael.reverdy@akretion.com>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from dateutil.relativedelta import relativedelta
from odoo import fields, models, api


class PurchaseRequestLine(models.Model):
    _inherit = 'purchase.request.line'

    least_date_order = fields.Datetime(
        compute='_compute_least_date_order',
        store=True)

    @api.depends('purchase_lines.date_order')
    def _compute_least_date_order(self):
        """Calc when to order with current RFQs."""
        for request_line in self:
            dates = []
            if not request_line.purchase_lines:
                dates.append(self._calc_default_date_required())
            for line in request_line.purchase_lines:
                dates.append(line.date_order)
            dates.sort()
            min_date = dates and dates[0] or False
            request_line.least_date_order = min_date

    def _calc_default_date_required(self):
        """Calc when to order with default vendor."""
        self.ensure_one()
        line = self
        seller_delay = int(
            line.product_id._select_seller(
                # partner_id=order.partner_id,
                quantity=line.product_qty,
                # uom_id=line.product_uom
            ).delay)
        date_planned = fields.Datetime.from_string(line.date_required)
        return date_planned - relativedelta(days=seller_delay)
