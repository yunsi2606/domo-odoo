# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class HrAppraisalGoal(models.Model):
    """
    HR Appraisal Goal - Objectives and goals for employee
    """
    _name = 'hr.appraisal.goal'
    _description = 'Appraisal Goal'
    _order = 'priority desc, deadline, id'

    name = fields.Char(
        string='Goal',
        required=True
    )
    description = fields.Html(
        string='Description',
        help='Detailed description of the goal'
    )
    appraisal_id = fields.Many2one(
        'hr.appraisal',
        string='Appraisal',
        required=True,
        ondelete='cascade'
    )
    employee_id = fields.Many2one(
        'hr.employee',
        string='Employee',
        related='appraisal_id.employee_id',
        store=True
    )
    
    # Goal Details
    category = fields.Selection([
        ('performance', 'Performance'),
        ('development', 'Development'),
        ('project', 'Project'),
        ('learning', 'Learning'),
        ('other', 'Other'),
    ], string='Category', default='performance', required=True)
    
    priority = fields.Selection([
        ('0', 'Low'),
        ('1', 'Medium'),
        ('2', 'High'),
        ('3', 'Critical'),
    ], string='Priority', default='1')
    
    deadline = fields.Date(
        string='Deadline',
        required=True
    )
    
    # Progress Tracking
    progress = fields.Float(
        string='Progress (%)',
        default=0.0,
        tracking=True
    )
    state = fields.Selection([
        ('not_started', 'Not Started'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ], string='Status', default='not_started', tracking=True)
    
    # Measurement
    metric_type = fields.Selection([
        ('percentage', 'Percentage'),
        ('number', 'Numeric Value'),
        ('boolean', 'Yes/No'),
        ('milestone', 'Milestone'),
    ], string='Metric Type', default='percentage')
    
    target_value = fields.Float(
        string='Target Value',
        help='Target value to achieve'
    )
    current_value = fields.Float(
        string='Current Value',
        help='Current achieved value'
    )
    
    # Notes
    manager_note = fields.Text(
        string='Manager Notes',
        help='Notes from manager about this goal'
    )
    employee_note = fields.Text(
        string='Employee Notes',
        help='Notes from employee about this goal'
    )
    
    weight = fields.Float(
        string='Weight (%)',
        default=100.0,
        help='Weight of this goal in overall calculation'
    )
    
    # Constraints
    @api.constrains('progress')
    def _check_progress(self):
        for goal in self:
            if goal.progress < 0 or goal.progress > 100:
                raise ValidationError(_('Progress must be between 0 and 100.'))
    
    @api.constrains('weight')
    def _check_weight(self):
        for goal in self:
            if goal.weight < 0 or goal.weight > 100:
                raise ValidationError(_('Weight must be between 0 and 100.'))
    
    # Onchange
    @api.onchange('progress')
    def _onchange_progress(self):
        if self.progress >= 100:
            self.state = 'completed'
        elif self.progress > 0:
            self.state = 'in_progress'
        else:
            self.state = 'not_started'
    
    @api.onchange('current_value', 'target_value')
    def _onchange_values(self):
        if self.metric_type in ['percentage', 'number'] and self.target_value:
            self.progress = min(100, (self.current_value / self.target_value) * 100)
    
    # Actions
    def action_mark_complete(self):
        """Mark goal as completed"""
        self.write({
            'state': 'completed',
            'progress': 100.0,
        })
        return True
    
    def action_cancel(self):
        """Cancel the goal"""
        self.write({'state': 'cancelled'})
        return True
    
    def action_reset(self):
        """Reset goal to not started"""
        self.write({
            'state': 'not_started',
            'progress': 0.0,
            'current_value': 0.0,
        })
        return True
