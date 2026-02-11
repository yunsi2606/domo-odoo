# -*- coding: utf-8 -*-
from odoo import api, fields, models, _


class ResCompany(models.Model):
    """
    Extension of res.company for planning settings
    """
    _inherit = 'res.company'

    # === Planning Settings ===
    planning_generation_interval = fields.Selection([
        ('week', 'Weekly'),
        ('month', 'Monthly'),
    ], string='Planning Generation Interval', default='week')
    
    planning_allow_self_unassign = fields.Boolean(
        string='Allow Self Unassign',
        default=True,
        help='Allow employees to unassign themselves from shifts'
    )
    
    planning_allow_open_shift = fields.Boolean(
        string='Allow Open Shifts',
        default=True,
        help='Allow shifts without assigned employees (open shifts)'
    )
    
    planning_send_notification = fields.Boolean(
        string='Send Notifications',
        default=True,
        help='Automatically send email notifications when shifts are published'
    )
    
    planning_default_start_time = fields.Float(
        string='Default Start Time',
        default=8.0,
        help='Default start time for new shifts (e.g., 8.0 = 8:00 AM)'
    )
    
    planning_default_duration = fields.Float(
        string='Default Shift Duration',
        default=8.0,
        help='Default duration in hours for new shifts'
    )
    
    planning_max_hours_per_week = fields.Float(
        string='Max Hours Per Week',
        default=40.0,
        help='Maximum hours an employee can be scheduled per week'
    )
    
    planning_warning_threshold = fields.Float(
        string='Warning Threshold (%)',
        default=80.0,
        help='Show warning when employee utilization exceeds this percentage'
    )
