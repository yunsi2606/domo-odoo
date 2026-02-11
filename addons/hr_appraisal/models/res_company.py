# -*- coding: utf-8 -*-
from odoo import api, fields, models, _


class ResCompany(models.Model):
    """
    Company settings for appraisal
    """
    _inherit = 'res.company'

    # Appraisal Settings
    appraisal_auto_create = fields.Boolean(
        string='Auto Create Appraisals',
        default=False,
        help='Automatically create periodic appraisals'
    )
    appraisal_frequency = fields.Integer(
        string='Appraisal Frequency (days)',
        default=365,
        help='Default days between appraisals'
    )
    appraisal_reminder_days = fields.Integer(
        string='Reminder Days Before Deadline',
        default=7,
        help='Send reminder this many days before deadline'
    )
    appraisal_default_template_id = fields.Many2one(
        'hr.appraisal.template',
        string='Default Appraisal Template'
    )
    appraisal_employee_feedback = fields.Boolean(
        string='Employee Self-Assessment',
        default=True,
        help='Enable employee self-assessment'
    )
    appraisal_skills = fields.Boolean(
        string='Skills Assessment',
        default=True,
        help='Enable skills assessment'
    )
    appraisal_goals = fields.Boolean(
        string='Goals Tracking',
        default=True,
        help='Enable goals tracking'
    )
