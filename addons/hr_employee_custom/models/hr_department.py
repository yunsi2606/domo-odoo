# -*- coding: utf-8 -*-
from odoo import api, fields, models, _


class HrDepartment(models.Model):
    """
    Mở rộng hr.department để phân biệt chi nhánh và phòng ban
    trong cùng một model phân cấp.
    Chi nhánh là đơn vị cấp cao nhất (không có parent hoặc parent là công ty).
    Phòng ban là đơn vị trực thuộc chi nhánh.
    """
    _inherit = 'hr.department'

    department_type = fields.Selection([
        ('branch', 'Branch'),
        ('department', 'Department'),
        ('division', 'Division'),
        ('team', 'Team'),
    ], string='Department Type', default='department',
       tracking=True,
       help='Phân loại đơn vị tổ chức: chi nhánh, phòng ban, bộ phận hoặc nhóm')

    branch_address = fields.Char(
        string='Branch Address',
        help='Địa chỉ chi nhánh (chỉ dùng khi loại là Chi nhánh)',
    )

    branch_phone = fields.Char(
        string='Branch Phone',
        help='Số điện thoại liên hệ chi nhánh',
    )

    branch_email = fields.Char(
        string='Branch Email',
    )

    branch_manager_id = fields.Many2one(
        'hr.employee',
        string='Branch Manager',
        help='Nhân viên giữ chức vụ quản lý chi nhánh',
        domain="[('department_id', '=', id)]",
    )

    # Computed: số nhân viên trực tiếp và toàn bộ
    total_employee_count = fields.Integer(
        string='Total Employee',
        compute='_compute_total_employee_count',
        help='Tổng số nhân viên thuộc đơn vị này và các đơn vị con',
    )

    is_branch = fields.Boolean(
        string='Is Branch?',
        compute='_compute_is_branch',
        store=True,
        help='True nếu đây là chi nhánh (department_type = branch)',
    )

    @api.depends('department_type')
    def _compute_is_branch(self):
        for record in self:
            record.is_branch = record.department_type == 'branch'

    def _compute_total_employee_count(self):
        for department in self:
            # Lấy tất cả phòng ban con (đệ quy)
            all_dept_ids = self._get_child_department_ids(department.id)
            all_dept_ids.append(department.id)
            employee_count = self.env['hr.employee'].search_count([
                ('department_id', 'in', all_dept_ids),
                ('active', '=', True),
            ])
            department.total_employee_count = employee_count

    def _get_child_department_ids(self, dept_id):
        """Lấy danh sách ID phòng ban con đệ quy"""
        child_depts = self.search([('parent_id', '=', dept_id)])
        result = []
        for child in child_depts:
            result.append(child.id)
            result.extend(self._get_child_department_ids(child.id))
        return result

    def get_branch_id(self):
        """Trả về chi nhánh gốc của đơn vị này (leo lên cây đến branch)"""
        self.ensure_one()
        dept = self
        while dept:
            if dept.department_type == 'branch':
                return dept
            dept = dept.parent_id
        return self  # fallback về chính nó
