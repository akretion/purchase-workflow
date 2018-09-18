# -*- coding: utf-8 -*-
# Copyright 2018 Akretion (http://www.akretion.com).
# @author Raphaël Reverdy <raphael.reverdy@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

{
    "name": 'Purchase Request RFQ date order',
    "summary": 'Display date order on purchase request lines',
    "version": "10.0.1.0.0",
    "category": "Purchase",
    "website": "https://odoo-community.org/",
    "author": "Akretion,Odoo Community Association (OCA)",
    "license": "AGPL-3",
    "application": False,
    "installable": True,
    "depends": [
        "purchase_update_date_order",
        "purchase_request_to_rfq",
    ],
    "data": [
        "views/purchase_request_line.xml",
    ],
}
