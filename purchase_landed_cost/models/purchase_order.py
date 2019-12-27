# Copyright 2013 Joaquín Gutierrez
# Copyright 2014-2016 Pedro M. Baeza <pedro.baeza@tecnativa.com>
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3

from odoo import api, models, fields


class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    is_picking_ok = fields.Boolean(
        compute='_compute_is_picking_ok', default=False)

    cost_distribution_ok = fields.Boolean(
        'Must be linked to Landed Costs', default=False)

    cost_distribution_state = fields.Char(
        compute='_compute_cost_distribution_state', default='', string='Cost Distribution State', store=True)

    @api.multi
    def _compute_is_picking_ok(self):
        for order in self:
            for picking in order.mapped('picking_ids'):
                if picking.state == 'done':
                    order.is_picking_ok = True

    @api.multi
    def action_open_landed_cost(self):
        self.ensure_one()

        line_obj = self.env['purchase.cost.distribution.line']
        lines = line_obj.search([('purchase_id', '=', self.id)])
        action = lines.get_action_purchase_cost_distribution()

        if lines:
            return action
        else:
            distribution = self.env['purchase.cost.distribution'].create({})

            import_picking_wizard = self.with_context(active_id=distribution.id)\
                .env['picking.import.wizard'].create({
                    'supplier': self.partner_id.id,
                    'pickings': [(6, 0, [picking.id for picking in self.mapped('picking_ids') if picking.state == 'done'])],
                })
            import_picking_wizard.action_import_picking()

            lines = line_obj.search([('purchase_id', '=', self.id)])
            action = lines.get_action_purchase_cost_distribution()

        return action

    @api.onchange('partner_id', 'company_id')
    def onchange_partner_id(self):
        res = super(PurchaseOrder, self).onchange_partner_id()
        self.cost_distribution_ok = self.partner_id.commercial_partner_id.cost_distribution_ok
        return res

    @api.multi
    @api.depends('order_line', 'picking_ids.state')
    def _compute_cost_distribution_state(self):
        line_obj = self.env['purchase.cost.distribution.line']
        available_states = ['draft', 'calculated', 'done']

        for order in self:
            lines = line_obj.search([('purchase_id', '=', order.id)])
            if lines:
                distributions_states = [
                    line.distribution.state for line in lines]
                lower_state = ''

                for state in available_states:
                    if state in distributions_states:
                        lower_state = state
                        break
                order.cost_distribution_state = lower_state
            else:
                if order.is_picking_ok:
                    order.cost_distribution_state = 'required'

    @api.multi
    def button_confirm(self):
        """Update 'cost_distribution_state' in both picking and PO when
        confirming order (and creating picking) """
        res = super(PurchaseOrder, self).button_confirm()
        for order in self:
            order._compute_is_picking_ok()
            order._compute_cost_distribution_state()
            for picking in order.mapped('picking_ids'):
                picking._compute_cost_distribution_state()
        return res
