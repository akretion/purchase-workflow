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
{"name": "Purchase supplier validation",
 "version": "1.0",
 "summary": "Allow external supplier to validate his purchase orders.",
 "author": "Akretion",
 "license": "AGPL-3",
 "category": "Purchase Management",
 "complexity": "normal",
 "images": [],
 "depends": ["purchase_double_validation",
             ],
 "demo": [],
 "data": ["security/supplier_security.xml",
          "security/ir.model.access.csv",
          "purchase_view.xml",
          "company_view.xml",
          ],
 "auto_install": False,
 "test": [],
 "installable": True,
 "certificate": "",
 }
