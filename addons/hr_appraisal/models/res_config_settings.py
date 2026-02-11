# -*- coding: utf-8 -*-
from odoo import api, fields, models, _


class ResConfigSettings(models.TransientModel):
    """
    Configuration settings for appraisal
    """
    _inherit = 'res.config.settings'

    # Appraisal Settings
    appraisal_auto_create = fields.Boolean(
        related='company_id.appraisal_auto_create',
        readonly=False
    )
    appraisal_frequency = fields.Integer(
        related='company_id.appraisal_frequency',
        readonly=False
    )
    appraisal_reminder_days = fields.Integer(
        related='company_id.appraisal_reminder_days',
        readonly=False
    )
    appraisal_default_template_id = fields.Many2one(
        related='company_id.appraisal_default_template_id',
        readonly=False
    )
    appraisal_employee_feedback = fields.Boolean(
        related='company_id.appraisal_employee_feedback',
        readonly=False
    )
    appraisal_skills = fields.Boolean(
        related='company_id.appraisal_skills',
        readonly=False
    )
    appraisal_goals = fields.Boolean(
        related='company_id.appraisal_goals',
        readonly=False
    )
