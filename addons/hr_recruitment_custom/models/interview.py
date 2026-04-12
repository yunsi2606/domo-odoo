# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError
from datetime import datetime, timedelta


class RecruitmentInterview(models.Model):
    """
    Quản lý lịch phỏng vấn - lên lịch, gửi thư mời tự động cho
    ứng viên và người phỏng vấn. Chấm điểm và đánh giá sau phỏng vấn.
    """
    _name = 'hr.recruitment.interview'
    _description = 'Recruitment Interview'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'interview_date desc, id desc'
    _rec_name = 'name'

    # Identification
    name = fields.Char(
        string='Interview Reference',
        compute='_compute_name',
        store=True,
    )

    # Applicant & Job
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
    job_id = fields.Many2one(
        'hr.job',
        string='Job Position',
        related='applicant_id.job_id',
        store=True,
    )
    department_id = fields.Many2one(
        'hr.department',
        string='Department',
        related='applicant_id.department_id',
        store=True,
    )

    # Interview Schedule
    interview_date = fields.Datetime(
        string='Interview Date & Time',
        required=True,
        tracking=True,
        help='Ngày giờ phỏng vấn',
    )
    interview_duration = fields.Float(
        string='Duration (hours)',
        default=1.0,
        help='Thời lượng phỏng vấn dự kiến (giờ)',
    )
    interview_end_date = fields.Datetime(
        string='End Time',
        compute='_compute_end_date',
        store=True,
    )
    location = fields.Char(
        string='Location',
        help='Địa điểm phỏng vấn (phòng, tầng, địa chỉ)',
    )
    interview_mode = fields.Selection([
        ('in_person', 'In Person'),
        ('phone', 'Phone'),
        ('video', 'Video Call'),
    ], string='Interview Mode', default='in_person', required=True, tracking=True)
    meeting_link = fields.Char(
        string='Meeting Link',
        help='Link họp trực tuyến (nếu phỏng vấn online)',
    )

    # Interview Round
    interview_round = fields.Selection([
        ('1', 'Round 1 - Screening'),
        ('2', 'Round 2 - Technical'),
        ('3', 'Round 3 - Manager'),
        ('4', 'Round 4 - Final'),
    ], string='Interview Round', default='1', required=True, tracking=True)

    # Interviewers
    interviewer_ids = fields.Many2many(
        'hr.employee',
        'interview_interviewer_rel',
        'interview_id',
        'employee_id',
        string='Interviewers',
        required=True,
        help='Danh sách người phỏng vấn',
    )
    responsible_id = fields.Many2one(
        'res.users',
        string='Responsible',
        default=lambda self: self.env.user,
        tracking=True,
    )

    # State
    state = fields.Selection([
        ('draft', 'Draft'),
        ('scheduled', 'Scheduled'),
        ('confirmed', 'Confirmed'),
        ('in_progress', 'In Progress'),
        ('done', 'Completed'),
        ('cancelled', 'Cancelled'),
        ('no_show', 'No Show'),
    ], string='Status', default='draft', tracking=True, required=True, copy=False)

    # Evaluation
    evaluation_ids = fields.One2many(
        'hr.recruitment.interview.evaluation',
        'interview_id',
        string='Evaluations',
    )
    average_score = fields.Float(
        string='Average Score',
        compute='_compute_average_score',
        store=True,
        help='Điểm trung bình từ tất cả người phỏng vấn',
    )
    interview_result = fields.Selection([
        ('pass', 'Pass'),
        ('fail', 'Fail'),
        ('hold', 'On Hold'),
    ], string='Result', tracking=True)

    # Calendar Event
    calendar_event_id = fields.Many2one(
        'calendar.event',
        string='Calendar Event',
        readonly=True,
    )

    # === Notes ===
    notes = fields.Html(string='Notes')
    candidate_notification_sent = fields.Boolean(
        string='Candidate Notified',
        default=False,
    )
    interviewer_notification_sent = fields.Boolean(
        string='Interviewers Notified',
        default=False,
    )

    # Constraints
    @api.constrains('interview_date')
    def _check_interview_date(self):
        for record in self:
            if record.interview_date and record.interview_date < fields.Datetime.now():
                raise ValidationError(_('Interview date cannot be in the past.'))

    # CRUD Overrides
    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)
        # Tự động cập nhật hồ sơ ứng viên sang 'Phỏng vấn' khi có lịch mới
        for record in records:
            if record.applicant_id and record.applicant_id.screening_status in ['new', 'screened', 'shortlisted']:
                record.applicant_id.write({'screening_status': 'interview'})
        return records

    # Compute Methods
    @api.depends('applicant_id', 'interview_round', 'interview_date')
    def _compute_name(self):
        round_labels = {
            '1': 'Screening',
            '2': 'Technical',
            '3': 'Manager',
            '4': 'Final',
        }
        for record in self:
            applicant_name = record.applicant_id.partner_name or 'N/A'
            round_label = round_labels.get(record.interview_round, '')
            date_str = ''
            if record.interview_date:
                date_str = record.interview_date.strftime('%d/%m/%Y')
            record.name = f"[{round_label}] {applicant_name} - {date_str}"

    @api.depends('interview_date', 'interview_duration')
    def _compute_end_date(self):
        for record in self:
            if record.interview_date and record.interview_duration:
                record.interview_end_date = record.interview_date + timedelta(
                    hours=record.interview_duration
                )
            else:
                record.interview_end_date = False

    @api.depends('evaluation_ids', 'evaluation_ids.total_score')
    def _compute_average_score(self):
        for record in self:
            evaluations = record.evaluation_ids
            if evaluations:
                scores = evaluations.mapped('total_score')
                record.average_score = sum(scores) / len(scores) if scores else 0.0
            else:
                record.average_score = 0.0

    def action_schedule(self):
        """Schedule the interview and send notifications"""
        for record in self:
            if record.state != 'draft':
                raise UserError(_('Only draft interviews can be scheduled.'))
            record.write({'state': 'scheduled'})
            record._create_calendar_event()
            # Auto-send email to candidate
            record.action_send_candidate_notification()
            # Auto-send email to all interviewers
            record.action_send_interviewer_notification()
            # Tự động cập nhật trạng thái ứng viên
            if record.applicant_id.screening_status != 'evaluated':
                record.applicant_id.write({'screening_status': 'interview'})
        return True

    def action_confirm(self):
        """Confirm the interview"""
        for record in self:
            if record.state != 'scheduled':
                raise UserError(_('Only scheduled interviews can be confirmed.'))
            record.write({'state': 'confirmed'})
        return True

    def action_start(self):
        """Start the interview"""
        self.write({'state': 'in_progress'})
        return True

    def action_complete(self):
        """Complete the interview"""
        for record in self:
            if record.state not in ('confirmed', 'in_progress'):
                raise UserError(_('Interview must be confirmed or in progress to complete.'))
            record.write({'state': 'done'})
            # Update applicant screening status
            record.applicant_id.write({'screening_status': 'evaluated'})
            # Auto-create Offer Letter when Round 4 passes
            if record.interview_round == '4' and record.interview_result == 'pass':
                existing_offer = record.applicant_id.offer_letter_ids.filtered(
                    lambda o: o.state not in ('cancelled', 'rejected')
                )
                if not existing_offer:
                    record.env['hr.offer.letter'].create({
                        'applicant_id': record.applicant_id.id,
                        'job_id': record.applicant_id.job_id.id,
                        'department_id': record.applicant_id.department_id.id,
                        'recruitment_request_id': record.applicant_id.recruitment_request_id.id,
                        'offered_salary': 1,  # Placeholder – HR cần điền lại
                        'expiry_date': fields.Date.today() + timedelta(days=7),
                        'start_date': fields.Date.today() + timedelta(days=14),
                        'responsible_id': record.responsible_id.id,
                    })
                    record.applicant_id.write({'screening_status': 'offer'})
                    record.message_post(
                        body=_('✅ Round 4 passed. Draft Offer Letter has been automatically created.')
                    )
        return True

    def action_cancel(self):
        """Cancel the interview"""
        for record in self:
            record.write({'state': 'cancelled'})
            # Cancel calendar event
            if record.calendar_event_id:
                record.calendar_event_id.unlink()
            record._send_interview_notification('cancelled')
        return True

    def action_no_show(self):
        """Mark as no show"""
        self.write({'state': 'no_show'})
        return True

    def action_reset_to_draft(self):
        """Reset to draft"""
        self.write({'state': 'draft'})
        return True

    def action_add_evaluation(self):
        """Open evaluation form"""
        self.ensure_one()
        return {
            'name': _('Add Interview Evaluation'),
            'type': 'ir.actions.act_window',
            'res_model': 'hr.recruitment.interview.evaluation',
            'view_mode': 'form',
            'target': 'current',
            'context': {
                'default_interview_id': self.id,
                'default_applicant_id': self.applicant_id.id,
            },
        }

    def action_send_candidate_notification(self):
        """Send interview invitation to candidate"""
        self.ensure_one()
        template = self.env.ref(
            'hr_recruitment_custom.mail_template_interview_invitation',
            raise_if_not_found=False,
        )
        if template:
            template.send_mail(self.id, force_send=True)
            self.write({'candidate_notification_sent': True})
        return True

    def action_send_interviewer_notification(self):
        """Send interview schedule to interviewers"""
        self.ensure_one()
        template = self.env.ref(
            'hr_recruitment_custom.mail_template_interview_interviewer',
            raise_if_not_found=False,
        )
        if not template:
            return True
        for interviewer in self.interviewer_ids:
            email = (interviewer.work_email
                     or (interviewer.user_id and interviewer.user_id.email)
                     or '')
            if not email:
                continue
            template.with_context(interviewer=interviewer).send_mail(
                self.id,
                force_send=True,
                email_values={'email_to': email},
            )
        self.write({'interviewer_notification_sent': True})
        return True

    # Calendar Event
    def _create_calendar_event(self):
        """Create a calendar event for the interview"""
        self.ensure_one()
        if self.calendar_event_id:
            return

        partner_ids = []
        for interviewer in self.interviewer_ids:
            if interviewer.user_id and interviewer.user_id.partner_id:
                partner_ids.append(interviewer.user_id.partner_id.id)

        event_vals = {
            'name': f'Interview: {self.applicant_id.partner_name} - {self.job_id.name}',
            'start': self.interview_date,
            'stop': self.interview_end_date or self.interview_date + timedelta(hours=1),
            'partner_ids': [(6, 0, partner_ids)],
            'description': self._get_calendar_description(),
            'location': self.location or '',
        }
        event = self.env['calendar.event'].create(event_vals)
        self.write({'calendar_event_id': event.id})

    def _get_calendar_description(self):
        """Generate calendar event description"""
        desc = f"""
Interview Details:
- Applicant: {self.applicant_id.partner_name}
- Position: {self.job_id.name}
- Round: {dict(self._fields['interview_round'].selection).get(self.interview_round)}
- Mode: {dict(self._fields['interview_mode'].selection).get(self.interview_mode)}
"""
        if self.meeting_link:
            desc += f"- Meeting Link: {self.meeting_link}\n"
        if self.location:
            desc += f"- Location: {self.location}\n"
        return desc

    # Notifications
    def _send_interview_notification(self, notification_type):
        """Send notifications for interview"""
        self.ensure_one()
        template_map = {
            'scheduled': 'hr_recruitment_custom.mail_template_interview_invitation',
            'cancelled': 'hr_recruitment_custom.mail_template_interview_cancelled',
        }
        template_xmlid = template_map.get(notification_type)
        if template_xmlid:
            template = self.env.ref(template_xmlid, raise_if_not_found=False)
            if template:
                template.send_mail(self.id, force_send=True)
