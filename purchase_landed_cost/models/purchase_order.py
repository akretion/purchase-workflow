# Copyright 2013 Joaquín Gutierrez
# Copyright 2014-2016 Pedro M. Baeza <pedro.baeza@tecnativa.com>
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3

from odoo import api, models, fields


class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    is_picking_done = fields.Boolean(
        compute='_compute_is_picking_done', default='False')

    cost_distribution_ok = fields.Boolean(
        'Linked to Landed Costs', default='False')

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
        action = lines.get_action_purchase_cost_distribution()

        if lines:
            return action
        else:
            distribution = self.env['purchase.cost.distribution'].create({})

            import_picking_wizard = self.with_context(active_id=distribution.id).env['picking.import.wizard'].create({
                'supplier': self.partner_id.id,
                'pickings': [(6, 0, [picking.id for picking in self.mapped('picking_ids')])],
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


#TODO ajouter un filtrage pour avoir la liste des purchase orders qui n'ont pas encore de landed_cost enregistrés
