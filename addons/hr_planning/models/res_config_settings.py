# -*- coding: utf-8 -*-
from odoo import api, fields, models, _


class ResConfigSettings(models.TransientModel):
    """
    Planning configuration settings in General Settings
    """
    _inherit = 'res.config.settings'

    # === Planning Settings (Company Level) ===
    planning_generation_interval = fields.Selection(
        related='company_id.planning_generation_interval',
        readonly=False
    )
    planning_allow_self_unassign = fields.Boolean(
        related='company_id.planning_allow_self_unassign',
        readonly=False
    )
    planning_allow_open_shift = fields.Boolean(
        related='company_id.planning_allow_open_shift',
        readonly=False
    )
    planning_send_notification = fields.Boolean(
        related='company_id.planning_send_notification',
        readonly=False
    )
    planning_default_start_time = fields.Float(
        related='company_id.planning_default_start_time',
        readonly=False
    )
    planning_default_duration = fields.Float(
        related='company_id.planning_default_duration',
        readonly=False
    )
    planning_max_hours_per_week = fields.Float(
        related='company_id.planning_max_hours_per_week',
        readonly=False
    )
    planning_warning_threshold = fields.Float(
        related='company_id.planning_warning_threshold',
        readonly=False
    )
    
    # === Module Level Settings ===
    module_hr_planning_project = fields.Boolean(
        string='Project Planning Integration',
        help='Enable integration with Project module'
    )
    module_hr_planning_sale = fields.Boolean(
        string='Sales Planning Integration',
        help='Enable integration with Sales module'
    )
