# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import UserError
from datetime import datetime, timedelta


class PlanningSlotCopy(models.TransientModel):
    """
    Wizard to copy planning slots from one period to another
    """
    _name = 'planning.slot.copy'
    _description = 'Copy Planning Slots'

    # Source period
    source_start_date = fields.Date(
        string='Source Start Date',
        required=True,
        default=lambda self: self._default_source_start()
    )
    source_end_date = fields.Date(
        string='Source End Date',
        required=True,
        default=lambda self: self._default_source_end()
    )
    
    # Target period
    target_start_date = fields.Date(
        string='Target Start Date',
        required=True,
        default=lambda self: fields.Date.today()
    )
    
    # Options
    copy_mode = fields.Selection([
        ('week', 'Copy Previous Week'),
        ('custom', 'Custom Period'),
    ], string='Copy Mode', default='week')
    
    employee_ids = fields.Many2many(
        'hr.employee',
        string='Filter by Employees',
        help='Leave empty to copy all employees'
    )
    
    role_ids = fields.Many2many(
        'planning.role',
        string='Filter by Roles',
        help='Leave empty to copy all roles'
    )
    
    include_published = fields.Boolean(
        string='Include Published Shifts',
        default=True
    )
    
    mark_as_draft = fields.Boolean(
        string='Mark Copied as Draft',
        default=True
    )
    
    preview_count = fields.Integer(
        string='Shifts to Copy',
        compute='_compute_preview'
    )
    
    preview_info = fields.Text(
        string='Preview',
        compute='_compute_preview'
    )
    
    def _default_source_start(self):
        """Default to start of previous week"""
        today = fields.Date.today()
        return today - timedelta(days=today.weekday() + 7)
    
    def _default_source_end(self):
        """Default to end of previous week"""
        today = fields.Date.today()
        start = today - timedelta(days=today.weekday() + 7)
        return start + timedelta(days=6)
    
    @api.depends('source_start_date', 'source_end_date', 'employee_ids', 'role_ids')
    def _compute_preview(self):
        for wizard in self:
            slots = wizard._get_slots_to_copy()
            wizard.preview_count = len(slots)
            
            if slots:
                info_lines = [
                    _('%d shifts found:') % len(slots),
                    ''
                ]
                # Group by employee
                by_employee = {}
                for slot in slots:
                    emp_name = slot.employee_id.name if slot.employee_id else _('Unassigned')
                    if emp_name not in by_employee:
                        by_employee[emp_name] = 0
                    by_employee[emp_name] += 1
                
                for emp, count in by_employee.items():
                    info_lines.append(f"• {emp}: {count} shifts")
                
                wizard.preview_info = '\n'.join(info_lines)
            else:
                wizard.preview_info = _('No shifts found in source period')
    
    @api.onchange('copy_mode')
    def _onchange_copy_mode(self):
        if self.copy_mode == 'week':
            self.source_start_date = self._default_source_start()
            self.source_end_date = self._default_source_end()
            # Target is current week
            today = fields.Date.today()
            self.target_start_date = today - timedelta(days=today.weekday())
    
    def _get_slots_to_copy(self):
        """Get slots in source period matching filters"""
        domain = [
            ('start_datetime', '>=', datetime.combine(self.source_start_date, datetime.min.time())),
            ('end_datetime', '<=', datetime.combine(self.source_end_date, datetime.max.time())),
            ('state', '!=', 'cancel'),
        ]
        
        if not self.include_published:
            domain.append(('state', '=', 'draft'))
        
        if self.employee_ids:
            domain.append(('employee_id', 'in', self.employee_ids.ids))
        
        if self.role_ids:
            domain.append(('role_id', 'in', self.role_ids.ids))
        
        return self.env['planning.slot'].search(domain)
    
    def action_copy(self):
        """Copy slots from source to target period"""
        self.ensure_one()
        
        slots_to_copy = self._get_slots_to_copy()
        
        if not slots_to_copy:
            raise UserError(_('No shifts found in source period.'))
        
        # Calculate offset
        day_offset = (self.target_start_date - self.source_start_date).days
        
        new_slots = []
        for slot in slots_to_copy:
            new_start = slot.start_datetime + timedelta(days=day_offset)
            new_end = slot.end_datetime + timedelta(days=day_offset)
            
            new_vals = {
                'employee_id': slot.employee_id.id,
                'role_id': slot.role_id.id,
                'template_id': slot.template_id.id,
                'start_datetime': new_start,
                'end_datetime': new_end,
                'name': slot.name,
                'state': 'draft' if self.mark_as_draft else slot.state,
                'was_copied': True,
                'company_id': slot.company_id.id,
            }
            new_slots.append(new_vals)
        
        created = self.env['planning.slot'].create(new_slots)
        
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Success'),
                'message': _('%d shifts copied successfully!') % len(created),
                'type': 'success',
                'sticky': False,
                'next': {
                    'type': 'ir.actions.act_window',
                    'res_model': 'planning.slot',
                    'view_mode': 'gantt,tree,form',
                    'domain': [('id', 'in', created.ids)],
                    'name': _('Copied Shifts'),
                }
            }
        }
    
    def action_preview(self):
        """Preview slots that will be copied"""
        self.ensure_one()
        slots = self._get_slots_to_copy()
        
        return {
            'name': _('Shifts to Copy'),
            'type': 'ir.actions.act_window',
            'res_model': 'planning.slot',
            'view_mode': 'tree,form',
            'domain': [('id', 'in', slots.ids)],
            'context': {'create': False},
        }
