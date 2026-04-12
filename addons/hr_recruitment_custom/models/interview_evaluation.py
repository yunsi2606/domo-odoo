# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class InterviewEvaluation(models.Model):
    """
    Đánh giá phỏng vấn - Người phỏng vấn nhập điểm số và nhận xét
    đánh giá trực tiếp trên hồ sơ ứng viên sau mỗi buổi phỏng vấn.
    """
    _name = 'hr.recruitment.interview.evaluation'
    _description = 'Interview Evaluation'
    _order = 'create_date desc, id desc'
    _rec_name = 'display_name'

    # Link to Interview
    interview_id = fields.Many2one(
        'hr.recruitment.interview',
        string='Interview',
        required=True,
        ondelete='cascade',
    )
    applicant_id = fields.Many2one(
        'hr.applicant',
        string='Applicant',
        related='interview_id.applicant_id',
        store=True,
    )
    interview_round = fields.Selection(
        related='interview_id.interview_round',
        store=True,
        string='Interview Round',
    )

    # Evaluator
    evaluator_id = fields.Many2one(
        'hr.employee',
        string='Evaluator',
        required=True,
        default=lambda self: self.env.user.employee_id,
        help='Người phỏng vấn đánh giá',
    )
    evaluator_user_id = fields.Many2one(
        'res.users',
        string='Evaluator User',
        related='evaluator_id.user_id',
        store=True,
    )

    #Display Name
    display_name = fields.Char(
        string='Name',
        compute='_compute_display_name',
        store=True,
    )

    # Scoring Criteria (1-10)
    score_technical = fields.Integer(
        string='Technical Skills',
        help='Kỹ năng chuyên môn (1-10)',
    )
    score_communication = fields.Integer(
        string='Communication Skills',
        help='Kỹ năng giao tiếp (1-10)',
    )
    score_teamwork = fields.Integer(
        string='Teamwork',
        help='Khả năng làm việc nhóm (1-10)',
    )
    score_problem_solving = fields.Integer(
        string='Problem Solving',
        help='Khả năng giải quyết vấn đề (1-10)',
    )
    score_attitude = fields.Integer(
        string='Attitude & Motivation',
        help='Thái độ và động lực làm việc (1-10)',
    )
    score_experience = fields.Integer(
        string='Experience Relevance',
        help='Mức độ phù hợp kinh nghiệm (1-10)',
    )
    score_culture_fit = fields.Integer(
        string='Culture Fit',
        help='Phù hợp văn hóa doanh nghiệp (1-10)',
    )

    # Total Score
    total_score = fields.Float(
        string='Total Score',
        compute='_compute_total_score',
        store=True,
        help='Điểm tổng trung bình (tự động tính)',
    )

    # Comments
    strengths = fields.Html(
        string='Strengths',
        help='Điểm mạnh của ứng viên',
    )
    weaknesses = fields.Html(
        string='Weaknesses',
        help='Điểm cần cải thiện',
    )
    overall_comment = fields.Html(
        string='Overall Comments',
        help='Nhận xét tổng thể',
    )

    # Recommendation
    recommendation = fields.Selection([
        ('strong_hire', 'Strong Hire'),
        ('hire', 'Hire'),
        ('maybe', 'Maybe'),
        ('no_hire', 'No Hire'),
        ('strong_no_hire', 'Strong No Hire'),
    ], string='Recommendation', required=True, tracking=True,
       help='Khuyến nghị tuyển dụng')

    # Constraints
    @api.constrains('score_technical', 'score_communication', 'score_teamwork',
                    'score_problem_solving', 'score_attitude', 'score_experience',
                    'score_culture_fit')
    def _check_scores(self):
        score_fields = [
            'score_technical', 'score_communication', 'score_teamwork',
            'score_problem_solving', 'score_attitude', 'score_experience',
            'score_culture_fit'
        ]
        for record in self:
            for field_name in score_fields:
                score = getattr(record, field_name)
                if score and (score < 0 or score > 10):
                    raise ValidationError(_(
                        'All scores must be between 0 and 10. '
                        'Please correct the %(field)s field.',
                        field=field_name.replace('score_', '').replace('_', ' ').title()
                    ))

    # Compute Methods
    @api.depends('evaluator_id', 'interview_id')
    def _compute_display_name(self):
        for record in self:
            evaluator_name = record.evaluator_id.name or 'N/A'
            applicant_name = record.applicant_id.partner_name or 'N/A'
            record.display_name = f"{evaluator_name} → {applicant_name}"

    @api.depends('score_technical', 'score_communication', 'score_teamwork',
                 'score_problem_solving', 'score_attitude', 'score_experience',
                 'score_culture_fit')
    def _compute_total_score(self):
        score_fields = [
            'score_technical', 'score_communication', 'score_teamwork',
            'score_problem_solving', 'score_attitude', 'score_experience',
            'score_culture_fit'
        ]
        for record in self:
            scores = []
            for field_name in score_fields:
                val = getattr(record, field_name)
                if val:
                    scores.append(val)
            record.total_score = sum(scores) / len(scores) if scores else 0.0
