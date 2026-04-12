# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError
from datetime import date
from dateutil.relativedelta import relativedelta


class HrContract(models.Model):
    """
    Mở rộng hr.contract để thêm:
    - Luồng phê duyệt 3 cấp (Quản lý chi nhánh → Giám đốc)
    - Bảng phụ cấp chi tiết
    - Cảnh báo hết hạn tự động
    - Xác nhận điện tử từ nhân viên
    - Thỏa thuận và ghi chú đặc biệt
    """
    _inherit = 'hr.contract'

    @api.model
    def _default_name(self):
        self.env.cr.execute("SELECT name FROM hr_contract WHERE name LIKE 'HD-%'")
        max_num = 0
        for row in self.env.cr.fetchall():
            num_str = row[0].replace('HD-', '')
            if num_str.isdigit():
                max_num = max(max_num, int(num_str))
        return f'HD-{max_num + 1}'

    name = fields.Char(required=True, default=_default_name, copy=False)

    # LUỒNG PHÊ DUYỆT
    approval_state = fields.Selection([
        ('draft', 'Draft'),
        ('submitted', 'Submitted'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ], string='Approval State',
       default='draft',
       tracking=True,
       copy=False,
       help='Luồng phê duyệt riêng biệt với trạng thái hợp đồng Odoo chuẩn',
    )

    submitted_by = fields.Many2one(
        'res.users',
        string='Submitted By',
        readonly=True,
        copy=False,
        tracking=True,
    )
    submitted_date = fields.Datetime(
        string='Submitted Date',
        readonly=True,
        copy=False,
    )
    approved_by = fields.Many2one(
        'res.users',
        string='Approved By',
        readonly=True,
        copy=False,
        tracking=True,
    )
    approved_date = fields.Datetime(
        string='Ngày phê duyệt',
        readonly=True,
        copy=False,
    )
    rejection_reason = fields.Text(
        string='Rejection Reason',
        copy=False,
    )

    # PHỤ CẤP
    allowance_ids = fields.One2many(
        'hr.contract.allowance',
        'contract_id',
        string='Allowance',
    )

    total_allowance = fields.Monetary(
        string='Total Allowance',
        compute='_compute_total_allowance',
        store=True,
        currency_field='currency_id',
    )

    total_package = fields.Monetary(
        string='Total Package',
        compute='_compute_total_package',
        store=True,
        currency_field='currency_id',
        help='Lương cơ bản + Tổng phụ cấp',
    )

    # THỎA THUẬN KHÁC
    leave_policy_notes = fields.Text(
        string='Leave Policy Notes',
        help='Ghi chú về số ngày nghỉ phép, điều kiện nghỉ đặc biệt...',
    )
    other_agreements = fields.Text(
        string='Other Agreements',
        help='Các điều khoản bổ sung ngoài quy định chung',
    )
    probation_period_months = fields.Integer(
        string='Probation Period (months)',
        default=2,
    )

    # XÁC NHẬN TỪ NHÂN VIÊN
    employee_confirmed = fields.Boolean(
        string='Employee Confirmed',
        default=False,
        copy=False,
        tracking=True,
    )
    employee_confirmed_date = fields.Datetime(
        string='Employee Confirmed Date',
        readonly=True,
        copy=False,
    )

    # CẢNH BÁO HẾT HẠN
    days_to_expiry = fields.Integer(
        string='Days to Expiry',
        compute='_compute_days_to_expiry',
        store=True,
        help='Số ngày còn lại đến ngày kết thúc hợp đồng',
    )

    expiry_alert_level = fields.Selection([
        ('ok', 'Normal'),
        ('warning', 'Expiring soon (≤60 days)'),
        ('danger', 'Expiring immediately (≤30 days)'),
        ('expired', 'Expired'),
    ], string='Alert Level',
       compute='_compute_days_to_expiry',
       store=True,
    )

    # CHI NHÁNH (denormalized để dùng trong record rules)
    branch_id = fields.Many2one(
        'hr.department',
        string='Branch',
        compute='_compute_branch_id',
        store=True,
        domain="[('department_type', '=', 'branch')]",
        help='Chi nhánh của nhân viên (tự tính từ phòng ban)',
    )

    # COMPUTE METHODS
    @api.depends('allowance_ids.amount')
    def _compute_total_allowance(self):
        for contract in self:
            contract.total_allowance = sum(contract.allowance_ids.mapped('amount'))

    @api.depends('wage', 'total_allowance')
    def _compute_total_package(self):
        for contract in self:
            contract.total_package = (contract.wage or 0.0) + contract.total_allowance

    @api.depends('date_end')
    def _compute_days_to_expiry(self):
        today = date.today()
        for contract in self:
            if not contract.date_end:
                contract.days_to_expiry = 9999
                contract.expiry_alert_level = 'ok'
                continue
            delta = (contract.date_end - today).days
            contract.days_to_expiry = delta
            if delta < 0:
                contract.expiry_alert_level = 'expired'
            elif delta <= 30:
                contract.expiry_alert_level = 'danger'
            elif delta <= 60:
                contract.expiry_alert_level = 'warning'
            else:
                contract.expiry_alert_level = 'ok'

    @api.depends('employee_id', 'employee_id.department_id')
    def _compute_branch_id(self):
        for contract in self:
            dept = contract.employee_id.department_id
            if dept and hasattr(dept, 'get_branch_id'):
                contract.branch_id = dept.get_branch_id()
            else:
                contract.branch_id = False

    @api.onchange('employee_id')
    def _onchange_employee_id_custom(self):
        """Khi chọn nhân viên, tự động điền chức vụ, phòng ban và các thông tin từ Offer Letter (nếu có)."""
        if self.employee_id:
            if self.employee_id.job_id:
                self.job_id = self.employee_id.job_id
            if self.employee_id.department_id:
                self.department_id = self.employee_id.department_id
                
            # Lấy các thông tin từ Offer Letter đã Accepted của tuyển dụng (nếu module hr_recruitment_custom cài đặt)
            if 'hr.offer.letter' in self.env:
                offer = self.env['hr.offer.letter'].search([
                    ('employee_id', '=', self.employee_id.id),
                    ('state', 'in', ['accepted', 'done'])
                ], order='id desc', limit=1)
                
                if offer:
                    if offer.offered_salary and not self.wage:
                        self.wage = offer.offered_salary
                    if offer.start_date and not self.date_start:
                        self.date_start = offer.start_date
                    if offer.probation_period:
                        self.probation_period_months = offer.probation_period


    # APPROVAL WORKFLOW ACTIONS
    def action_submit_for_approval(self):
        """Quản lý chi nhánh gửi hợp đồng lên Giám đốc phê duyệt."""
        for contract in self:
            if contract.approval_state != 'draft':
                raise UserError(
                    _('Only contracts in draft state can be submitted for approval.')
                )
            if not contract.employee_id:
                raise UserError(_('Contract must have an employee before being submitted for approval.'))
            if not contract.wage:
                raise UserError(_('Please enter the basic salary before submitting for approval.'))
            contract.write({
                'approval_state': 'submitted',
                'submitted_by': self.env.user.id,
                'submitted_date': fields.Datetime.now(),
                'rejection_reason': False,
            })
            contract.message_post(
                body=_('Contract has been submitted for approval by %s.') % self.env.user.name,
                subtype_xmlid='mail.mt_note',
            )
        return True

    def action_approve(self):
        """Giám đốc phê duyệt hợp đồng và chuyển sang trạng thái 'open' (running)."""
        for contract in self:
            if contract.approval_state != 'submitted':
                raise UserError(_('Only contracts in submitted state can be approved.'))
            contract.write({
                'approval_state': 'approved',
                'approved_by': self.env.user.id,
                'approved_date': fields.Datetime.now(),
                'state': 'open',
            })
            contract.message_post(
                body=_('The contract has been approved by %s. The contract is officially effective.') % self.env.user.name,
                subtype_xmlid='mail.mt_note',
            )
            # Thông báo cho nhân viên
            if contract.employee_id.user_id:
                contract.message_post(
                    body=_('The contract has been approved by %s. Please log in to the system to view details and confirm.') % self.env.user.name,
                    partner_ids=[contract.employee_id.user_id.partner_id.id],
                    subtype_xmlid='mail.mt_comment',
                )
        return True

    def action_reject(self):
        """Giám đốc từ chối hợp đồng."""
        return {
            'type': 'ir.actions.act_window',
            'name': _('Rejection Reason'),
            'res_model': 'hr.contract.reject.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_contract_id': self.id},
        }

    def action_reset_to_draft(self):
        """Đưa hợp đồng về bản nháp để chỉnh sửa lại."""
        for contract in self:
            if contract.approval_state not in ('submitted', 'rejected'):
                raise UserError(_('Only contracts in submitted or rejected state can be reset to draft.'))
            contract.write({
                'approval_state': 'draft',
                'submitted_by': False,
                'submitted_date': False,
            })
            contract.message_post(
                body=_('The contract has been reset to draft.'),
                subtype_xmlid='mail.mt_note',
            )
        return True

    def action_employee_confirm(self):
        """Nhân viên xác nhận đã đọc và đồng ý hợp đồng."""
        self.ensure_one()
        is_admin = self.env.user.has_group('hr_contract.group_hr_contract_manager') or self.env.user.has_group('base.group_erp_manager')
        if self.employee_id.user_id != self.env.user and not is_admin:
            raise UserError(_('Only the specific employee or an HR Contract Manager can confirm this contract.'))
        if self.approval_state != 'approved':
            raise UserError(_('Contract has not been approved.'))
        self.write({
            'employee_confirmed': True,
            'employee_confirmed_date': fields.Datetime.now(),
        })
        self.message_post(
            body=_('Employee %s has confirmed the contract at %s.') % (
                self.employee_id.name,
                fields.Datetime.now().strftime('%d/%m/%Y %H:%M'),
            ),
            subtype_xmlid='mail.mt_note',
        )
        return True

    def action_renew(self):
        """Gia hạn hợp đồng: tạo bản sao với ngày bắt đầu mới."""
        self.ensure_one()
        new_date_start = self.date_end + relativedelta(days=1) if self.date_end else date.today()
        new_contract = self.copy({
            'date_start': new_date_start,
            'date_end': False,
            'approval_state': 'draft',
            'state': 'draft',
            'employee_confirmed': False,
            'employee_confirmed_date': False,
            'submitted_by': False,
            'submitted_date': False,
            'approved_by': False,
            'approved_date': False,
            'rejection_reason': False,
        })
        new_contract.message_post(
            body=_('The contract has been renewed from contract %s.') % self.name,
            subtype_xmlid='mail.mt_note',
        )
        return {
            'type': 'ir.actions.act_window',
            'name': _('Renewed Contract'),
            'res_model': 'hr.contract',
            'res_id': new_contract.id,
            'view_mode': 'form',
            'target': 'current',
        }

    def action_terminate(self):
        """Chấm dứt hợp đồng: đặt về trạng thái close và cập nhật nhân viên."""
        for contract in self:
            contract.write({
                'state': 'close',
                'date_end': contract.date_end or date.today(),
            })
            contract.message_post(
                body=_('The contract has been terminated by %s on %s.') % (
                    self.env.user.name,
                    date.today().strftime('%d/%m/%Y'),
                ),
                subtype_xmlid='mail.mt_note',
            )
            # Cập nhật trạng thái nhân viên nếu có
            if hasattr(contract.employee_id, 'employee_status'):
                contract.employee_id.write({'employee_status': 'resigned'})
        return True
        
    # CRON JOB
    @api.model
    def _cron_check_contract_expiry(self):
        """Cron hàng ngày: tái tính cảnh báo hết hạn và gửi thông báo."""
        contracts = self.search([
            ('state', '=', 'open'),
            ('date_end', '!=', False),
        ])
        contracts._compute_days_to_expiry()

        # Gửi thông báo cho các hợp đồng sắp hết hạn 30 ngày
        expiring_soon = contracts.filtered(
            lambda c: c.expiry_alert_level in ('danger', 'warning')
                      and c.date_end
        )
        for contract in expiring_soon:
            followers = contract.message_follower_ids.mapped('partner_id')
            if followers:
                contract.message_post(
                    body=_(
                        'Warning: The contract of employee <b>%s</b> will expire on <b>%s</b> '
                        '(<b>%s</b> days left). Please consider renewing or terminating.'
                    ) % (
                        contract.employee_id.name,
                        contract.date_end.strftime('%d/%m/%Y'),
                        contract.days_to_expiry,
                    ),
                    partner_ids=followers.ids,
                    subtype_xmlid='mail.mt_comment',
                )

    # SMART BUTTONS
    def action_view_allowances(self):
        """Mở bảng phụ cấp của hợp đồng."""
        self.ensure_one()
        return {
            'name': _('Allowances - %s') % self.name,
            'type': 'ir.actions.act_window',
            'res_model': 'hr.contract.allowance',
            'view_mode': 'list,form',
            'domain': [('contract_id', '=', self.id)],
            'context': {'default_contract_id': self.id},
        }
