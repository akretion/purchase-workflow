# Copyright 2013 Joaquín Gutierrez
# Copyright 2014-2016 Pedro M. Baeza <pedro.baeza@tecnativa.com>
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3

from odoo import api, models, fields


class Partner(models.Model):
    _inherit = 'res.partner'

    cost_distribution_ok = fields.Boolean('Products linked to Landed Costs', default='True',
                                          help='By default, storable products from this vendor will need to be linked to Landed Costs')
