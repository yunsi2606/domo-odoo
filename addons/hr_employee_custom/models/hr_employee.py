# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class HrEmployee(models.Model):
    """
    Mở rộng model hr.employee để chuẩn hóa hồ sơ nhân viên:
    - Mã nhân viên duy nhất (Employee ID)
    - Thông tin cá nhân đầy đủ (CMND/CCCD, liên hệ khẩn cấp)
    - Thông tin ngân hàng
    - Lịch sử vị trí/phòng ban
    - Quản lý tài liệu
    - Liên kết với quy trình tuyển dụng
    """
    _inherit = 'hr.employee'

    # ĐỊNH DANH
    employee_code = fields.Char(
        string='Employee Code',
        copy=False,
        readonly=True,
        index=True,
        default=lambda self: _('New'),
        tracking=True,
        help='Mã số nhân viên duy nhất, tự động tạo theo chuỗi EMP/YYYY/XXXX',
    )

    # THÔNG TIN CCCD / CMND MỞ RỘNG
    id_issue_date = fields.Date(
        string='ID Issue Date',
        groups='hr.group_hr_user',
        tracking=True,
    )
    id_issue_place = fields.Char(
        string='ID Issue Place',
        groups='hr.group_hr_user',
        tracking=True,
    )

    # LIÊN HỆ KHẨN CẤP
    emergency_contact_name = fields.Char(
        string='Emergency Contact Name',
        groups='hr.group_hr_user',
        help='Họ tên người liên hệ khi khẩn cấp',
    )
    emergency_contact_phone = fields.Char(
        string='Emergency Contact Phone',
        groups='hr.group_hr_user',
    )
    emergency_contact_relation = fields.Selection([
        ('spouse', 'Spouse'),
        ('parent', 'Parent'),
        ('child', 'Child'),
        ('sibling', 'Sibling'),
        ('friend', 'Friend'),
        ('other', 'Other'),
    ], string='Emergency Contact Relation', groups='hr.group_hr_user')

    # THÔNG TIN CÔNG VIỆC MỞ RỘNG
    branch_id = fields.Many2one(
        'hr.department',
        string='Branch',
        domain="[('department_type', '=', 'branch')]",
        compute='_compute_branch_id',
        store=True,
        readonly=False,
        tracking=True,
        help='Chi nhánh nhân viên đang làm việc (tự động tính từ phòng ban)',
    )

    join_date = fields.Date(
        string='Join Date',
        tracking=True,
        help='Ngày nhân viên chính thức gia nhập công ty',
    )

    employee_status = fields.Selection([
        ('probation', 'Probation'),
        ('official', 'Official'),
        ('resigned', 'Resigned'),
        ('suspended', 'Suspended'),
        ('maternity', 'Maternity'),
    ], string='Employee Status',
       default='official',
       tracking=True,
       help='Trạng thái làm việc hiện tại của nhân viên',
    )

    resignation_date = fields.Date(
        string='Resignation Date',
        tracking=True,
        groups='hr.group_hr_user',
    )

    resignation_reason = fields.Text(
        string='Resignation Reason',
        groups='hr.group_hr_user',
    )

    # THÔNG TIN NGÂN HÀNG
    bank_name = fields.Char(
        string='Bank Name',
        groups='hr.group_hr_user',
        help='Ngân hàng nhân viên nhận lương',
    )
    bank_account_number = fields.Char(
        string='Bank Account Number',
        groups='hr.group_hr_user',
        help='Số tài khoản ngân hàng để nhận lương',
    )
    bank_account_holder = fields.Char(
        string='Bank Account Holder',
        groups='hr.group_hr_user',
        help='Tên chủ tài khoản (thường là tên nhân viên)',
    )
    bank_branch_name = fields.Char(
        string='Bank Branch Name',
        groups='hr.group_hr_user',
    )

    # GIẤY TỜ & LỊCH SỬ
    document_ids = fields.One2many(
        'hr.employee.document',
        'employee_id',
        string='Documents',
        groups='hr.group_hr_user',
    )
    document_count = fields.Integer(
        string='Number of Documents',
        compute='_compute_document_count',
    )

    position_history_ids = fields.One2many(
        'hr.position.history',
        'employee_id',
        string='Position History',
        groups='hr.group_hr_user',
    )
    position_history_count = fields.Integer(
        string='Number of Position Changes',
        compute='_compute_position_history_count',
    )

    # KẾT NỐI TUYỂN DỤNG
    applicant_id = fields.Many2one(
        'hr.applicant',
        string='Original Applicant Record',
        readonly=True,
        groups='hr.group_hr_user',
        help='Hồ sơ ứng viên từ quy trình tuyển dụng đã được chuyển đổi thành nhân viên này',
    )

    # THỐNG KÊ
    expiring_document_count = fields.Integer(
        string='Expiring Documents',
        compute='_compute_expiring_document_count',
        help='Số tài liệu sắp hết hạn trong 30 ngày tới',
    )

    # COMPUTE METHODS
    @api.depends('department_id', 'department_id.department_type',
                 'department_id.parent_id', 'department_id.parent_id.department_type')
    def _compute_branch_id(self):
        for employee in self:
            if employee.department_id:
                employee.branch_id = employee.department_id.get_branch_id()
            else:
                employee.branch_id = False

    def _compute_document_count(self):
        for employee in self:
            employee.document_count = len(employee.document_ids)

    def _compute_position_history_count(self):
        for employee in self:
            employee.position_history_count = len(employee.position_history_ids)

    def _compute_expiring_document_count(self):
        today = fields.Date.today()
        for employee in self:
            expiring = employee.document_ids.filtered(
                lambda d: d.expiry_date and (d.expiry_date - today).days <= 30
                and d.state == 'valid'
            )
            employee.expiring_document_count = len(expiring)

    # CRUD OVERRIDE
    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('employee_code', _('New')) == _('New'):
                vals['employee_code'] = self.env['ir.sequence'].next_by_code(
                    'hr.employee.code'
                ) or _('New')
        employees = super().create(vals_list)
        # Tạo bản ghi lịch sử vị trí ban đầu
        for employee in employees:
            if employee.job_id or employee.department_id:
                employee._create_position_history('Onboarding')
        return employees

    def write(self, vals):
        # Theo dõi thay đổi vị trí/phòng ban → tạo lịch sử
        position_fields = {'job_id', 'department_id', 'job_title'}
        position_changed = bool(position_fields & set(vals.keys()))

        # Lưu trạng thái cũ trước khi ghi
        old_data = {}
        if position_changed:
            for employee in self:
                old_data[employee.id] = {
                    'job_id': employee.job_id.id,
                    'department_id': employee.department_id.id,
                    'job_title': employee.job_title,
                }

        result = super().write(vals)

        # Tạo lịch sử vị trí nếu có thay đổi thực sự
        if position_changed:
            for employee in self:
                old = old_data.get(employee.id, {})
                if (vals.get('job_id') and vals['job_id'] != old.get('job_id')) or \
                   (vals.get('department_id') and vals['department_id'] != old.get('department_id')):
                    employee._create_position_history('Change Position / Transfer')

        return result

    # HELPER METHODS
    def _create_position_history(self, reason_note=''):
        """Ghi nhận lịch sử vị trí hiện tại của nhân viên"""
        self.ensure_one()
        # Đóng bản ghi lịch sử đang mở
        open_history = self.env['hr.position.history'].search([
            ('employee_id', '=', self.id),
            ('date_end', '=', False),
        ])
        if open_history:
            open_history.write({'date_end': fields.Date.today()})

        # Tạo bản ghi mới
        self.env['hr.position.history'].create({
            'employee_id': self.id,
            'date_start': fields.Date.today(),
            'department_id': self.department_id.id,
            'job_id': self.job_id.id,
            'job_title': self.job_title or (self.job_id.name if self.job_id else ''),
            'reason': reason_note,
            'approved_by': self.env.user.id,
        })

    # ACTION METHODS
    def action_view_documents(self):
        """Mở danh sách tài liệu của nhân viên"""
        self.ensure_one()
        return {
            'name': _('Documents - %s') % self.name,
            'type': 'ir.actions.act_window',
            'res_model': 'hr.employee.document',
            'view_mode': 'list,form',
            'domain': [('employee_id', '=', self.id)],
            'context': {'default_employee_id': self.id},
        }

    def action_view_position_history(self):
        """Mở lịch sử vị trí của nhân viên"""
        self.ensure_one()
        return {
            'name': _('Position History - %s') % self.name,
            'type': 'ir.actions.act_window',
            'res_model': 'hr.position.history',
            'view_mode': 'list,form',
            'domain': [('employee_id', '=', self.id)],
            'context': {'default_employee_id': self.id},
        }

    def action_mark_resigned(self):
        """Đánh dấu nhân viên nghỉ việc"""
        for employee in self:
            employee.write({
                'employee_status': 'resigned',
                'resignation_date': fields.Date.today(),
                'active': False,
            })
        return True
