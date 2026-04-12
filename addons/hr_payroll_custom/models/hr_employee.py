# -*- coding: utf-8 -*-
from odoo import fields, models


class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    num_dependents = fields.Integer('Number of Dependents', default=0,
                                    help='Số người phụ thuộc (giảm trừ 4.4tr/người)')
    abc_rating = fields.Selection([('A', 'A'), ('B', 'B'), ('C', 'C')],
                                  string='ABC Rating (this month)',
                                  tracking=True,
                                  help='Xếp loại ABC cuối tháng do quản lý chấm')

    payslip_ids = fields.One2many('hr.payslip.custom', 'employee_id', 'Payslips')
    payslip_count = fields.Integer(compute='_compute_payslip_count')
    sales_record_ids = fields.One2many('hr.sales.record', 'employee_id', 'Sales Records')

    def _compute_payslip_count(self):
        for e in self:
            e.payslip_count = len(e.payslip_ids)

    def action_view_payslips(self):
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'hr.payslip.custom',
            'view_mode': 'list,form',
            'domain': [('employee_id', '=', self.id)],
        }


class HrContract(models.Model):
    _inherit = 'hr.contract'

    position_allowance = fields.Monetary('Position Allowance',
                                         help='Phụ cấp chức vụ')
    job_allowance = fields.Monetary('Job Allowance',
                                    help='Phụ cấp đầu công việc')
