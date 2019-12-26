# Copyright 2013 Joaquín Gutierrez
# Copyright 2014-2016 Pedro M. Baeza <pedro.baeza@tecnativa.com>
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3

from odoo import api, models, fields


class Partner(models.Model):
    _inherit = 'res.partner'

    cost_distribution_ok = fields.Boolean('Linked to Landed Costs', default='True')
