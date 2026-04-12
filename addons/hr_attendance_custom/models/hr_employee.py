# -*- coding: utf-8 -*-
from odoo import api, fields, models, _


class HrEmployee(models.Model):
    """
    Mở rộng hr.employee để thêm:
    - Mã PIN chấm công (cho kiosk)
    - Thống kê chấm công nhanh
    """
    _inherit = 'hr.employee'

    # ──────────────────────────────────────────────────────────────
    # PIN cho Kiosk Chấm công
    # ──────────────────────────────────────────────────────────────
    attendance_pin = fields.Char(
        string='Attendance PIN',
        size=6,
        help='Mã PIN 4–6 chữ số dùng để check-in/check-out tại kiosk',
        groups='hr.group_hr_user',
    )

    # ──────────────────────────────────────────────────────────────
    # Attendance Summary (Smart Buttons)
    # ──────────────────────────────────────────────────────────────
    correction_count = fields.Integer(
        string='Correction Requests',
        compute='_compute_correction_count',
        help='Số yêu cầu sửa công đang chờ xử lý',
    )
    pending_correction_count = fields.Integer(
        string='Pending Corrections',
        compute='_compute_correction_count',
    )

    # ──────────────────────────────────────────────────────────────
    # Compute
    # ──────────────────────────────────────────────────────────────
    def _compute_correction_count(self):
        Correction = self.env['hr.attendance.correction']
        for employee in self:
            all_corrections = Correction.search_count([
                ('employee_id', '=', employee.id),
            ])
            pending = Correction.search_count([
                ('employee_id', '=', employee.id),
                ('state', '=', 'submitted'),
            ])
            employee.correction_count = all_corrections
            employee.pending_correction_count = pending

    # ──────────────────────────────────────────────────────────────
    # Action Buttons
    # ──────────────────────────────────────────────────────────────
    def action_view_correction_requests(self):
        self.ensure_one()
        return {
            'name': _('Attendance Correction Requests'),
            'type': 'ir.actions.act_window',
            'res_model': 'hr.attendance.correction',
            'view_mode': 'list,form',
            'domain': [('employee_id', '=', self.id)],
            'context': {
                'default_employee_id': self.id,
            },
        }

    # ──────────────────────────────────────────────────────────────
    # PIN Validation for Kiosk
    # ──────────────────────────────────────────────────────────────
    @api.model
    def get_employee_by_pin(self, pin):
        """
        Tìm nhân viên theo mã PIN (dùng cho kiosk self-service).
        Trả về dict thông tin nhân viên hoặc False.
        """
        employee = self.sudo().search([
            ('attendance_pin', '=', pin),
            ('active', '=', True),
        ], limit=1)
        if not employee:
            return False
        return {
            'id': employee.id,
            'name': employee.name,
            'job_title': employee.job_title or '',
            'department': employee.department_id.name if employee.department_id else '',
            'image': employee.image_128 and employee.image_128.decode() or '',
        }
