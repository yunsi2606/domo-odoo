# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from datetime import date, datetime, timedelta


class HrEmployee(models.Model):
    """
    Extension of hr.employee for appraisal functionality
    """
    _inherit = 'hr.employee'

    # Appraisal Fields
    appraisal_ids = fields.One2many(
        'hr.appraisal',
        'employee_id',
        string='Appraisals'
    )
    appraisal_count = fields.Integer(
        string='Appraisal Count',
        compute='_compute_appraisal_count'
    )
    last_appraisal_id = fields.Many2one(
        'hr.appraisal',
        string='Last Appraisal',
        compute='_compute_last_appraisal',
        store=True
    )
    last_appraisal_date = fields.Date(
        string='Last Appraisal Date',
        compute='_compute_last_appraisal',
        store=True
    )
    last_appraisal_rating = fields.Selection([
        ('1', 'Needs Improvement'),
        ('2', 'Below Expectations'),
        ('3', 'Meets Expectations'),
        ('4', 'Exceeds Expectations'),
        ('5', 'Outstanding'),
    ], string='Last Rating', compute='_compute_last_appraisal', store=True)
    
    next_appraisal_date = fields.Date(
        string='Next Appraisal Date',
        compute='_compute_next_appraisal'
    )
    
    pending_appraisal_count = fields.Integer(
        string='Pending Appraisals',
        compute='_compute_pending_appraisals'
    )
    
    # Appraisal Settings per Employee
    appraisal_frequency = fields.Integer(
        string='Appraisal Frequency (days)',
        default=365,
        help='Days between appraisals'
    )
    
    def _compute_appraisal_count(self):
        for employee in self:
            employee.appraisal_count = len(employee.appraisal_ids)
    
    @api.depends('appraisal_ids', 'appraisal_ids.state', 'appraisal_ids.date_close', 'appraisal_ids.final_rating')
    def _compute_last_appraisal(self):
        for employee in self:
            done_appraisals = employee.appraisal_ids.filtered(
                lambda a: a.state == 'done'
            ).sorted(key=lambda a: a.date_close, reverse=True)
            
            if done_appraisals:
                last = done_appraisals[0]
                employee.last_appraisal_id = last
                employee.last_appraisal_date = last.date_close
                employee.last_appraisal_rating = last.final_rating
            else:
                employee.last_appraisal_id = False
                employee.last_appraisal_date = False
                employee.last_appraisal_rating = False
    
    def _compute_next_appraisal(self):
        for employee in self:
            if employee.last_appraisal_date:
                employee.next_appraisal_date = employee.last_appraisal_date + timedelta(
                    days=employee.appraisal_frequency
                )
            else:
                # If no previous appraisal, suggest one month from now
                employee.next_appraisal_date = date.today() + timedelta(days=30)
    
    def _compute_pending_appraisals(self):
        for employee in self:
            employee.pending_appraisal_count = self.env['hr.appraisal'].search_count([
                ('employee_id', '=', employee.id),
                ('state', 'not in', ['done', 'cancel']),
            ])
    
    def action_view_appraisals(self):
        """View all appraisals for this employee"""
        self.ensure_one()
        return {
            'name': _('Appraisals for %s', self.name),
            'type': 'ir.actions.act_window',
            'res_model': 'hr.appraisal',
            'view_mode': 'list,form,calendar',
            'domain': [('employee_id', '=', self.id)],
            'context': {'default_employee_id': self.id},
        }
    
    def action_create_appraisal(self):
        """Create a new appraisal for this employee"""
        self.ensure_one()
        return {
            'name': _('New Appraisal'),
            'type': 'ir.actions.act_window',
            'res_model': 'hr.appraisal',
            'view_mode': 'form',
            'target': 'current',
            'context': {
                'default_employee_id': self.id,
                'default_manager_id': self.parent_id.id if self.parent_id else False,
            },
        }


class HrEmployeePublic(models.Model):
    """
    Extension of public employee model
    """
    _inherit = 'hr.employee.public'

    appraisal_count = fields.Integer(
        string='Appraisal Count',
        related='employee_id.appraisal_count'
    )
    last_appraisal_date = fields.Date(
        string='Last Appraisal Date',
        related='employee_id.last_appraisal_date'
    )
