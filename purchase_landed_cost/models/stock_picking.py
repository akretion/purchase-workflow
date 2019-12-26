# Copyright 2013 Joaquín Gutierrez
# Copyright 2014-2016 Tecnativa - Pedro M. Baeza
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3
from odoo import api, models, fields


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    cost_distribution_ok = fields.Boolean(
        related='purchase_id.cost_distribution_ok', readonly='False')

    @api.multi
    def action_open_landed_cost(self):
        self.ensure_one()

        line_obj = self.env['purchase.cost.distribution.line']
        lines = line_obj.search([('picking_id', '=', self.id)])
        action = lines.get_action_purchase_cost_distribution()

        if lines:
            return action
        else:
            distribution = self.env['purchase.cost.distribution'].create({})
            import_picking_wizard = self.with_context(active_id=distribution.id).env['picking.import.wizard'].create({
                'supplier': self.partner_id.id,
                'pickings': [(6, 0, [self.id])],
            })

            import_picking_wizard.action_import_picking()

            lines = line_obj.search([('picking_id', '=', self.id)])
            action = lines.get_action_purchase_cost_distribution()

        return action
