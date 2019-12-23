# Copyright 2013 Joaquín Gutierrez
# Copyright 2014-2016 Pedro M. Baeza <pedro.baeza@tecnativa.com>
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3

from odoo import api, models, fields


class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    is_picking_done = fields.Boolean(
        compute='_compute_is_picking_done', default='False')

    cost_distribution_ok = fields.Boolean('Linked to Landed Costs', default='False')

    @api.multi
    def _compute_is_picking_done(self):
        for order in self:
            for picking in order.mapped('picking_ids'):
                if picking.state == 'done':
                    order.is_picking_done = True
                else:
                    order.is_picking_done = False

    @api.multi
    def action_open_landed_cost(self):
        self.ensure_one()
        line_obj = self.env['purchase.cost.distribution.line']
        lines = line_obj.search([('purchase_id', '=', self.id)])
        if lines:
            return lines.get_action_purchase_cost_distribution()

    @api.onchange('partner_id', 'company_id')
    def onchange_partner_id(self):
        res = super(Partner, self).onchange_partner_id()
        self.cost_distribution_ok = self.commercial_partner_id.cost_distribution_ok
        return res
