# -*- coding: utf-8 -*-
import base64
import io
import csv
import logging
from odoo import api, fields, models, _
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class CodReconcileWizard(models.TransientModel):
    """
    Import a COD payment settlement file from GHN or GHTK (CSV/Excel).
    Expected columns: tracking_number, cod_amount, status (delivered/returned)
    Matches each row to a stock.picking by tracking_number, then to the
    related sale.order invoice and registers a payment automatically.
    """
    _name = 'cod.reconcile.wizard'
    _description = 'COD Reconciliation Wizard'

    carrier = fields.Selection([
        ('ghn', 'GHN'),
        ('ghtk', 'GHTK'),
    ], required=True, default='ghn')
    payment_date = fields.Date('Bank Receipt Date', required=True, default=fields.Date.today)
    journal_id = fields.Many2one('account.journal', 'Bank Journal', required=True,
                                 domain=[('type', 'in', ('bank', 'cash'))])
    file_data = fields.Binary('Settlement File (CSV)', required=True)
    filename = fields.Char()

    # Result lines (auto-populated after parse)
    line_ids = fields.One2many('cod.reconcile.line', 'wizard_id', 'Parsed Lines')
    total_matched = fields.Integer(compute='_compute_totals')
    total_amount = fields.Monetary(compute='_compute_totals', currency_field='currency_id')
    currency_id = fields.Many2one('res.currency', default=lambda s: s.env.company.currency_id)

    @api.depends('line_ids')
    def _compute_totals(self):
        for w in self:
            matched = w.line_ids.filtered(lambda l: l.picking_id)
            w.total_matched = len(matched)
            w.total_amount = sum(matched.mapped('cod_amount'))

    def action_parse_file(self):
        """Parse uploaded CSV and populate line_ids."""
        self.ensure_one()
        if not self.file_data:
            raise UserError('Please upload a settlement file.')

        raw = base64.b64decode(self.file_data).decode('utf-8-sig', errors='replace')
        reader = csv.DictReader(io.StringIO(raw))

        # Delete old lines
        self.line_ids.unlink()

        lines = []
        Picking = self.env['stock.picking']
        for row in reader:
            tracking = (row.get('tracking_number') or row.get('order_code') or
                        row.get('label') or '').strip()
            if not tracking:
                continue
            try:
                amount = float((row.get('cod_amount') or row.get('cod') or '0')
                               .replace(',', '').replace('đ', '').strip())
            except ValueError:
                amount = 0.0
            status_raw = (row.get('status') or row.get('trang_thai') or '').lower()
            delivered = any(k in status_raw for k in ('delivered', 'thành công', 'thanh cong', 'success'))

            picking = Picking.search([('tracking_number', '=', tracking)], limit=1)
            lines.append({
                'wizard_id': self.id,
                'tracking_number': tracking,
                'cod_amount': amount,
                'carrier_status': status_raw[:100],
                'is_delivered': delivered,
                'picking_id': picking.id if picking else False,
                'invoice_id': picking.sale_id.invoice_ids[:1].id if picking and picking.sale_id else False,
            })

        self.env['cod.reconcile.line'].create(lines)
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'cod.reconcile.wizard',
            'res_id': self.id,
            'view_mode': 'form',
            'target': 'new',
        }

    def action_reconcile(self):
        """Register payments for all matched delivered invoices."""
        self.ensure_one()
        reconciled = 0
        errors = []

        for line in self.line_ids.filtered(lambda l: l.is_delivered and l.invoice_id and l.cod_amount > 0):
            invoice = line.invoice_id
            if invoice.payment_state in ('paid', 'in_payment'):
                continue
            try:
                payment = self.env['account.payment'].create({
                    'payment_type': 'inbound',
                    'partner_type': 'customer',
                    'partner_id': invoice.partner_id.id,
                    'amount': line.cod_amount,
                    'date': self.payment_date,
                    'journal_id': self.journal_id.id,
                    'ref': f'COD – {line.tracking_number}',
                    'currency_id': self.currency_id.id,
                })
                payment.action_post()
                # Reconcile payment with invoice
                (invoice.line_ids + payment.move_id.line_ids).filtered(
                    lambda l: l.account_id == invoice.line_ids.filtered(
                        lambda ll: ll.account_id.account_type == 'asset_receivable'
                    )[:1].account_id
                ).reconcile()
                # Update picking shipping status
                line.picking_id.shipping_status = 'delivered'
                reconciled += 1
            except Exception as e:
                errors.append(f'{line.tracking_number}: {e}')
                _logger.error('COD reconcile error for %s: %s', line.tracking_number, e)

        msg = f'✅ {reconciled} invoice(s) reconciled.'
        if errors:
            msg += '\n⚠️ Errors:\n' + '\n'.join(errors)

        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'message': msg,
                'type': 'success' if not errors else 'warning',
                'sticky': True,
            }
        }


class CodReconcileLine(models.TransientModel):
    _name = 'cod.reconcile.line'
    _description = 'COD Reconciliation Line'

    wizard_id = fields.Many2one('cod.reconcile.wizard', ondelete='cascade')
    tracking_number = fields.Char('Tracking #', readonly=True)
    carrier_status = fields.Char('Carrier Status', readonly=True)
    is_delivered = fields.Boolean('Delivered?', readonly=True)
    cod_amount = fields.Monetary('COD Amount', currency_field='currency_id')
    currency_id = fields.Many2one(related='wizard_id.currency_id')
    picking_id = fields.Many2one('stock.picking', 'Matched Delivery', readonly=True)
    invoice_id = fields.Many2one('account.move', 'Invoice', readonly=True)
    reconcile = fields.Boolean('Include in Reconciliation', default=True)
