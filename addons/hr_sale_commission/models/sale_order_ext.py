# -*- coding: utf-8 -*-
from odoo import models, fields


class SaleOrderCommission(models.Model):
    """Add commission fields to sale.order."""
    _inherit = 'sale.order'

    x_commission_counted = fields.Boolean(string='Commission Counted', default=False, copy=False)
    x_commission_line_id = fields.Many2one('hr.commission.line', string='Commission Line', 
                                           copy=False, readonly=True)
    x_commission_record_id = fields.Many2one('hr.commission.record', string='Commission Record',
                                             related='x_commission_line_id.commission_record_id',
                                             store=True, readonly=True)

    def _is_eligible_for_commission(self):
        """Eligible if confirmed + has salesperson + not yet counted."""
        self.ensure_one()
        return self.state == 'sale' and not self.x_commission_counted and self.user_id

    def _has_completed_delivery(self):
        """True if any delivery is done."""
        self.ensure_one()
        return bool(self.env['stock.picking'].search([
            ('sale_id', '=', self.id),
            ('state', '=', 'done'),
        ], limit=1))

    def _get_commission_employee(self):
        """Find employee for this order's salesperson."""
        self.ensure_one()
        if not self.user_id:
            return False
        return self.env['hr.employee'].search([('user_id', '=', self.user_id.id)], limit=1) or False

    def _mark_commission_counted(self, commission_line):
        """Flag order as commission-counted."""
        self.ensure_one()
        if commission_line:
            self.write({
                'x_commission_counted': True,
                'x_commission_line_id': commission_line.id,
            })
