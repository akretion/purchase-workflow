# -*- coding: utf-8 -*-
###############################################################################
#
#   Module for Odoo
#   Copyright (C) 2015 Akretion (http://www.akretion.com).
#   @author Benoît GUILLOT <benoit.guillot@akretion.com>
#
#   This program is free software: you can redistribute it and/or modify
#   it under the terms of the GNU Affero General Public License as
#   published by the Free Software Foundation, either version 3 of the
#   License, or (at your option) any later version.
#
#   This program is distributed in the hope that it will be useful,
#   but WITHOUT ANY WARRANTY; without even the implied warranty of
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#   GNU Affero General Public License for more details.
#
#   You should have received a copy of the GNU Affero General Public License
#   along with this program.  If not, see <http://www.gnu.org/licenses/>.

###############################################################################
from openerp import models, api, _, exceptions


class PurchaseOrder(models.Model):
    _inherit = "purchase.order"

    @api.multi
    def purchase_supplier_confirm(self):
        action_user_id = self.company_id.purchase_action_user_id.id
        if not action_user_id:
            raise exceptions.Warning(
                _('No purchase user is configured on the company '
                  'you should contact the administrador'))
        self.sudo(action_user_id).signal_workflow('purchase_approve')
        return True
