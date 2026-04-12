# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError


class AttendanceCorrection(models.Model):
    """
    Yêu cầu sửa công — Nhân viên gửi yêu cầu khi quên check-in/check-out
    hoặc ghi nhầm giờ. Quản lý xem xét và phê duyệt để cập nhật dữ liệu.
    """
    _name = 'hr.attendance.correction'
    _description = 'Attendance Correction Request'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'create_date desc, id desc'
    _rec_name = 'name'

    # ──────────────────────────────────────────────────────────────
    # Core Fields
    # ──────────────────────────────────────────────────────────────
    name = fields.Char(
        string='Reference',
        required=True,
        copy=False,
        readonly=True,
        default=lambda self: _('New'),
        tracking=True,
    )

    employee_id = fields.Many2one(
        'hr.employee',
        string='Employee',
        required=True,
        tracking=True,
        help='Nhân viên gửi yêu cầu sửa công',
    )
    department_id = fields.Many2one(
        'hr.department',
        string='Department',
        related='employee_id.department_id',
        store=True,
    )
    manager_id = fields.Many2one(
        'hr.employee',
        string='Manager',
        related='employee_id.parent_id',
        store=True,
        help='Quản lý trực tiếp cần phê duyệt',
    )

    date = fields.Date(
        string='Date',
        required=True,
        tracking=True,
        help='Ngày cần sửa công',
    )

    # ── Loại lỗi cần sửa ──
    correction_type = fields.Selection([
        ('forgot_checkin', 'Forgot Check-in'),
        ('forgot_checkout', 'Forgot Check-out'),
        ('wrong_time', 'Wrong Time Recorded'),
        ('missing_record', 'Missing Record (Full Day)'),
        ('other', 'Other'),
    ], string='Correction Type', required=True,
       default='forgot_checkout', tracking=True,
       help='Loại lỗi chấm công cần sửa')

    # ── Giờ thực tế (nhân viên khai báo) ──
    requested_check_in = fields.Datetime(
        string='Requested Check-in',
        tracking=True,
        help='Giờ check-in thực tế theo khai báo của nhân viên',
    )
    requested_check_out = fields.Datetime(
        string='Requested Check-out',
        tracking=True,
        help='Giờ check-out thực tế theo khai báo của nhân viên',
    )

    # ── Giờ hiện tại trên hệ thống (nếu có) ──
    actual_check_in = fields.Datetime(
        string='Current Check-in (System)',
        readonly=True,
        help='Giờ check-in hiện tại trên hệ thống',
    )
    actual_check_out = fields.Datetime(
        string='Current Check-out (System)',
        readonly=True,
        help='Giờ check-out hiện tại trên hệ thống',
    )

    # ── Bản ghi chấm công liên quan ──
    attendance_id = fields.Many2one(
        'hr.attendance',
        string='Related Attendance',
        tracking=True,
        help='Bản ghi chấm công cần sửa (để trống nếu bị thiếu hoàn toàn)',
    )

    # ── Lý do / Bằng chứng ──
    reason = fields.Text(
        string='Reason',
        required=True,
        help='Lý do xin sửa công (bắt buộc)',
    )
    evidence_attachment_ids = fields.Many2many(
        'ir.attachment',
        'correction_evidence_attachment_rel',
        'correction_id',
        'attachment_id',
        string='Evidence / Attachments',
        help='Bằng chứng đính kèm (ảnh, email, xác nhận từ quản lý...)',
    )

    # ── Phê duyệt ──
    approved_by = fields.Many2one(
        'res.users',
        string='Approved By',
        readonly=True,
        tracking=True,
    )
    approval_date = fields.Datetime(
        string='Approval Date',
        readonly=True,
    )
    rejection_reason = fields.Text(
        string='Rejection Reason',
        tracking=True,
        help='Lý do từ chối (nếu bị từ chối)',
    )

    # ── Trạng thái ──
    state = fields.Selection([
        ('draft', 'Draft'),
        ('submitted', 'Submitted'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('cancelled', 'Cancelled'),
    ], string='Status', default='draft',
       tracking=True, required=True, copy=False)

    # ── Công thêm sau xử lý ──
    new_attendance_id = fields.Many2one(
        'hr.attendance',
        string='Created/Updated Attendance',
        readonly=True,
        help='Bản ghi chấm công đã được tạo/cập nhật sau khi phê duyệt',
    )

    # ──────────────────────────────────────────────────────────────
    # Constraints
    # ──────────────────────────────────────────────────────────────
    @api.constrains('requested_check_in', 'requested_check_out')
    def _check_times(self):
        for record in self:
            if (record.requested_check_in and record.requested_check_out
                    and record.requested_check_in > record.requested_check_out):
                raise ValidationError(_(
                    'Requested Check-in time must be before Check-out time.'
                ))

    @api.constrains('date')
    def _check_date(self):
        for record in self:
            if record.date and record.date > fields.Date.today():
                raise ValidationError(_('Cannot request correction for a future date.'))

    # ──────────────────────────────────────────────────────────────
    # CRUD
    # ──────────────────────────────────────────────────────────────
    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', _('New')) == _('New'):
                vals['name'] = self.env['ir.sequence'].next_by_code(
                    'hr.attendance.correction') or _('New')
        return super().create(vals_list)

    # ──────────────────────────────────────────────────────────────
    # Onchange
    # ──────────────────────────────────────────────────────────────
    @api.onchange('employee_id', 'date')
    def _onchange_employee_date(self):
        """Tự động tìm bản ghi chấm công liên quan khi thay đổi nhân viên/ngày"""
        if self.employee_id and self.date:
            attendance = self.env['hr.attendance'].search([
                ('employee_id', '=', self.employee_id.id),
                ('check_in', '>=', fields.Datetime.from_string(str(self.date) + ' 00:00:00')),
                ('check_in', '<=', fields.Datetime.from_string(str(self.date) + ' 23:59:59')),
            ], limit=1)
            if attendance:
                self.attendance_id = attendance.id
                self.actual_check_in = attendance.check_in
                self.actual_check_out = attendance.check_out
            else:
                self.attendance_id = False
                self.actual_check_in = False
                self.actual_check_out = False

    # ──────────────────────────────────────────────────────────────
    # Action Methods
    # ──────────────────────────────────────────────────────────────
    def action_submit(self):
        """Nhân viên gửi yêu cầu sửa công"""
        for record in self:
            if record.state != 'draft':
                raise UserError(_('Only draft requests can be submitted.'))
            if not record.reason:
                raise UserError(_('Please provide a reason for the correction request.'))
            record.write({'state': 'submitted'})
            record._notify_manager()
        return True

    def action_approve(self):
        """Quản lý phê duyệt và áp dụng sửa công"""
        for record in self:
            if record.state != 'submitted':
                raise UserError(_('Only submitted requests can be approved.'))
            # Áp dụng thay đổi vào bản ghi chấm công
            record._apply_correction()
            record.write({
                'state': 'approved',
                'approved_by': self.env.user.id,
                'approval_date': fields.Datetime.now(),
            })
            record._notify_employee_approved()
        return True

    def action_reject(self):
        """Quản lý từ chối yêu cầu"""
        for record in self:
            if record.state != 'submitted':
                raise UserError(_('Only submitted requests can be rejected.'))
            if not record.rejection_reason:
                raise UserError(_('Please provide a rejection reason.'))
            record.write({
                'state': 'rejected',
                'approved_by': self.env.user.id,
                'approval_date': fields.Datetime.now(),
            })
            record._notify_employee_rejected()
        return True

    def action_cancel(self):
        """Huỷ yêu cầu"""
        for record in self:
            if record.state in ('approved',):
                raise UserError(_('Cannot cancel an already approved request.'))
            record.write({'state': 'cancelled'})
        return True

    def action_reset_to_draft(self):
        """Đặt lại về nháp"""
        for record in self:
            if record.state not in ('submitted', 'rejected', 'cancelled'):
                raise UserError(_('Only submitted/rejected/cancelled requests can be reset.'))
            record.write({
                'state': 'draft',
                'rejection_reason': False,
                'approved_by': False,
                'approval_date': False,
            })
        return True

    # ──────────────────────────────────────────────────────────────
    # Core Logic: Apply Correction
    # ──────────────────────────────────────────────────────────────
    def _apply_correction(self):
        """
        Áp dụng yêu cầu sửa công vào hệ thống:
        - Nếu đã có bản ghi attendance → cập nhật check_in/check_out
        - Nếu chưa có → tạo mới bản ghi attendance
        """
        self.ensure_one()
        AttendanceModel = self.env['hr.attendance']

        vals = {
            'source': 'correction',
            'correction_id': self.id,
            'note': f'Corrected via request {self.name}: {self.reason}',
        }

        if self.correction_type == 'forgot_checkin':
            if self.attendance_id:
                self.attendance_id.write({
                    'check_in': self.requested_check_in,
                    **vals,
                })
                self.new_attendance_id = self.attendance_id
            else:
                new_att = AttendanceModel.create({
                    'employee_id': self.employee_id.id,
                    'check_in': self.requested_check_in,
                    'check_out': self.requested_check_out,
                    **vals,
                })
                self.new_attendance_id = new_att

        elif self.correction_type == 'forgot_checkout':
            if self.attendance_id:
                self.attendance_id.write({
                    'check_out': self.requested_check_out,
                    **vals,
                })
                self.new_attendance_id = self.attendance_id
            else:
                raise UserError(_(
                    'No attendance record found to update check-out. '
                    'Please select "Missing Record" type instead.'
                ))

        elif self.correction_type == 'wrong_time':
            if self.attendance_id:
                write_vals = {**vals}
                if self.requested_check_in:
                    write_vals['check_in'] = self.requested_check_in
                if self.requested_check_out:
                    write_vals['check_out'] = self.requested_check_out
                self.attendance_id.write(write_vals)
                self.new_attendance_id = self.attendance_id
            else:
                raise UserError(_(
                    'No attendance record found to update. '
                    'Please select "Missing Record" type instead.'
                ))

        elif self.correction_type == 'missing_record':
            # Kiểm tra xem đã có bản ghi nào chưa
            existing = AttendanceModel.search([
                ('employee_id', '=', self.employee_id.id),
                ('check_in', '>=', fields.Datetime.from_string(
                    str(self.date) + ' 00:00:00')),
                ('check_in', '<=', fields.Datetime.from_string(
                    str(self.date) + ' 23:59:59')),
            ], limit=1)
            if existing:
                existing.write({
                    'check_in': self.requested_check_in or existing.check_in,
                    'check_out': self.requested_check_out or existing.check_out,
                    **vals,
                })
                self.new_attendance_id = existing
            else:
                new_att = AttendanceModel.create({
                    'employee_id': self.employee_id.id,
                    'check_in': self.requested_check_in,
                    'check_out': self.requested_check_out,
                    **vals,
                })
                self.new_attendance_id = new_att
        else:
            # other — chỉ ghi chú
            if self.attendance_id:
                self.attendance_id.write({**vals})
                self.new_attendance_id = self.attendance_id

    # ──────────────────────────────────────────────────────────────
    # Notifications
    # ──────────────────────────────────────────────────────────────
    def _notify_manager(self):
        """Thông báo cho quản lý trực tiếp khi nhân viên gửi yêu cầu"""
        self.ensure_one()
        template = self.env.ref(
            'hr_attendance_custom.mail_template_correction_submitted',
            raise_if_not_found=False,
        )
        if template:
            template.send_mail(self.id, force_send=True)

    def _notify_employee_approved(self):
        """Thông báo cho nhân viên khi yêu cầu được phê duyệt"""
        self.ensure_one()
        template = self.env.ref(
            'hr_attendance_custom.mail_template_correction_approved',
            raise_if_not_found=False,
        )
        if template:
            template.send_mail(self.id, force_send=True)

    def _notify_employee_rejected(self):
        """Thông báo cho nhân viên khi yêu cầu bị từ chối"""
        self.ensure_one()
        template = self.env.ref(
            'hr_attendance_custom.mail_template_correction_rejected',
            raise_if_not_found=False,
        )
        if template:
            template.send_mail(self.id, force_send=True)
