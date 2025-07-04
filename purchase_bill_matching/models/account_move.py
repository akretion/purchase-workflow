import difflib
import logging
import time
from markupsafe import Markup

from odoo import api, fields, models, Command, _
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)

TOLERANCE = 0.02

class AccountMove(models.Model):
    _inherit = 'account.move'

    is_purchase_matched = fields.Boolean(compute='_compute_is_purchase_matched')

    @api.depends('invoice_line_ids.purchase_line_id')
    def _compute_is_purchase_matched(self):
        for move in self:
            if any(il.display_type == 'product' and not bool(il.purchase_line_id) for il in move.invoice_line_ids):
                move.is_purchase_matched = False
                continue
            move.is_purchase_matched = True

    def _add_purchase_order_lines(self, purchase_order_lines):
        """ Creates new invoice lines from purchase order lines """
        self.ensure_one()
        for po_line in purchase_order_lines:
            self.invoice_line_ids += self.env['account.move.line'].new(
                po_line._prepare_account_move_line(self)
            )

    def action_purchase_matching(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _("Purchase Matching"),
            'res_model': 'purchase.bill.line.match',
            'domain': [
                ('partner_id', 'in', (self.partner_id | self.partner_id.commercial_partner_id).ids),
                ('company_id', '=', self.company_id.id),
                ('account_move_id', 'in', [self.id, False]),
            ],
            'views': [(self.env.ref('purchase_bill_matching.purchase_bill_line_match_tree').id, 'list')],
            'context': self.env.context,
        }

    def _find_matching_subset_po_lines(self, po_lines_with_amount, goal_total, timeout):
        """Finds the purchase order lines adding up to the goal amount."""
        def find_matching_subset_po_lines_recursive(lines, goal):
            if time.time() - start_time > timeout:
                raise TimeoutError
            solutions = []
            for i, line in enumerate(lines):
                if line['amount_to_invoice'] < goal - TOLERANCE:
                    sub_solutions = find_matching_subset_po_lines_recursive(lines[i + 1:], goal - line['amount_to_invoice'])
                    solutions.extend((line['line'], *solution) for solution in sub_solutions)
                elif goal - TOLERANCE <= line['amount_to_invoice'] <= goal + TOLERANCE:
                    solutions.append([line['line']])
                if len(solutions) > 1:
                    return []
            return solutions

        start_time = time.time()
        try:
            subsets = find_matching_subset_po_lines_recursive(
                sorted(po_lines_with_amount, key=lambda line: line['amount_to_invoice'], reverse=True),
                goal_total
            )
            return subsets[0] if subsets else []
        except TimeoutError:
            _logger.warning("Timed out during search of a matching subset of purchase order lines")
            return []

    def _find_matching_po_and_inv_lines(self, po_lines, inv_lines, timeout):
        """Finds purchase order lines that match some of the invoice lines."""
        invoice_lines = sorted(inv_lines, key=lambda line: (line.price_unit, line.quantity), reverse=True)
        purchase_lines = sorted(
            po_lines,
            key=lambda line: (line.price_unit, line.product_qty - line.qty_invoiced),
            reverse=True
        )
        matched_po_lines = []
        matched_inv_lines = []
        try:
            start_time = time.time()
            for invoice_line in invoice_lines:
                if not purchase_lines:
                    break
                purchase_line_candidates = {}
                for purchase_line in purchase_lines:
                    if time.time() - start_time > timeout:
                        raise TimeoutError
                    if purchase_line.price_unit < invoice_line.price_unit:
                        break
                    if (invoice_line.price_unit == purchase_line.price_unit
                            and invoice_line.quantity <= purchase_line.product_qty - purchase_line.qty_invoiced):
                        purchase_line_candidates[purchase_line] = difflib.SequenceMatcher(
                            None, invoice_line.name, purchase_line.name).ratio()

                if len(purchase_line_candidates) > 0:
                    purchase_line_match = max(purchase_line_candidates, key=purchase_line_candidates.get)
                    if purchase_line_match:
                        purchase_lines.remove(purchase_line_match)
                        matched_po_lines.append(purchase_line_match)
                        matched_inv_lines.append((purchase_line_match.id, invoice_line))
            return (matched_po_lines, matched_inv_lines)
        except TimeoutError:
            _logger.warning('Timed out during search of matching purchase order lines')
            return ([], [])

    def _match_purchase_orders(self, po_references, partner_id, amount_total, from_ocr, timeout):
        """Tries to match open purchase order lines with this invoice given the information we have."""
        common_domain = [
            ('company_id', '=', self.company_id.id),
            ('state', 'in', ('purchase', 'done')),
            ('invoice_status', 'in', ('to invoice', 'no'))
        ]
        matching_purchase_orders = self.env['purchase.order']
        if po_references and amount_total:
            matching_purchase_orders |= self.env['purchase.order'].search(
                common_domain + [('name', 'in', po_references)])
            if not matching_purchase_orders:
                matching_purchase_orders |= self.env['purchase.order'].search(
                    common_domain + [('partner_ref', 'in', po_references)])

            if matching_purchase_orders:
                po_lines = [line for line in matching_purchase_orders.order_line if line.product_qty]
                po_lines_with_amount = [{
                    'line': line,
                    'amount_to_invoice': (1 - line.qty_invoiced / line.product_qty) * line.price_total,
                } for line in po_lines]

                if (amount_total - TOLERANCE
                        < sum(line['amount_to_invoice'] for line in po_lines_with_amount)
                        < amount_total + TOLERANCE):
                    return 'total_match', matching_purchase_orders.order_line, None
                elif from_ocr:
                    matching_po_lines = self._find_matching_subset_po_lines(
                        po_lines_with_amount, amount_total, timeout)
                    if matching_po_lines:
                        return 'subset_total_match', self.env['purchase.order.line'].union(*matching_po_lines), None
                    else:
                        return 'po_match', matching_purchase_orders.order_line, None
                else:
                    matching_po_lines, matching_inv_lines = self._find_matching_po_and_inv_lines(
                        po_lines, self.invoice_line_ids, timeout)
                    if matching_po_lines:
                        return ('subset_match',
                                self.env['purchase.order.line'].union(*matching_po_lines),
                                matching_inv_lines)

        if partner_id and amount_total:
            purchase_id_domain = common_domain + [
                ('partner_id', 'child_of', [partner_id]),
                ('amount_total', '>=', amount_total - TOLERANCE),
                ('amount_total', '<=', amount_total + TOLERANCE)
            ]
            matching_purchase_orders = self.env['purchase.order'].search(purchase_id_domain)
            if len(matching_purchase_orders) == 1:
                return 'total_match', matching_purchase_orders.order_line, None

        return ('no_match', matching_purchase_orders.order_line, None)

    def _find_and_set_purchase_orders(self, po_references, partner_id, amount_total, from_ocr=False, timeout=10):
        """Finds related purchase orders and links the matching lines on this vendor bill."""
        self.ensure_one()
        method, matched_po_lines, matched_inv_lines = self._match_purchase_orders(
            po_references, partner_id, amount_total, from_ocr, timeout)

        with self._get_edi_creation() as move:
            if method in ('total_match', 'po_match'):
                move._set_purchase_orders(matched_po_lines.order_id, force_write=True)
            elif method == 'subset_total_match':
                move._set_purchase_orders(matched_po_lines.order_id, force_write=False)
                unmatched_lines = move.invoice_line_ids.filtered(
                    lambda l: l.purchase_line_id and l.purchase_line_id not in matched_po_lines)
                move.invoice_line_ids = [Command.update(line.id, {'quantity': 0}) for line in unmatched_lines]
            elif method == 'subset_match':
                move._set_purchase_orders(matched_po_lines.order_id, force_write=False)
                unmatched_lines = move.invoice_line_ids.filtered(
                    lambda l: l.purchase_line_id and l.purchase_line_id not in matched_po_lines)
                move.invoice_line_ids = [Command.delete(line.id) for line in unmatched_lines]

                inv_and_po_lines = list(map(lambda line: (
                        move.invoice_line_ids.filtered(
                            lambda l: l.purchase_line_id and l.purchase_line_id.id == line[0]),
                        move.invoice_line_ids.filtered(
                            lambda l: l in line[1])
                    ),
                    matched_inv_lines
                ))
                move.invoice_line_ids = [
                    Command.update(po_line.id, {'quantity': inv_line.quantity, 'tax_ids': inv_line.tax_ids})
                    for po_line, inv_line in inv_and_po_lines
                ]
                move.invoice_line_ids = [Command.delete(inv_line.id) for dummy, inv_line in inv_and_po_lines]
                unmatched_lines = move.invoice_line_ids.filtered(lambda l: not l.purchase_line_id)
                if len(unmatched_lines) > 0:
                    move.invoice_line_ids = [Command.create({
                        'display_type': 'line_section',
                        'name': _('From Electronic Document'),
                        'sequence': -1,
                    })]

class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'

    is_downpayment = fields.Boolean()

    def _copy_data_extend_business_fields(self, values):
        super(AccountMoveLine, self)._copy_data_extend_business_fields(values)
        values['purchase_line_id'] = self.purchase_line_id.id

    def _prepare_line_values_for_purchase(self):
        return [
            {
                'product_id': line.product_id.id,
                'product_qty': line.quantity,
                'product_uom': line.product_uom_id.id,
                'price_unit': line.price_unit,
                'taxes_id': [(6, 0, line.tax_ids.ids)],
            }
            for line in self
        ]
