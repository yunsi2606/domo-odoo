# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError
from datetime import datetime, timedelta


class RecruitmentRequest(models.Model):
    """
    Yêu cầu tuyển dụng - Quản lý chi nhánh/trưởng bộ phận tạo yêu cầu tuyển dụng
    với đầy đủ thông tin: vị trí, số lượng, mô tả công việc, yêu cầu kỹ năng, ngân sách lương.
    Yêu cầu được gửi đến cấp quản lý cao hơn để phê duyệt.
    """
    _name = 'hr.recruitment.request'
    _description = 'Recruitment Request'
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
    active = fields.Boolean(default=True)
    company_id = fields.Many2one(
        'res.company',
        string='Company',
        required=True,
        default=lambda self: self.env.company,
    )

    # Request Information
    job_id = fields.Many2one(
        'hr.job',
        string='Job Position',
        required=True,
        tracking=True,
        help='Vị trí cần tuyển dụng',
    )
    department_id = fields.Many2one(
        'hr.department',
        string='Department',
        required=True,
        tracking=True,
        help='Phòng ban/bộ phận yêu cầu tuyển dụng',
    )
    number_of_positions = fields.Integer(
        string='Number of Positions',
        required=True,
        default=1,
        tracking=True,
        help='Số lượng nhân sự cần tuyển',
    )
    job_description = fields.Html(
        string='Job Description',
        help='Mô tả công việc chi tiết',
    )
    skill_requirements = fields.Html(
        string='Skill Requirements',
        help='Yêu cầu kỹ năng cho vị trí',
    )
    experience_requirements = fields.Text(
        string='Experience Requirements',
        help='Yêu cầu kinh nghiệm',
    )
    education_requirements = fields.Text(
        string='Education Requirements',
        help='Yêu cầu trình độ học vấn',
    )

    # Budget
    salary_min = fields.Monetary(
        string='Minimum Salary',
        currency_field='currency_id',
        tracking=True,
        help='Ngân sách lương tối thiểu',
    )
    salary_max = fields.Monetary(
        string='Maximum Salary',
        currency_field='currency_id',
        tracking=True,
        help='Ngân sách lương tối đa',
    )
    currency_id = fields.Many2one(
        'res.currency',
        string='Currency',
        default=lambda self: self.env.company.currency_id,
    )

    # Timeline
    date_expected = fields.Date(
        string='Expected Start Date',
        tracking=True,
        help='Ngày dự kiến nhân sự bắt đầu làm việc',
    )
    date_deadline = fields.Date(
        string='Recruitment Deadline',
        tracking=True,
        help='Hạn chót hoàn thành tuyển dụng',
    )

    # Requestor & Approver
    requested_by = fields.Many2one(
        'res.users',
        string='Requested By',
        default=lambda self: self.env.user,
        required=True,
        tracking=True,
        help='Người tạo yêu cầu (quản lý chi nhánh/trưởng bộ phận)',
    )
    approved_by = fields.Many2one(
        'res.users',
        string='Approved By',
        tracking=True,
        readonly=True,
        help='Cấp quản lý phê duyệt yêu cầu',
    )
    approval_date = fields.Datetime(
        string='Approval Date',
        readonly=True,
    )
    rejection_reason = fields.Text(
        string='Rejection Reason',
        tracking=True,
    )

    # Priority & Urgency
    priority = fields.Selection([
        ('0', 'Normal'),
        ('1', 'Low'),
        ('2', 'High'),
        ('3', 'Urgent'),
    ], string='Priority', default='0', tracking=True)

    reason = fields.Selection([
        ('new_position', 'New Position'),
        ('replacement', 'Replacement'),
        ('expansion', 'Team Expansion'),
        ('seasonal', 'Seasonal'),
        ('project', 'Project-based'),
    ], string='Reason for Hiring', required=True, default='new_position', tracking=True)

    employment_type = fields.Selection([
        ('full_time', 'Full-time'),
        ('part_time', 'Part-time'),
        ('contract', 'Contract'),
        ('intern', 'Internship'),
        ('temporary', 'Temporary'),
    ], string='Employment Type', required=True, default='full_time', tracking=True)

    # State Management
    state = fields.Selection([
        ('draft', 'Draft'),
        ('submitted', 'Submitted'),
        ('approved', 'Approved'),
        ('in_progress', 'In Progress'),
        ('filled', 'Filled'),
        ('rejected', 'Rejected'),
        ('cancelled', 'Cancelled'),
    ], string='Status', default='draft', tracking=True, required=True, copy=False)

    # Related Applicants
    applicant_ids = fields.One2many(
        'hr.applicant',
        'recruitment_request_id',
        string='Applicants',
    )
    applicant_count = fields.Integer(
        string='Applicant Count',
        compute='_compute_applicant_count',
    )
    hired_count = fields.Integer(
        string='Hired Count',
        compute='_compute_hired_count',
    )

    # Notes
    notes = fields.Html(string='Internal Notes')

    # Constraints
    @api.constrains('number_of_positions')
    def _check_number_of_positions(self):
        for record in self:
            if record.number_of_positions < 1:
                raise ValidationError(_('Number of positions must be at least 1.'))

    @api.constrains('salary_min', 'salary_max')
    def _check_salary_range(self):
        for record in self:
            if record.salary_min and record.salary_max and record.salary_min > record.salary_max:
                raise ValidationError(_('Minimum salary cannot be greater than maximum salary.'))

    @api.constrains('date_expected', 'date_deadline')
    def _check_dates(self):
        for record in self:
            if record.date_expected and record.date_deadline:
                if record.date_deadline > record.date_expected:
                    raise ValidationError(_(
                        'Recruitment deadline should be before the expected start date.'
                    ))

    # Compute Methods
    def _compute_applicant_count(self):
        for record in self:
            record.applicant_count = len(record.applicant_ids)

    def _compute_hired_count(self):
        for record in self:
            record.hired_count = len(
                record.applicant_ids.filtered(lambda a: a.stage_id.hired_stage)
            )

    # CRUD
    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', _('New')) == _('New'):
                vals['name'] = self.env['ir.sequence'].next_by_code(
                    'hr.recruitment.request') or _('New')
        return super().create(vals_list)

    # Onchange
    @api.onchange('job_id')
    def _onchange_job_id(self):
        if self.job_id:
            self.department_id = self.job_id.department_id

    # Action Methods
    def action_submit(self):
        """Submit the request for approval"""
        for record in self:
            if record.state != 'draft':
                raise UserError(_('Only draft requests can be submitted.'))
            record.write({'state': 'submitted'})
            record._send_notification('submit')
        return True

    def action_approve(self):
        """Approve the recruitment request"""
        for record in self:
            if record.state != 'submitted':
                raise UserError(_('Only submitted requests can be approved.'))
            record.write({
                'state': 'approved',
                'approved_by': self.env.user.id,
                'approval_date': fields.Datetime.now(),
            })
            record._send_notification('approve')
        return True

    def action_reject(self):
        """Reject the recruitment request - opens wizard for reason"""
        self.ensure_one()
        return {
            'name': _('Reject Request'),
            'type': 'ir.actions.act_window',
            'res_model': 'hr.recruitment.request',
            'view_mode': 'form',
            'target': 'new',
            'res_id': self.id,
            'context': {'show_rejection_reason': True},
        }

    def action_reject_confirm(self):
        """Confirm rejection with reason"""
        for record in self:
            if record.state != 'submitted':
                raise UserError(_('Only submitted requests can be rejected.'))
            if not record.rejection_reason:
                raise UserError(_('Please provide a reason for rejection.'))
            record.write({
                'state': 'rejected',
                'approved_by': self.env.user.id,
                'approval_date': fields.Datetime.now(),
            })
            record._send_notification('reject')
        return True

    def action_start_recruitment(self):
        """Start the recruitment process"""
        for record in self:
            if record.state != 'approved':
                raise UserError(_('Only approved requests can start recruitment.'))
            record.write({'state': 'in_progress'})
        return True

    def action_mark_filled(self):
        """Mark the position as filled"""
        for record in self:
            if record.state != 'in_progress':
                raise UserError(_('Only in-progress requests can be marked as filled.'))
            record.write({'state': 'filled'})
        return True

    def action_cancel(self):
        """Cancel the request"""
        self.write({'state': 'cancelled'})
        return True

    def action_reset_to_draft(self):
        """Reset to draft"""
        self.write({
            'state': 'draft',
            'approved_by': False,
            'approval_date': False,
            'rejection_reason': False,
        })
        return True

    def action_view_applicants(self):
        """View applicants for this request"""
        self.ensure_one()
        return {
            'name': _('Applicants'),
            'type': 'ir.actions.act_window',
            'res_model': 'hr.applicant',
            'view_mode': 'list,kanban,form',
            'domain': [('recruitment_request_id', '=', self.id)],
            'context': {
                'default_recruitment_request_id': self.id,
                'default_job_id': self.job_id.id,
                'default_department_id': self.department_id.id,
            },
        }

    # Notifications
    def _send_notification(self, notification_type):
        """Send email notification based on type"""
        self.ensure_one()
        template_ref = {
            'submit': 'hr_recruitment_custom.mail_template_request_submitted',
            'approve': 'hr_recruitment_custom.mail_template_request_approved',
            'reject': 'hr_recruitment_custom.mail_template_request_rejected',
        }
        template_xmlid = template_ref.get(notification_type)
        if template_xmlid:
            template = self.env.ref(template_xmlid, raise_if_not_found=False)
            if template:
                template.send_mail(self.id, force_send=True)
