# -*- coding: utf-8 -*-
from odoo import api, fields, models, _


class RecruitmentSource(models.Model):
    """
    Nguồn tuyển dụng - Quản lý các kênh tuyển dụng (website, trang việc làm,
    mạng xã hội, giới thiệu nội bộ...)
    """
    _name = 'hr.recruitment.source.channel'
    _description = 'Recruitment Source Channel'
    _order = 'sequence, name'

    name = fields.Char(
        string='Channel Name',
        required=True,
    )
    code = fields.Char(
        string='Code',
        required=True,
    )
    channel_type = fields.Selection([
        ('website', 'Company Website'),
        ('job_board', 'Job Board'),
        ('social_media', 'Social Media'),
        ('referral', 'Employee Referral'),
        ('agency', 'Recruitment Agency'),
        ('campus', 'Campus Recruitment'),
        ('walk_in', 'Walk-in'),
        ('other', 'Other'),
    ], string='Channel Type', required=True, default='other')
    url = fields.Char(string='URL')
    description = fields.Text(string='Description')
    active = fields.Boolean(default=True)
    sequence = fields.Integer(default=10)

    # Statistics
    applicant_count = fields.Integer(
        string='Applicant Count',
        compute='_compute_applicant_count',
    )

    def _compute_applicant_count(self):
        for record in self:
            record.applicant_count = self.env['hr.applicant'].search_count([
                ('source_channel', '=', record.code),
            ])
