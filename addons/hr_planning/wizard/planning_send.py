# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import UserError
from datetime import datetime, timedelta


class PlanningSend(models.TransientModel):
    """
    Wizard to send planning notifications to employees
    """
    _name = 'planning.send'
    _description = 'Send Planning Notification'

    slot_ids = fields.Many2many(
        'planning.slot',
        string='Shifts to Send',
        required=True
    )
    
    start_date = fields.Date(
        string='Start Date',
        default=lambda self: fields.Date.today()
    )
    end_date = fields.Date(
        string='End Date',
        default=lambda self: fields.Date.today() + timedelta(days=7)
    )
    
    employee_ids = fields.Many2many(
        'hr.employee',
        string='Employees',
        compute='_compute_employee_ids',
        store=True,
        readonly=False
    )
    
    include_unassigned = fields.Boolean(
        string='Include Unassigned Shifts',
        default=False
    )
    
    publish_slots = fields.Boolean(
        string='Also Publish Shifts',
        default=True,
        help='Publish draft shifts when sending'
    )
    
    note = fields.Text(
        string='Note',
        help='Additional note to include in notification'
    )
    
    slot_count = fields.Integer(
        string='Shifts Count',
        compute='_compute_slot_count'
    )
    
    @api.depends('slot_ids')
    def _compute_employee_ids(self):
        for wizard in self:
            employees = wizard.slot_ids.mapped('employee_id')
            wizard.employee_ids = [(6, 0, employees.ids)]
    
    @api.depends('slot_ids')
    def _compute_slot_count(self):
        for wizard in self:
            wizard.slot_count = len(wizard.slot_ids)
    
    @api.onchange('start_date', 'end_date')
    def _onchange_dates(self):
        """Filter slots by date range"""
        if self.start_date and self.end_date:
            domain = [
                ('start_datetime', '>=', datetime.combine(self.start_date, datetime.min.time())),
                ('end_datetime', '<=', datetime.combine(self.end_date, datetime.max.time())),
                ('state', 'in', ['draft', 'published']),
            ]
            slots = self.env['planning.slot'].search(domain)
            self.slot_ids = [(6, 0, slots.ids)]
    
    def action_send(self):
        """Send planning notifications to employees"""
        self.ensure_one()
        
        if not self.slot_ids:
            raise UserError(_('No shifts selected to send.'))
        
        if not self.employee_ids:
            raise UserError(_('No employees selected.'))
        
        # Publish slots if requested
        if self.publish_slots:
            draft_slots = self.slot_ids.filtered(
                lambda s: s.state == 'draft' and s.employee_id
            )
            draft_slots.action_publish()
        
        # Send notifications
        template = self.env.ref(
            'hr_planning.mail_template_slot_notification',
            raise_if_not_found=False
        )
        
        sent_count = 0
        for employee in self.employee_ids:
            if not employee.work_email:
                continue
            
            employee_slots = self.slot_ids.filtered(
                lambda s: s.employee_id == employee
            )
            
            if not employee_slots:
                continue
            
            # Send email
            if template:
                for slot in employee_slots:
                    template.with_context(
                        custom_note=self.note
                    ).send_mail(slot.id, force_send=True)
                    sent_count += 1
            else:
                # Fallback notification
                employee.message_post(
                    body=_('You have %s scheduled shifts. %s') % (
                        len(employee_slots),
                        self.note or ''
                    ),
                    subject=_('Planning Notification'),
                )
                sent_count += len(employee_slots)
        
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Success'),
                'message': _('%d notifications sent successfully!') % sent_count,
                'type': 'success',
                'sticky': False,
            }
        }
    
    def action_send_all_published(self):
        """Send notifications for all published slots in date range"""
        self.ensure_one()
        
        domain = [
            ('state', '=', 'published'),
            ('employee_id', '!=', False),
        ]
        
        if self.start_date:
            domain.append(
                ('start_datetime', '>=', datetime.combine(self.start_date, datetime.min.time()))
            )
        if self.end_date:
            domain.append(
                ('end_datetime', '<=', datetime.combine(self.end_date, datetime.max.time()))
            )
        
        slots = self.env['planning.slot'].search(domain)
        self.slot_ids = [(6, 0, slots.ids)]
        
        return self.action_send()
