# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError


class OfferLetter(models.Model):
    """
    Thư mời nhận việc - Tạo và gửi thư mời theo mẫu chuẩn công ty.
    Theo dõi trạng thái: đã gửi, chấp nhận, từ chối.
    Khi ứng viên chấp nhận → cho phép chuyển đổi thành nhân viên.
    """
    _name = 'hr.offer.letter'
    _description = 'Offer Letter'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'create_date desc, id desc'
    _rec_name = 'name'

    # Identification
    name = fields.Char(
        string='Reference',
        required=True,
        copy=False,
        readonly=True,
        default=lambda self: _('New'),
        tracking=True,
    )

    # Applicant Information
    applicant_id = fields.Many2one(
        'hr.applicant',
        string='Applicant',
        required=True,
        tracking=True,
        ondelete='cascade',
    )
    applicant_name = fields.Char(
        string='Applicant Name',
        related='applicant_id.partner_name',
        store=True,
    )
    applicant_email = fields.Char(
        string='Email',
        related='applicant_id.email_from',
        store=True,
    )
    applicant_phone = fields.Char(
        string='Phone',
        related='applicant_id.partner_phone',
        store=True,
    )

    # Job Details
    job_id = fields.Many2one(
        'hr.job',
        string='Job Position',
        required=True,
        tracking=True,
    )
    department_id = fields.Many2one(
        'hr.department',
        string='Department',
        tracking=True,
    )
    recruitment_request_id = fields.Many2one(
        'hr.recruitment.request',
        string='Recruitment Request',
    )
    company_id = fields.Many2one(
        'res.company',
        string='Company',
        required=True,
        default=lambda self: self.env.company,
    )

    # Offer Details
    offered_salary = fields.Monetary(
        string='Offered Salary',
        currency_field='currency_id',
        required=True,
        tracking=True,
        help='Mức lương đề xuất',
    )
    currency_id = fields.Many2one(
        'res.currency',
        string='Currency',
        default=lambda self: self.env.company.currency_id,
    )
    employment_type = fields.Selection([
        ('full_time', 'Full-time'),
        ('part_time', 'Part-time'),
        ('contract', 'Contract'),
        ('intern', 'Internship'),
        ('temporary', 'Temporary'),
    ], string='Employment Type', default='full_time', required=True, tracking=True)

    probation_period = fields.Integer(
        string='Probation Period (months)',
        default=2,
        help='Thời gian thử việc (tháng)',
    )
    probation_salary_percentage = fields.Float(
        string='Probation Salary (%)',
        default=85.0,
        help='Phần trăm lương trong thời gian thử việc',
    )
    probation_salary = fields.Monetary(
        string='Probation Salary',
        currency_field='currency_id',
        compute='_compute_probation_salary',
        store=True,
    )

    # Dates
    offer_date = fields.Date(
        string='Offer Date',
        default=fields.Date.today,
        required=True,
        tracking=True,
    )
    expiry_date = fields.Date(
        string='Offer Expiry Date',
        required=True,
        tracking=True,
        help='Hạn chót phản hồi thư mời',
    )
    start_date = fields.Date(
        string='Expected Start Date',
        required=True,
        tracking=True,
        help='Ngày bắt đầu làm việc dự kiến',
    )

    # Benefits
    benefits = fields.Html(
        string='Benefits & Perks',
        help='Phúc lợi và quyền lợi',
    )
    working_hours = fields.Char(
        string='Working Hours',
        help='Giờ làm việc',
    )
    work_location = fields.Char(
        string='Work Location',
        help='Địa điểm làm việc',
    )

    # Offer Content
    offer_content = fields.Html(
        string='Offer Letter Content',
        help='Nội dung thư mời nhận việc (theo mẫu chuẩn)',
    )

    # State
    state = fields.Selection([
        ('draft', 'Draft'),
        ('sent', 'Sent'),
        ('accepted', 'Accepted'),
        ('rejected', 'Rejected'),
        ('expired', 'Expired'),
        ('cancelled', 'Cancelled'),
    ], string='Status', default='draft', tracking=True, required=True, copy=False)

    # === Response ===
    response_date = fields.Datetime(
        string='Response Date',
        readonly=True,
        help='Ngày ứng viên phản hồi',
    )
    rejection_reason = fields.Text(
        string='Rejection Reason',
        help='Lý do từ chối (nếu có)',
    )

    # Responsible
    responsible_id = fields.Many2one(
        'res.users',
        string='Responsible',
        default=lambda self: self.env.user,
        tracking=True,
    )

    # Notes
    notes = fields.Html(string='Internal Notes')

    # Employee Created
    employee_id = fields.Many2one(
        'hr.employee',
        string='Created Employee',
        readonly=True,
        help='Nhân viên được tạo từ thư mời này',
    )

    # Constraints
    @api.constrains('offer_date', 'expiry_date')
    def _check_expiry_date(self):
        for record in self:
            if record.expiry_date and record.offer_date:
                if record.expiry_date < record.offer_date:
                    raise ValidationError(_('Expiry date must be after offer date.'))

    @api.constrains('offered_salary')
    def _check_salary(self):
        for record in self:
            if record.offered_salary <= 0:
                raise ValidationError(_('Offered salary must be greater than 0.'))

    # Compute Methods
    @api.depends('offered_salary', 'probation_salary_percentage')
    def _compute_probation_salary(self):
        for record in self:
            record.probation_salary = (
                record.offered_salary * record.probation_salary_percentage / 100
            )

    # CRUD
    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', _('New')) == _('New'):
                vals['name'] = self.env['ir.sequence'].next_by_code(
                    'hr.offer.letter') or _('New')
        records = super().create(vals_list)
        for record in records:
            if not record.offer_content:
                record._generate_offer_content()
            # Tự động cập nhật hồ sơ ứng viên sang 'Offer'
            if record.applicant_id and record.applicant_id.screening_status not in ['hired', 'rejected']:
                record.applicant_id.write({'screening_status': 'offer'})
        return records

    # Generate Offer Content
    def _generate_offer_content(self):
        """Generate standard offer letter content"""
        self.ensure_one()
        content = f"""
<div style="font-family: Arial, sans-serif; padding: 20px;">
    <h2 style="color: #2c3e50; border-bottom: 2px solid #3498db; padding-bottom: 10px;">
        THƯ MỜI NHẬN VIỆC
    </h2>

    <p><strong>Kính gửi:</strong> {self.applicant_name}</p>

    <p>Chúng tôi rất vui mừng thông báo rằng bạn đã được chọn cho vị trí
    <strong>{self.job_id.name}</strong> tại
    <strong>{self.department_id.name or ''}</strong>,
    <strong>{self.company_id.name}</strong>.</p>

    <h3 style="color: #2c3e50;">Chi tiết công việc:</h3>
    <table style="width: 100%; border-collapse: collapse; margin: 10px 0;">
        <tr>
            <td style="padding: 8px; border: 1px solid #ddd; font-weight: bold; width: 30%;">
                Vị trí</td>
            <td style="padding: 8px; border: 1px solid #ddd;">{self.job_id.name}</td>
        </tr>
        <tr>
            <td style="padding: 8px; border: 1px solid #ddd; font-weight: bold;">
                Phòng ban</td>
            <td style="padding: 8px; border: 1px solid #ddd;">
                {self.department_id.name or 'N/A'}</td>
        </tr>
        <tr>
            <td style="padding: 8px; border: 1px solid #ddd; font-weight: bold;">
                Hình thức</td>
            <td style="padding: 8px; border: 1px solid #ddd;">
                {dict(self._fields['employment_type'].selection).get(self.employment_type)}</td>
        </tr>
        <tr>
            <td style="padding: 8px; border: 1px solid #ddd; font-weight: bold;">
                Mức lương chính thức</td>
            <td style="padding: 8px; border: 1px solid #ddd;">
                {self.offered_salary:,.0f} {self.currency_id.symbol}</td>
        </tr>
        <tr>
            <td style="padding: 8px; border: 1px solid #ddd; font-weight: bold;">
                Thời gian thử việc</td>
            <td style="padding: 8px; border: 1px solid #ddd;">
                {self.probation_period} tháng ({self.probation_salary_percentage}% lương)</td>
        </tr>
        <tr>
            <td style="padding: 8px; border: 1px solid #ddd; font-weight: bold;">
                Ngày bắt đầu</td>
            <td style="padding: 8px; border: 1px solid #ddd;">{self.start_date}</td>
        </tr>
    </table>

    <p>Vui lòng phản hồi trước ngày <strong>{self.expiry_date}</strong>.</p>

    <p>Chúng tôi mong đợi sự gia nhập của bạn!</p>

    <p style="margin-top: 30px;">Trân trọng,<br/>
    <strong>Phòng Nhân sự</strong><br/>
    {self.company_id.name}</p>
</div>
"""
        self.write({'offer_content': content})

    # Action Methods
    def action_send_offer(self):
        """Send the offer letter to the candidate"""
        for record in self:
            if record.state != 'draft':
                raise UserError(_('Only draft offers can be sent.'))
            record.write({'state': 'sent'})
            record._send_offer_notification('sent')
            # Update applicant screening status
            record.applicant_id.write({'screening_status': 'offer'})
        return True

    def action_accept(self):
        """Mark offer as accepted"""
        for record in self:
            if record.state != 'sent':
                raise UserError(_('Only sent offers can be accepted.'))
            record.write({
                'state': 'accepted',
                'response_date': fields.Datetime.now(),
            })
            record._send_offer_notification('accepted')
            # Update applicant screening status
            record.applicant_id.write({'screening_status': 'hired'})
        return True

    def action_reject(self):
        """Mark offer as rejected"""
        for record in self:
            if record.state != 'sent':
                raise UserError(_('Only sent offers can be rejected.'))
            record.write({
                'state': 'rejected',
                'response_date': fields.Datetime.now(),
            })
            record._send_offer_notification('rejected')
            record.applicant_id.write({'screening_status': 'rejected'})
        return True

    def action_expire(self):
        """Mark offer as expired"""
        self.write({'state': 'expired'})
        return True

    def action_cancel(self):
        """Cancel the offer"""
        self.write({'state': 'cancelled'})
        return True

    def action_reset_to_draft(self):
        """Reset to draft"""
        self.write({
            'state': 'draft',
            'response_date': False,
            'rejection_reason': False,
        })
        return True

    def action_regenerate_content(self):
        """Regenerate offer letter content"""
        self._generate_offer_content()
        return True

    def action_create_employee(self):
        """Open wizard to create employee from accepted offer"""
        self.ensure_one()
        if self.state != 'accepted':
            raise UserError(_('Employee can only be created from accepted offers.'))
        return {
            'name': _('Create Employee'),
            'type': 'ir.actions.act_window',
            'res_model': 'hr.recruitment.create.employee.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_applicant_id': self.applicant_id.id,
                'default_offer_letter_id': self.id,
                'default_job_id': self.job_id.id,
                'default_department_id': self.department_id.id,
                'default_offered_salary': self.offered_salary,
                'default_start_date': str(self.start_date),
            },
        }

    # Cron: Auto-expire
    @api.model
    def _cron_expire_offers(self):
        """Auto-expire offers past their expiry date"""
        expired_offers = self.search([
            ('state', '=', 'sent'),
            ('expiry_date', '<', fields.Date.today()),
        ])
        expired_offers.write({'state': 'expired'})
        return True

    # Notifications
    def _send_offer_notification(self, notification_type):
        """Send offer-related notification"""
        self.ensure_one()
        template_map = {
            'sent': 'hr_recruitment_custom.mail_template_offer_sent',
            'accepted': 'hr_recruitment_custom.mail_template_offer_accepted',
            'rejected': 'hr_recruitment_custom.mail_template_offer_rejected',
        }
        template_xmlid = template_map.get(notification_type)
        if template_xmlid:
            template = self.env.ref(template_xmlid, raise_if_not_found=False)
            if template:
                template.send_mail(self.id, force_send=True)
