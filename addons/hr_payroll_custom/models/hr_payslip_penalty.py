# -*- coding: utf-8 -*-
from odoo import api, fields, models
from odoo.exceptions import UserError


class HrPayslipPenalty(models.Model):
    _name = 'hr.payslip.penalty'
    _description = 'Payslip Penalty'
    _inherit = ['mail.thread']

    employee_id = fields.Many2one('hr.employee', required=True)
    date = fields.Date('Date', required=True, default=fields.Date.today)
    amount = fields.Monetary('Amount', currency_field='currency_id', required=True)
    currency_id = fields.Many2one('res.currency', default=lambda s: s.env.company.currency_id)
    reason = fields.Char('Reason', required=True,
                         help='Ví dụ: lên sai đơn, ship sai...')
    state = fields.Selection([
        ('draft', 'Draft'), ('approved', 'Approved'), ('cancelled', 'Cancelled'),
    ], default='draft', tracking=True)
    payslip_id = fields.Many2one('hr.payslip.custom', 'Applied to Payslip', readonly=True)
    approved_by = fields.Many2one('res.users', readonly=True)

    def action_approve(self):
        self.write({'state': 'approved', 'approved_by': self.env.user.id})

    def action_cancel(self):
        if any(r.payslip_id for r in self):
            raise UserError('Cannot cancel a penalty already applied to a payslip.')
        self.write({'state': 'cancelled'})
