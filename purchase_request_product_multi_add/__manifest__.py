# Copyright 2021 Akretion - Florian Mounier
{
    "name": "Purchase Request Product Multi Add",
    "summary": "This module adds a new wizard to add multiple products at the same time on a purchase request",
    "website": "https://github.com/OCA/purchase-workflow",
    "author": "Akretion, Odoo Community Association (OCA)",
    "category": "Usability",
    "version": "14.0.1.0.0",
    "license": "LGPL-3",
    "depends": ["purchase_request"],
    "data": [
        "security/ir.model.access.csv",
        "wizards/purchase_request_import_products_view.xml",
        "views/purchase_request_view.xml",
    ],
}
