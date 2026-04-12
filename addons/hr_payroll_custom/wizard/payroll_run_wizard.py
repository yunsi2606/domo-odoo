# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from datetime import date


class PayrollRunWizard(models.TransientModel):
    _name = 'hr.payroll.run.wizard'
    _description = 'Generate Payslips for Period'

    date_from = fields.Date('From', required=True,
                            default=lambda s: date.today().replace(day=1))
    date_to = fields.Date('To', required=True, default=fields.Date.today)
    department_id = fields.Many2one('hr.department', 'Department (optional)')
    employee_ids = fields.Many2many('hr.employee', string='Employees (blank = all)')
    result_msg = fields.Text('Result', readonly=True)

    def action_run(self):
        domain = [('state', 'in', ('open',))]
        if self.department_id:
            domain.append(('employee_id.department_id', '=', self.department_id.id))
        if self.employee_ids:
            domain.append(('employee_id', 'in', self.employee_ids.ids))

        contracts = self.env['hr.contract'].search(domain)
        Payslip = self.env['hr.payslip.custom']
        created = 0
        for contract in contracts:
            # Avoid duplicates
            existing = Payslip.search([
                ('employee_id', '=', contract.employee_id.id),
                ('date_from', '=', self.date_from),
                ('date_to', '=', self.date_to),
                ('state', '!=', 'cancelled'),
            ], limit=1)
            if existing:
                continue
            slip = Payslip.create({
                'employee_id': contract.employee_id.id,
                'contract_id': contract.id,
                'date_from': self.date_from,
                'date_to': self.date_to,
                'wage': contract.wage,
                'position_allowance': contract.position_allowance,
                'job_allowance': contract.job_allowance,
            })
            slip.action_compute()
            created += 1

        self.result_msg = f'Created and computed {created} payslips.'
        return {
            'type': 'ir.actions.act_window',
            'res_model': self._name,
            'res_id': self.id,
            'view_mode': 'form',
            'target': 'new',
        }
