# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import UserError
from datetime import timedelta


class AppraisalRequestWizard(models.TransientModel):
    """
    Wizard to create appraisals for multiple employees
    """
    _name = 'hr.appraisal.request.wizard'
    _description = 'Appraisal Request Wizard'

    # Employee Selection
    employee_ids = fields.Many2many(
        'hr.employee',
        string='Employees',
        required=True,
        help='Select employees to create appraisals for'
    )
    
    # Appraisal Settings
    template_id = fields.Many2one(
        'hr.appraisal.template',
        string='Template',
        help='Template to use for the appraisals'
    )
    date_close = fields.Date(
        string='Deadline',
        required=True,
        default=lambda self: fields.Date.today() + timedelta(days=30)
    )
    appraisal_period_start = fields.Date(
        string='Period Start',
        required=True,
        default=lambda self: fields.Date.today().replace(month=1, day=1)
    )
    appraisal_period_end = fields.Date(
        string='Period End',
        required=True,
        default=lambda self: fields.Date.today().replace(month=12, day=31)
    )
    
    # Options
    send_notification = fields.Boolean(
        string='Send Notification',
        default=True,
        help='Send email notification to employees'
    )
    auto_confirm = fields.Boolean(
        string='Auto Confirm',
        default=False,
        help='Automatically confirm the appraisals'
    )
    
    def action_create_appraisals(self):
        """Create appraisals for selected employees"""
        self.ensure_one()
        
        if not self.employee_ids:
            raise UserError(_('Please select at least one employee.'))
        
        Appraisal = self.env['hr.appraisal']
        created_appraisals = Appraisal
        
        for employee in self.employee_ids:
            # Check if employee already has pending appraisal
            existing = Appraisal.search([
                ('employee_id', '=', employee.id),
                ('state', 'not in', ['done', 'cancel']),
            ], limit=1)
            
            if existing:
                continue  # Skip if already has pending appraisal
            
            appraisal = Appraisal.create({
                'employee_id': employee.id,
                'template_id': self.template_id.id if self.template_id else False,
                'date_close': self.date_close,
                'appraisal_period_start': self.appraisal_period_start,
                'appraisal_period_end': self.appraisal_period_end,
            })
            created_appraisals |= appraisal
            
            if self.auto_confirm:
                appraisal.action_confirm()
            elif self.send_notification:
                appraisal._send_notification('confirm')
        
        if not created_appraisals:
            raise UserError(_('No appraisals were created. All selected employees already have pending appraisals.'))
        
        # Return action to view created appraisals
        return {
            'name': _('Created Appraisals'),
            'type': 'ir.actions.act_window',
            'res_model': 'hr.appraisal',
            'view_mode': 'list,form',
            'domain': [('id', 'in', created_appraisals.ids)],
        }
