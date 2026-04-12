# -*- coding: utf-8 -*-
from odoo import api, fields, models, _


class HrPositionHistory(models.Model):
    """
    Lịch sử vị trí/phòng ban của nhân viên.
    Ghi nhận mọi thay đổi chức danh, phòng ban, chi nhánh theo thời gian.
    Bản ghi được tạo tự động khi có thay đổi trên hr.employee.
    """
    _name = 'hr.position.history'
    _description = 'Employee Position History'
    _order = 'date_start desc, id desc'
    _rec_name = 'display_name_computed'

    # CÁC TRƯỜNG CHÍNH
    employee_id = fields.Many2one(
        'hr.employee',
        string='Employee',
        required=True,
        ondelete='cascade',
        index=True,
    )
    company_id = fields.Many2one(
        'res.company',
        string='Company',
        related='employee_id.company_id',
        store=True,
    )

    date_start = fields.Date(
        string='Start Date',
        required=True,
        default=fields.Date.today,
    )
    date_end = fields.Date(
        string='End Date',
        help='Để trống nếu đây là vị trí hiện tại',
    )

    is_current = fields.Boolean(
        string='Current Position?',
        compute='_compute_is_current',
        store=True,
    )

    # THÔNG TIN VỊ TRÍ
    department_id = fields.Many2one(
        'hr.department',
        string='Department',
        tracking=True,
    )
    branch_id = fields.Many2one(
        'hr.department',
        string='Branch',
        domain="[('department_type', '=', 'branch')]",
        compute='_compute_branch_id',
        store=True,
    )
    job_id = fields.Many2one(
        'hr.job',
        string='Job Position',
        tracking=True,
    )
    job_title = fields.Char(
        string='Job Title',
        help='Chức danh cụ thể tại thời điểm này',
    )

    # LÝ DO THAY ĐỔI
    change_type = fields.Selection([
        ('onboarding', 'Onboarding'),
        ('promotion', 'Promotion'),
        ('transfer', 'Transfer'),
        ('branch_transfer', 'Branch Transfer'),
        ('demotion', 'Demotion'),
        ('title_change', 'Title Change'),
        ('other', 'Other'),
    ], string='Change Type', default='other', tracking=True)

    reason = fields.Text(
        string='Reason',
        tracking=True,
    )

    approved_by = fields.Many2one(
        'res.users',
        string='Approved By',
        default=lambda self: self.env.user,
    )

    # DISPLAY NAME
    display_name_computed = fields.Char(
        string='Description',
        compute='_compute_display_name_computed',
    )

    # COMPUTE METHODS
    @api.depends('date_end')
    def _compute_is_current(self):
        for record in self:
            record.is_current = not bool(record.date_end)

    @api.depends('department_id', 'department_id.department_type',
                 'department_id.parent_id')
    def _compute_branch_id(self):
        for record in self:
            if record.department_id:
                record.branch_id = record.department_id.get_branch_id()
            else:
                record.branch_id = False

    @api.depends('job_id', 'department_id', 'date_start', 'is_current')
    def _compute_display_name_computed(self):
        for record in self:
            parts = []
            if record.job_id:
                parts.append(record.job_id.name)
            if record.department_id:
                parts.append(record.department_id.name)
            if record.date_start:
                parts.append(str(record.date_start))
            if record.is_current:
                parts.append('(Current)')
            record.display_name_computed = ' | '.join(parts) if parts else _('No Information')
