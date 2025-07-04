from odoo import api, fields, models, _
from odoo.exceptions import UserError


class BillToPoWizard(models.TransientModel):
    _name = 'bill.to.po.wizard'
    _description = "Wizard to add bill lines to PO"

    purchase_order_id = fields.Many2one('purchase.order', string="Purchase Order")
    partner_id = fields.Many2one('res.partner', string="Vendor", required=True)

    def _get_active_lines(self):
        active_ids = self.env.context.get('active_ids', [])
        return self.env['purchase.bill.line.match'].browse(active_ids)

    def action_add_to_po(self):
        self.ensure_one()
        lines = self._get_active_lines()
        aml_ids = lines.aml_id

        if not self.purchase_order_id:
            raise UserError(_("You must select a Purchase Order."))

        po_lines_vals = aml_ids._prepare_line_values_for_purchase()
        self.purchase_order_id.order_line = [(0, 0, vals) for vals in po_lines_vals]
        aml_ids.unlink()

        return self.purchase_order_id.action_view_purchase_order()

    def action_add_downpayment(self):
        self.ensure_one()
        lines = self._get_active_lines()
        aml_ids = lines.aml_id

        if not self.purchase_order_id:
            # Create a new PO if none is selected
            self.purchase_order_id = self.env['purchase.order'].create({'partner_id': self.partner_id.id})

        po_lines_vals = [
            {
                'name': _("Down Payment (ref: %s)", line.name),
                'product_qty': -1,
                'price_unit': line.price_unit,
                'is_downpayment': True,
                'order_id': self.purchase_order_id.id,
            }
            for line in aml_ids
        ]

        dp_lines = self.purchase_order_id._create_downpayments(po_lines_vals)
        for i, line in enumerate(aml_ids):
            line.purchase_line_id = dp_lines[i]

        return self.purchase_order_id.action_view_purchase_order()
