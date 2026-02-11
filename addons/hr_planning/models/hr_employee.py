# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from datetime import date, datetime, timedelta


class HrEmployee(models.Model):
    """
    Extension of hr.employee to add planning-related fields
    """
    _inherit = 'hr.employee'

    # === Planning Fields ===
    planning_role_ids = fields.Many2many(
        'planning.role',
        'planning_role_employee_rel',
        'employee_id',
        'role_id',
        string='Planning Roles',
        help='Roles this employee can perform'
    )
    default_planning_role_id = fields.Many2one(
        'planning.role',
        string='Default Role',
        help='Default role when creating shifts for this employee'
    )
    
    # Slot counts
    planning_slot_count = fields.Integer(
        string='Planning Slots',
        compute='_compute_planning_slot_count'
    )
    current_week_slots = fields.Integer(
        string='This Week Shifts',
        compute='_compute_current_week_slots'
    )
    
    # Hours computation
    allocated_hours_this_week = fields.Float(
        string='Allocated Hours (This Week)',
        compute='_compute_planning_hours'
    )
    allocated_hours_this_month = fields.Float(
        string='Allocated Hours (This Month)',
        compute='_compute_planning_hours'
    )
    planning_utilization = fields.Float(
        string='Planning Utilization (%)',
        compute='_compute_planning_utilization',
        help='Percentage of working hours allocated'
    )
    
    # Availability
    has_planning_conflict = fields.Boolean(
        string='Has Conflicts',
        compute='_compute_has_planning_conflict'
    )
    is_available = fields.Boolean(
        string='Is Available',
        compute='_compute_is_available'
    )
    
    def _compute_planning_slot_count(self):
        """Count total planning slots for employee"""
        PlanningSlot = self.env['planning.slot']
        for employee in self:
            if employee.id:
                employee.planning_slot_count = PlanningSlot.search_count([
                    ('employee_id', '=', employee.id),
                    ('state', '!=', 'cancel')
                ])
            else:
                employee.planning_slot_count = 0
    
    def _compute_current_week_slots(self):
        """Count slots for current week"""
        PlanningSlot = self.env['planning.slot']
        today = date.today()
        week_start = today - timedelta(days=today.weekday())
        week_end = week_start + timedelta(days=6)
        
        for employee in self:
            if employee.id:
                employee.current_week_slots = PlanningSlot.search_count([
                    ('employee_id', '=', employee.id),
                    ('state', '!=', 'cancel'),
                    ('start_datetime', '>=', datetime.combine(week_start, datetime.min.time())),
                    ('end_datetime', '<=', datetime.combine(week_end, datetime.max.time())),
                ])
            else:
                employee.current_week_slots = 0
    
    def _compute_planning_hours(self):
        """Compute allocated hours for this week and month"""
        PlanningSlot = self.env['planning.slot']
        today = date.today()
        
        # Week boundaries
        week_start = today - timedelta(days=today.weekday())
        week_end = week_start + timedelta(days=6)
        
        # Month boundaries
        month_start = today.replace(day=1)
        if today.month == 12:
            month_end = today.replace(year=today.year + 1, month=1, day=1) - timedelta(days=1)
        else:
            month_end = today.replace(month=today.month + 1, day=1) - timedelta(days=1)
        
        for employee in self:
            if employee.id:
                # This week
                week_slots = PlanningSlot.search([
                    ('employee_id', '=', employee.id),
                    ('state', '!=', 'cancel'),
                    ('start_datetime', '>=', datetime.combine(week_start, datetime.min.time())),
                    ('end_datetime', '<=', datetime.combine(week_end, datetime.max.time())),
                ])
                employee.allocated_hours_this_week = sum(week_slots.mapped('allocated_hours'))
                
                # This month
                month_slots = PlanningSlot.search([
                    ('employee_id', '=', employee.id),
                    ('state', '!=', 'cancel'),
                    ('start_datetime', '>=', datetime.combine(month_start, datetime.min.time())),
                    ('end_datetime', '<=', datetime.combine(month_end, datetime.max.time())),
                ])
                employee.allocated_hours_this_month = sum(month_slots.mapped('allocated_hours'))
            else:
                employee.allocated_hours_this_week = 0
                employee.allocated_hours_this_month = 0
    
    @api.depends('allocated_hours_this_week', 'resource_calendar_id')
    def _compute_planning_utilization(self):
        """Compute percentage of working hours utilized"""
        for employee in self:
            if employee.resource_calendar_id:
                # hours_per_day is available in Odoo 18, calculate weekly hours
                hours_per_day = employee.resource_calendar_id.hours_per_day or 8.0
                expected_hours = hours_per_day * 5  # 5 working days
                if expected_hours > 0:
                    employee.planning_utilization = (
                        employee.allocated_hours_this_week / expected_hours
                    ) * 100
                else:
                    employee.planning_utilization = 0
            else:
                employee.planning_utilization = 0
    
    def _compute_has_planning_conflict(self):
        """Check if employee has any conflicting slots"""
        PlanningSlot = self.env['planning.slot']
        for employee in self:
            if employee.id:
                conflicts = PlanningSlot.search_count([
                    ('employee_id', '=', employee.id),
                    ('has_conflict', '=', True),
                    ('state', '!=', 'cancel')
                ])
                employee.has_planning_conflict = conflicts > 0
            else:
                employee.has_planning_conflict = False
    
    def _compute_is_available(self):
        """Check if employee is available now"""
        now = fields.Datetime.now()
        PlanningSlot = self.env['planning.slot']
        HrLeave = self.env['hr.leave']
        
        for employee in self:
            if not employee.id:
                employee.is_available = True
                continue
                
            # Check if on leave
            on_leave = HrLeave.search_count([
                ('employee_id', '=', employee.id),
                ('state', '=', 'validate'),
                ('date_from', '<=', now),
                ('date_to', '>=', now),
            ])
            
            if on_leave:
                employee.is_available = False
                continue
            
            # Check if already in a shift
            in_shift = PlanningSlot.search_count([
                ('employee_id', '=', employee.id),
                ('state', '=', 'published'),
                ('start_datetime', '<=', now),
                ('end_datetime', '>=', now),
            ])
            
            employee.is_available = not in_shift
    
    def action_view_planning(self):
        """Open planning view for this employee"""
        self.ensure_one()
        return {
            'name': _('Planning for %s', self.name),
            'type': 'ir.actions.act_window',
            'res_model': 'planning.slot',
            'view_mode': 'calendar,list,form',
            'domain': [('employee_id', '=', self.id)],
            'context': {
                'default_employee_id': self.id,
                'default_role_id': self.default_planning_role_id.id if self.default_planning_role_id else False,
            },
        }
    
    def action_open_planning_slots(self):
        """Open all planning slots for employee"""
        self.ensure_one()
        return {
            'name': _('%s\'s Shifts', self.name),
            'type': 'ir.actions.act_window',
            'res_model': 'planning.slot',
            'view_mode': 'list,form,calendar',
            'domain': [('employee_id', '=', self.id)],
            'context': {'default_employee_id': self.id},
        }
    
    def get_planning_slots_for_period(self, start_date, end_date):
        """Get planning slots within a period"""
        self.ensure_one()
        return self.env['planning.slot'].search([
            ('employee_id', '=', self.id),
            ('state', '!=', 'cancel'),
            ('start_datetime', '>=', start_date),
            ('end_datetime', '<=', end_date),
        ])


class HrEmployeePublic(models.Model):
    """
    Extension of public employee model for portal access
    """
    _inherit = 'hr.employee.public'
    
    planning_role_ids = fields.Many2many(
        'planning.role',
        related='employee_id.planning_role_ids',
        string='Planning Roles',
    )
