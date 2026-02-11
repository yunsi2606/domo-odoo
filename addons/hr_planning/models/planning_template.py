# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from datetime import timedelta


class PlanningTemplate(models.Model):
    """
    Planning Template - Reusable shift templates with predefined settings
    """
    _name = 'planning.template'
    _description = 'Shift Template'
    _order = 'sequence, name'

    name = fields.Char(
        string='Template Name',
        required=True,
        translate=True
    )
    sequence = fields.Integer(
        string='Sequence',
        default=10
    )
    active = fields.Boolean(
        string='Active',
        default=True
    )
    company_id = fields.Many2one(
        'res.company',
        string='Company',
        default=lambda self: self.env.company
    )
    
    # Role
    role_id = fields.Many2one(
        'planning.role',
        string='Role',
        help='Default role for this shift template'
    )
    
    # Timing
    start_time = fields.Float(
        string='Start Hour',
        required=True,
        default=8.0,
        help='Default start hour (e.g., 8.5 = 8:30 AM)'
    )
    duration = fields.Float(
        string='Duration (Hours)',
        required=True,
        default=8.0
    )
    
    # Computed end time
    end_time = fields.Float(
        string='End Hour',
        compute='_compute_end_time',
        store=True
    )
    
    # Display
    start_time_display = fields.Char(
        string='Start Time',
        compute='_compute_time_display'
    )
    end_time_display = fields.Char(
        string='End Time',
        compute='_compute_time_display'
    )
    
    @api.depends('start_time', 'duration')
    def _compute_end_time(self):
        for template in self:
            template.end_time = template.start_time + template.duration
    
    @api.depends('start_time', 'end_time')
    def _compute_time_display(self):
        """Convert float hours to HH:MM format"""
        for template in self:
            template.start_time_display = self._float_to_time_str(template.start_time)
            template.end_time_display = self._float_to_time_str(template.end_time)
    
    @staticmethod
    def _float_to_time_str(float_time):
        """Convert float hours to HH:MM string"""
        hours = int(float_time)
        minutes = int((float_time - hours) * 60)
        return f"{hours:02d}:{minutes:02d}"
    
    @staticmethod
    def _time_str_to_float(time_str):
        """Convert HH:MM string to float hours"""
        hours, minutes = map(int, time_str.split(':'))
        return hours + minutes / 60.0
    
    def name_get(self):
        result = []
        for template in self:
            name = f"{template.name} ({template.start_time_display} - {template.end_time_display})"
            if template.role_id:
                name = f"{name} - {template.role_id.name}"
            result.append((template.id, name))
        return result
    
    def action_create_slot(self):
        """Create a new slot from this template"""
        self.ensure_one()
        return {
            'name': _('Create Shift'),
            'type': 'ir.actions.act_window',
            'res_model': 'planning.slot',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_template_id': self.id,
                'default_role_id': self.role_id.id,
            },
        }
