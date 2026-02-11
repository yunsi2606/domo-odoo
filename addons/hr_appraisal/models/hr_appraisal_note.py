# -*- coding: utf-8 -*-
from odoo import api, fields, models, _


class HrAppraisalNote(models.Model):
    """
    HR Appraisal Note - Meeting notes and observations
    """
    _name = 'hr.appraisal.note'
    _description = 'Appraisal Note'
    _order = 'date desc, id desc'

    name = fields.Char(
        string='Subject',
        required=True
    )
    content = fields.Html(
        string='Content',
        required=True
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
    date = fields.Datetime(
        string='Date',
        default=fields.Datetime.now,
        required=True
    )
    author_id = fields.Many2one(
        'res.users',
        string='Author',
        default=lambda self: self.env.user,
        required=True
    )
    note_type = fields.Selection([
        ('meeting', 'Meeting Note'),
        ('observation', 'Observation'),
        ('feedback', 'Feedback'),
        ('action_item', 'Action Item'),
        ('other', 'Other'),
    ], string='Type', default='meeting', required=True)
    
    visibility = fields.Selection([
        ('private', 'Private (Manager Only)'),
        ('shared', 'Shared with Employee'),
    ], string='Visibility', default='shared')
    
    is_action_item = fields.Boolean(
        string='Is Action Item',
        compute='_compute_is_action_item',
        store=True
    )
    action_deadline = fields.Date(
        string='Action Deadline'
    )
    action_status = fields.Selection([
        ('pending', 'Pending'),
        ('in_progress', 'In Progress'),
        ('done', 'Done'),
    ], string='Action Status', default='pending')
    
    @api.depends('note_type')
    def _compute_is_action_item(self):
        for note in self:
            note.is_action_item = note.note_type == 'action_item'
    
    def action_mark_done(self):
        """Mark action item as done"""
        self.write({'action_status': 'done'})
        return True
