# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import UserError


class HrApplicant(models.Model):
    """
    Mở rộng model hr.applicant để tích hợp với Yêu cầu tuyển dụng,
    quản lý hồ sơ ứng viên tập trung, sàng lọc và phân loại.
    """
    _inherit = 'hr.applicant'

    # Link to Recruitment Request
    recruitment_request_id = fields.Many2one(
        'hr.recruitment.request',
        string='Recruitment Request',
        tracking=True,
        help='Yêu cầu tuyển dụng liên quan',
    )

    # Source Tracking
    source_channel = fields.Selection([
        ('website', 'Website'),
        ('job_board', 'Job Board (VietnamWorks, TopCV...)'),
        ('social_media', 'Social Media (Facebook, LinkedIn...)'),
        ('referral', 'Employee Referral'),
        ('walk_in', 'Walk-in'),
        ('recruitment_agency', 'Recruitment Agency'),
        ('internal', 'Internal Transfer'),
        ('other', 'Other'),
    ], string='Source Channel', tracking=True,
       help='Nguồn tiếp nhận hồ sơ ứng viên')

    # Extended Applicant Info
    date_of_birth = fields.Date(string='Date of Birth')
    gender = fields.Selection([
        ('male', 'Male'),
        ('female', 'Female'),
        ('other', 'Other'),
    ], string='Gender')
    address = fields.Text(string='Address')
    phone_secondary = fields.Char(string='Secondary Phone')

    # Education & Experience
    education_level = fields.Selection([
        ('high_school', 'High School'),
        ('college', 'College'),
        ('bachelor', 'Bachelor'),
        ('master', 'Master'),
        ('phd', 'PhD'),
        ('other', 'Other'),
    ], string='Education Level', tracking=True)
    education_detail = fields.Text(
        string='Education Details',
        help='Chi tiết trường/ngành/năm tốt nghiệp',
    )
    years_of_experience = fields.Float(
        string='Years of Experience',
        help='Số năm kinh nghiệm',
    )
    experience_detail = fields.Html(
        string='Experience Details',
        help='Chi tiết kinh nghiệm làm việc',
    )

    # Skills
    skill_tags = fields.Text(
        string='Skills',
        help='Danh sách kỹ năng (mỗi kỹ năng cách nhau bằng dấu phẩy)',
    )

    # Documents
    cv_attachment_ids = fields.Many2many(
        'ir.attachment',
        'applicant_cv_attachment_rel',
        'applicant_id',
        'attachment_id',
        string='CV / Resume',
        help='Tải lên CV/Resume của ứng viên',
    )

    # Interview
    interview_ids = fields.One2many(
        'hr.recruitment.interview',
        'applicant_id',
        string='Interviews',
    )
    interview_count = fields.Integer(
        string='Interview Count',
        compute='_compute_interview_count',
    )

    # Offer Letter
    offer_letter_ids = fields.One2many(
        'hr.offer.letter',
        'applicant_id',
        string='Offer Letters',
    )
    offer_letter_count = fields.Integer(
        string='Offer Letter Count',
        compute='_compute_offer_letter_count',
    )

    # Overall Rating
    overall_interview_score = fields.Float(
        string='Overall Interview Score',
        compute='_compute_overall_interview_score',
        store=True,
        help='Điểm trung bình phỏng vấn tổng hợp',
    )

    # Screening Status
    screening_status = fields.Selection([
        ('new', 'New'),
        ('screened', 'Screened'),
        ('shortlisted', 'Shortlisted'),
        ('interview', 'Interview Scheduled'),
        ('evaluated', 'Evaluated'),
        ('offer', 'Offer Sent'),
        ('hired', 'Hired'),
        ('rejected', 'Rejected'),
    ], string='Screening Status', default='new', tracking=True,
       help='Trạng thái sàng lọc ứng viên')

    screening_notes = fields.Html(
        string='Screening Notes',
        help='Ghi chú sàng lọc hồ sơ ban đầu',
    )

    # Converted Employee
    employee_id = fields.Many2one(
        'hr.employee',
        string='Created Employee',
        readonly=True,
        help='Nhân viên được tạo từ ứng viên này',
    )

    # Compute Methods
    def _compute_interview_count(self):
        for record in self:
            record.interview_count = len(record.interview_ids)

    def _compute_offer_letter_count(self):
        for record in self:
            record.offer_letter_count = len(record.offer_letter_ids)

    @api.depends('interview_ids', 'interview_ids.evaluation_ids',
                 'interview_ids.evaluation_ids.total_score')
    def _compute_overall_interview_score(self):
        for record in self:
            evaluations = record.interview_ids.mapped('evaluation_ids')
            if evaluations:
                scores = evaluations.mapped('total_score')
                record.overall_interview_score = sum(scores) / len(scores) if scores else 0.0
            else:
                record.overall_interview_score = 0.0

    # Action Methods
    def action_screen(self):
        """Mark as screened"""
        self.write({'screening_status': 'screened'})
        return True

    def action_shortlist(self):
        """Shortlist the applicant"""
        self.write({'screening_status': 'shortlisted'})
        return True

    def action_reject_applicant(self):
        """Reject the applicant"""
        self.write({'screening_status': 'rejected'})
        return True

    def action_view_interviews(self):
        """View interviews for this applicant"""
        self.ensure_one()
        return {
            'name': _('Interviews'),
            'type': 'ir.actions.act_window',
            'res_model': 'hr.recruitment.interview',
            'view_mode': 'list,form',
            'domain': [('applicant_id', '=', self.id)],
            'context': {
                'default_applicant_id': self.id,
                'default_job_id': self.job_id.id,
            },
        }

    def action_schedule_interview(self):
        """Quick action to schedule an interview"""
        self.ensure_one()
        self.write({'screening_status': 'interview'})
        return {
            'name': _('Schedule Interview'),
            'type': 'ir.actions.act_window',
            'res_model': 'hr.recruitment.interview',
            'view_mode': 'form',
            'target': 'current',
            'context': {
                'default_applicant_id': self.id,
                'default_job_id': self.job_id.id,
                'default_department_id': self.department_id.id,
            },
        }

    def action_view_offer_letters(self):
        """View offer letters for this applicant"""
        self.ensure_one()
        return {
            'name': _('Offer Letters'),
            'type': 'ir.actions.act_window',
            'res_model': 'hr.offer.letter',
            'view_mode': 'list,form',
            'domain': [('applicant_id', '=', self.id)],
            'context': {
                'default_applicant_id': self.id,
            },
        }

    def action_create_offer(self):
        """Create offer letter for this applicant"""
        self.ensure_one()
        self.write({'screening_status': 'offer'})
        return {
            'name': _('Create Offer Letter'),
            'type': 'ir.actions.act_window',
            'res_model': 'hr.offer.letter',
            'view_mode': 'form',
            'target': 'current',
            'context': {
                'default_applicant_id': self.id,
                'default_job_id': self.job_id.id,
                'default_department_id': self.department_id.id,
                'default_recruitment_request_id': self.recruitment_request_id.id,
            },
        }

    def action_create_employee(self):
        """Open wizard to create employee from applicant"""
        self.ensure_one()
        return {
            'name': _('Create Employee'),
            'type': 'ir.actions.act_window',
            'res_model': 'hr.recruitment.create.employee.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_applicant_id': self.id,
                'default_job_id': self.job_id.id,
                'default_department_id': self.department_id.id,
            },
        }

    # Override Write để tự động chuyển cột (Stage) trên Kanban
    def write(self, vals):
        res = super(HrApplicant, self).write(vals)
        if 'screening_status' in vals:
            for record in self:
                keyword = False
                if record.screening_status == 'interview':
                    keyword = 'Interview'
                elif record.screening_status == 'offer':
                    keyword = 'Contract'
                elif record.screening_status == 'rejected':
                    keyword = 'Refuse'
                
                if keyword:
                    # Tìm Stage có chứa từ khóa tương ứng
                    stage = self.env['hr.recruitment.stage'].search([('name', 'ilike', keyword)], limit=1)
                    if stage and record.stage_id.id != stage.id:
                        record.stage_id = stage.id
        return res
