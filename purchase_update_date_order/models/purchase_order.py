# -*- coding: utf-8 -*-
# Copyright 2018 Akretion (http://www.akretion.com).
# @author Raphaël Reverdy <raphael.reverdy@akretion.com>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from datetime import datetime
from dateutil.relativedelta import relativedelta
from odoo import api, fields, models
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT


class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    date_order = fields.Datetime(
        compute='_compute_date_order',
        store=True)

    @api.depends('order_line.date_planned', 'partner_id')
    def _compute_date_order(self):
        for order in self:
            dates = []
            for line in order.order_line:
                seller_delay = int(
                    line.product_id._select_seller(
                        partner_id=order.partner_id,
                        quantity=line.product_qty,
                        uom_id=line.product_uom
                    ).delay)
                date_planned = datetime.strptime(
                    line.date_planned, DEFAULT_SERVER_DATETIME_FORMAT)
                dates.append(
                    date_planned - relativedelta(days=seller_delay)
                )
            dates.sort()
            min_date = dates and dates[0] or False
            if min_date:
                order.date_order = min_date
            else:
                order.date_order = order.create_date
