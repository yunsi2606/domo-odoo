# -*- coding: utf-8 -*-
from odoo import api, fields, models, _, SUPERUSER_ID
from odoo.exceptions import ValidationError, UserError
from datetime import datetime, timedelta, time
from dateutil.relativedelta import relativedelta
from dateutil.rrule import rrule, DAILY, WEEKLY, MONTHLY
import pytz


class PlanningSlot(models.Model):
    """
    Planning Slot - The core model representing a scheduled shift/work slot
    """
    _name = 'planning.slot'
    _description = 'Planning Shift'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'start_datetime desc, id'
    _rec_name = 'display_name'

    # === Basic Fields ===
    name = fields.Char(
        string='Note',
        help='Additional note for this shift'
    )
    display_name = fields.Char(
        string='Display Name',
        compute='_compute_display_name',
        store=True
    )
    active = fields.Boolean(
        string='Active',
        default=True
    )
    company_id = fields.Many2one(
        'res.company',
        string='Company',
        required=True,
        default=lambda self: self.env.company
    )
    color = fields.Integer(
        string='Color',
        compute='_compute_color'
    )
    
    # === Resource Assignment ===
    employee_id = fields.Many2one(
        'hr.employee',
        string='Employee',
        tracking=True,
        index=True,
        help='The employee assigned to this shift'
    )
    user_id = fields.Many2one(
        'res.users',
        string='User',
        related='employee_id.user_id',
        store=True,
        readonly=True
    )
    department_id = fields.Many2one(
        'hr.department',
        string='Department',
        related='employee_id.department_id',
        store=True,
        readonly=True
    )
    manager_id = fields.Many2one(
        'hr.employee',
        string='Manager',
        related='employee_id.parent_id',
        store=True,
        readonly=True
    )
    resource_id = fields.Many2one(
        'resource.resource',
        string='Resource',
        related='employee_id.resource_id',
        store=True,
        readonly=True
    )
    
    # === Role ===
    role_id = fields.Many2one(
        'planning.role',
        string='Role',
        tracking=True,
        index=True
    )
    
    # === Template ===
    template_id = fields.Many2one(
        'planning.template',
        string='Shift Template',
        help='Select a template to auto-fill timing details'
    )
    
    # === Timing ===
    start_datetime = fields.Datetime(
        string='Start Date',
        required=True,
        tracking=True,
        default=lambda self: fields.Datetime.now().replace(hour=8, minute=0, second=0)
    )
    end_datetime = fields.Datetime(
        string='End Date',
        required=True,
        tracking=True,
        default=lambda self: fields.Datetime.now().replace(hour=17, minute=0, second=0)
    )
    
    # Duration & Hours
    allocated_hours = fields.Float(
        string='Allocated Hours',
        compute='_compute_allocated_hours',
        store=True,
        readonly=False,
        help='Total hours allocated for this shift'
    )
    allocated_percentage = fields.Float(
        string='Allocated Time (%)',
        compute='_compute_allocated_percentage',
        help='Percentage of working time allocated'
    )
    working_days_count = fields.Float(
        string='Working Days',
        compute='_compute_working_days',
        store=True
    )
    
    # === Status & Publishing ===
    state = fields.Selection([
        ('draft', 'Draft'),
        ('published', 'Published'),
        ('done', 'Done'),
        ('cancel', 'Cancelled'),
    ], string='Status', default='draft', tracking=True, index=True)
    
    is_published = fields.Boolean(
        string='Is Published',
        compute='_compute_is_published',
        store=True
    )
    publication_warning = fields.Boolean(
        string='Has Publication Warning',
        compute='_compute_publication_warning'
    )
    
    # === Conflict Detection ===
    conflict_slot_ids = fields.Many2many(
        'planning.slot',
        'planning_slot_conflict_rel',
        'slot_id',
        'conflict_slot_id',
        string='Conflicting Shifts',
        compute='_compute_conflicts'
    )
    has_conflict = fields.Boolean(
        string='Has Conflict',
        compute='_compute_conflicts',
        store=True
    )
    overlap_slot_count = fields.Integer(
        string='Overlapping Shifts',
        compute='_compute_conflicts'
    )
    
    # === Recurrence ===
    recurrency_id = fields.Many2one(
        'planning.slot.recurrency',
        string='Recurrency Group',
        readonly=True,
        index=True
    )
    repeat = fields.Boolean(
        string='Repeat',
        default=False
    )
    repeat_interval = fields.Integer(
        string='Repeat Every',
        default=1
    )
    repeat_unit = fields.Selection([
        ('day', 'Days'),
        ('week', 'Weeks'),
        ('month', 'Months'),
    ], string='Repeat Unit', default='week')
    repeat_until = fields.Date(
        string='Repeat Until'
    )
    repeat_type = fields.Selection([
        ('forever', 'Forever'),
        ('until', 'Until'),
        ('x_times', 'Number of Times'),
    ], string='Repeat Type', default='until')
    repeat_x_times = fields.Integer(
        string='Number of Repeats',
        default=1
    )
    
    # Weekday selection for weekly repeat
    repeat_monday = fields.Boolean(
        string='Monday',
        default=True
    )
    repeat_tuesday = fields.Boolean(
        string='Tuesday',
        default=True
    )
    repeat_wednesday = fields.Boolean(
        string='Wednesday',
        default=True
    )
    repeat_thursday = fields.Boolean(
        string='Thursday',
        default=True
    )
    repeat_friday = fields.Boolean(
        string='Friday',
        default=True
    )
    repeat_saturday = fields.Boolean(
        string='Saturday',
        default=False
    )
    repeat_sunday = fields.Boolean(
        string='Sunday',
        default=False
    )
    
    # === Time Off ===
    is_leave = fields.Boolean(
        string='Is Time Off',
        compute='_compute_is_leave'
    )
    leave_id = fields.Many2one(
        'hr.leave',
        string='Related Time Off',
        readonly=True
    )
    
    # === Filters ===
    was_copied = fields.Boolean(
        string='Was Copied',
        default=False
    )
    is_past = fields.Boolean(
        string='Is Past',
        compute='_compute_is_past'
    )
    
    # === Request ===
    request_to_switch = fields.Boolean(
        string='Request to Switch',
        default=False
    )
    allow_self_unassign = fields.Boolean(
        string='Allow Self Unassign',
        default=False
    )
    
    # === Computed Display Fields ===
    @api.depends('employee_id', 'role_id', 'start_datetime', 'end_datetime')
    def _compute_display_name(self):
        for slot in self:
            parts = []
            if slot.employee_id:
                parts.append(slot.employee_id.name)
            if slot.role_id:
                parts.append(slot.role_id.name)
            if slot.start_datetime and slot.end_datetime:
                start_str = slot.start_datetime.strftime('%d/%m %H:%M')
                end_str = slot.end_datetime.strftime('%H:%M')
                parts.append(f"({start_str}-{end_str})")
            slot.display_name = ' - '.join(parts) if parts else _('New Shift')
    
    @api.depends('role_id.color', 'state')
    def _compute_color(self):
        for slot in self:
            if slot.state == 'cancel':
                slot.color = 1  # Red
            elif slot.state == 'done':
                slot.color = 10  # Green
            elif slot.role_id:
                slot.color = slot.role_id.color
            else:
                slot.color = 0  # Default

    @api.depends('start_datetime', 'end_datetime')
    def _compute_allocated_hours(self):
        for slot in self:
            if slot.start_datetime and slot.end_datetime:
                delta = slot.end_datetime - slot.start_datetime
                slot.allocated_hours = delta.total_seconds() / 3600.0
            else:
                slot.allocated_hours = 0.0
    
    @api.depends('allocated_hours', 'employee_id')
    def _compute_allocated_percentage(self):
        for slot in self:
            if slot.employee_id and slot.employee_id.resource_calendar_id:
                # Get daily hours from employee's calendar (hours_per_day is available in Odoo 18)
                hours_per_day = slot.employee_id.resource_calendar_id.hours_per_day or 8.0
                slot.allocated_percentage = (slot.allocated_hours / hours_per_day) * 100 if hours_per_day else 0
            else:
                slot.allocated_percentage = 0
    
    @api.depends('start_datetime', 'end_datetime')
    def _compute_working_days(self):
        for slot in self:
            if slot.start_datetime and slot.end_datetime:
                delta = slot.end_datetime - slot.start_datetime
                slot.working_days_count = delta.days + delta.seconds / 86400.0
            else:
                slot.working_days_count = 0
    
    @api.depends('state')
    def _compute_is_published(self):
        for slot in self:
            slot.is_published = slot.state == 'published'
    
    @api.depends('employee_id', 'start_datetime', 'end_datetime')
    def _compute_publication_warning(self):
        for slot in self:
            slot.publication_warning = not slot.employee_id
    
    @api.depends('employee_id', 'start_datetime', 'end_datetime')
    def _compute_conflicts(self):
        """Detect overlapping shifts for the same employee"""
        for slot in self:
            slot.conflict_slot_ids = [(5, 0, 0)]
            slot.has_conflict = False
            slot.overlap_slot_count = 0
            
            if slot.employee_id and slot.start_datetime and slot.end_datetime:
                overlapping = self.search([
                    ('id', '!=', slot.id),
                    ('employee_id', '=', slot.employee_id.id),
                    ('state', 'not in', ['cancel']),
                    '|',
                    '&', ('start_datetime', '<', slot.end_datetime),
                         ('end_datetime', '>', slot.start_datetime),
                    '&', ('start_datetime', '>=', slot.start_datetime),
                         ('start_datetime', '<', slot.end_datetime),
                ])
                if overlapping:
                    slot.conflict_slot_ids = [(6, 0, overlapping.ids)]
                    slot.has_conflict = True
                    slot.overlap_slot_count = len(overlapping)
    
    @api.depends('employee_id', 'start_datetime', 'end_datetime')
    def _compute_is_leave(self):
        """Check if shift overlaps with employee's time off"""
        HrLeave = self.env['hr.leave']
        for slot in self:
            slot.is_leave = False
            if slot.employee_id and slot.start_datetime and slot.end_datetime:
                leaves = HrLeave.search([
                    ('employee_id', '=', slot.employee_id.id),
                    ('state', '=', 'validate'),
                    ('date_from', '<=', slot.end_datetime),
                    ('date_to', '>=', slot.start_datetime),
                ])
                slot.is_leave = bool(leaves)
    
    @api.depends('end_datetime')
    def _compute_is_past(self):
        now = fields.Datetime.now()
        for slot in self:
            slot.is_past = slot.end_datetime and slot.end_datetime < now
    
    # === Onchange Methods ===
    @api.onchange('template_id')
    def _onchange_template_id(self):
        """Apply template settings to the slot"""
        if self.template_id:
            template = self.template_id
            if template.role_id:
                self.role_id = template.role_id
            
            # Apply timing from template
            if self.start_datetime:
                base_date = self.start_datetime.date()
                start_hour = int(template.start_time)
                start_minute = int((template.start_time - start_hour) * 60)
                end_hour = int(template.end_time)
                end_minute = int((template.end_time - end_hour) * 60)
                
                self.start_datetime = datetime.combine(
                    base_date, 
                    time(hour=start_hour, minute=start_minute)
                )
                self.end_datetime = datetime.combine(
                    base_date, 
                    time(hour=end_hour, minute=end_minute)
                )
    
    @api.onchange('employee_id')
    def _onchange_employee_id(self):
        """Set default role from employee's roles"""
        if self.employee_id and not self.role_id:
            roles = self.env['planning.role'].search([
                ('resource_ids', 'in', self.employee_id.id)
            ], limit=1)
            if roles:
                self.role_id = roles[0]
    
    @api.onchange('start_datetime', 'allocated_hours')
    def _onchange_hours(self):
        """Recalculate end datetime when hours changed"""
        if self.start_datetime and self.allocated_hours:
            self.end_datetime = self.start_datetime + timedelta(hours=self.allocated_hours)
    
    # === Constraints ===
    @api.constrains('start_datetime', 'end_datetime')
    def _check_dates(self):
        for slot in self:
            if slot.start_datetime and slot.end_datetime:
                if slot.start_datetime >= slot.end_datetime:
                    raise ValidationError(_('End date must be after start date.'))
    
    @api.constrains('allocated_hours')
    def _check_allocated_hours(self):
        for slot in self:
            if slot.allocated_hours < 0:
                raise ValidationError(_('Allocated hours cannot be negative.'))
    
    # === CRUD Methods ===
    @api.model_create_multi
    def create(self, vals_list):
        slots = super().create(vals_list)
        # Generate recurrence if needed
        for slot in slots:
            if slot.repeat and not slot.recurrency_id:
                slot._create_recurrence()
        return slots
    
    def write(self, vals):
        res = super().write(vals)
        # Check if repeat was enabled and recurrence needs to be created
        if vals.get('repeat') or 'repeat' in vals:
            for slot in self:
                if slot.repeat and not slot.recurrency_id:
                    slot._create_recurrence()
        return res
    
    def copy(self, default=None):
        default = dict(default or {})
        default['was_copied'] = True
        default['state'] = 'draft'
        return super().copy(default)
    
    # === Action Methods ===
    def action_publish(self):
        """Publish the shift and notify employee"""
        slots_to_publish = self.filtered(lambda s: s.state == 'draft')
        if not slots_to_publish:
            raise UserError(_('No draft shifts to publish.'))
        
        for slot in slots_to_publish:
            if not slot.employee_id:
                raise UserError(_('Cannot publish shift without an assigned employee.'))
        
        slots_to_publish.write({'state': 'published'})
        
        # Send notification
        for slot in slots_to_publish:
            slot._send_notification()
        
        return True
    
    def action_unpublish(self):
        """Unpublish shift back to draft"""
        self.filtered(lambda s: s.state == 'published').write({'state': 'draft'})
        return True
    
    def action_done(self):
        """Mark shift as completed"""
        self.write({'state': 'done'})
        return True
    
    def action_cancel(self):
        """Cancel the shift"""
        self.write({'state': 'cancel'})
        return True
    
    def action_draft(self):
        """Reset to draft"""
        self.write({'state': 'draft'})
        return True
    
    def action_unassign(self):
        """Unassign employee from shift"""
        if self.state == 'published':
            raise UserError(_('Cannot unassign employee from published shift.'))
        self.write({
            'employee_id': False,
            'state': 'draft'
        })
        return True
    
    def action_self_unassign(self):
        """Allow employee to unassign themselves"""
        self.ensure_one()
        if not self.allow_self_unassign:
            raise UserError(_('Self unassignment is not allowed for this shift.'))
        if self.env.user.employee_id != self.employee_id:
            raise UserError(_('You can only unassign yourself from your own shifts.'))
        self.action_unassign()
        return True
    
    def action_copy_previous(self, days=7):
        """Copy shift to previous week"""
        self.ensure_one()
        return self.copy({
            'start_datetime': self.start_datetime - timedelta(days=days),
            'end_datetime': self.end_datetime - timedelta(days=days),
            'state': 'draft',
        })
    
    def action_copy_next(self, days=7):
        """Copy shift to next week"""
        self.ensure_one()
        return self.copy({
            'start_datetime': self.start_datetime + timedelta(days=days),
            'end_datetime': self.end_datetime + timedelta(days=days),
            'state': 'draft',
        })
    
    def action_send(self):
        """Open wizard to send schedule to employees"""
        return {
            'name': _('Send Shift'),
            'type': 'ir.actions.act_window',
            'res_model': 'planning.send',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_slot_ids': [(6, 0, self.ids)],
            }
        }
    
    def action_view_conflicts(self):
        """View conflicting shifts"""
        self.ensure_one()
        return {
            'name': _('Conflicting Shifts'),
            'type': 'ir.actions.act_window',
            'res_model': 'planning.slot',
            'view_mode': 'tree,form',
            'domain': [('id', 'in', self.conflict_slot_ids.ids)],
        }
    
    # === Recurrence Methods ===
    def _create_recurrence(self):
        """Create recurring slots based on repeat settings"""
        self.ensure_one()
        if not self.repeat:
            return
        
        # Create recurrence group
        recurrency = self.env['planning.slot.recurrency'].create({
            'repeat_interval': self.repeat_interval,
            'repeat_unit': self.repeat_unit,
            'repeat_until': self.repeat_until,
            'repeat_type': self.repeat_type,
            'repeat_x_times': self.repeat_x_times,
            'repeat_monday': self.repeat_monday,
            'repeat_tuesday': self.repeat_tuesday,
            'repeat_wednesday': self.repeat_wednesday,
            'repeat_thursday': self.repeat_thursday,
            'repeat_friday': self.repeat_friday,
            'repeat_saturday': self.repeat_saturday,
            'repeat_sunday': self.repeat_sunday,
        })
        
        self.recurrency_id = recurrency
        
        # Generate recurring slots
        recurrency._generate_slots(self)
        
        return recurrency
    
    # === Notification Methods ===
    def _send_notification(self):
        """Send email notification to employee"""
        self.ensure_one()
        if not self.employee_id or not self.employee_id.work_email:
            return False
        
        template = self.env.ref('hr_planning.mail_template_slot_notification', raise_if_not_found=False)
        if template:
            template.send_mail(self.id, force_send=True)
        return True
    
    # === Utility Methods ===
    def _get_tz(self):
        """Get timezone for the slot"""
        return self.employee_id.tz or self.env.user.tz or 'UTC'
    
    def _localize_datetime(self, dt):
        """Localize datetime to slot's timezone"""
        tz = pytz.timezone(self._get_tz())
        return pytz.utc.localize(dt).astimezone(tz)
    
    # === Cron Methods ===
    @api.model
    def _cron_auto_publish_slots(self):
        """Auto-publish draft slots that are scheduled to start soon"""
        # Find slots starting in the next 24 hours that are still draft
        now = fields.Datetime.now()
        tomorrow = now + timedelta(days=1)
        
        slots_to_publish = self.search([
            ('state', '=', 'draft'),
            ('employee_id', '!=', False),
            ('start_datetime', '>=', now),
            ('start_datetime', '<=', tomorrow),
        ])
        
        if slots_to_publish:
            slots_to_publish.write({'state': 'published'})
            for slot in slots_to_publish:
                slot._send_notification()
        
        return True
    
    @api.model
    def _cron_archive_past_slots(self):
        """Archive slots that ended more than 30 days ago"""
        cutoff_date = fields.Datetime.now() - timedelta(days=30)
        
        old_slots = self.search([
            ('end_datetime', '<', cutoff_date),
            ('state', 'in', ['done', 'cancel']),
            ('active', '=', True),
        ])
        
        if old_slots:
            old_slots.write({'active': False})
        
        return True
    
    @api.model
    def _demo_create_slots(self):
        """Create demo planning slots for testing"""
        # Get some employees
        employees = self.env['hr.employee'].search([], limit=5)
        if not employees:
            return
        
        # Get roles
        roles = self.env['planning.role'].search([], limit=3)
        role_ids = roles.ids if roles else [False]
        
        # Get templates
        templates = self.env['planning.template'].search([], limit=3)
        
        # Create slots for current week
        today = fields.Date.today()
        week_start = today - timedelta(days=today.weekday())
        
        demo_slots = []
        for i, employee in enumerate(employees):
            for day_offset in range(5):  # Monday to Friday
                slot_date = week_start + timedelta(days=day_offset)
                
                # Alternate between templates or use default timing
                if templates and i < len(templates):
                    template = templates[i]
                    start_hour = int(template.start_time)
                    start_min = int((template.start_time - start_hour) * 60)
                    duration = template.duration
                else:
                    start_hour = 8 + (i % 3)
                    start_min = 0
                    duration = 8
                
                start_dt = datetime.combine(slot_date, time(hour=start_hour, minute=start_min))
                end_dt = start_dt + timedelta(hours=duration)
                
                demo_slots.append({
                    'employee_id': employee.id,
                    'role_id': role_ids[i % len(role_ids)] if role_ids[0] else False,
                    'start_datetime': start_dt,
                    'end_datetime': end_dt,
                    'state': 'published' if day_offset < 3 else 'draft',
                })
        
        if demo_slots:
            self.create(demo_slots)
        
        return True


class PlanningSlotRecurrency(models.Model):
    """
    Planning Slot Recurrency - Groups recurring slots together
    """
    _name = 'planning.slot.recurrency'
    _description = 'Planning Slot Recurrence'
    
    slot_ids = fields.One2many(
        'planning.slot',
        'recurrency_id',
        string='Slots'
    )
    repeat_interval = fields.Integer(
        string='Repeat Every',
        default=1
    )
    repeat_unit = fields.Selection([
        ('day', 'Days'),
        ('week', 'Weeks'),
        ('month', 'Months'),
    ], string='Repeat Unit', default='week')
    repeat_until = fields.Date(
        string='Repeat Until'
    )
    repeat_type = fields.Selection([
        ('forever', 'Forever'),
        ('until', 'Until'),
        ('x_times', 'Number of Times'),
    ], string='Repeat Type', default='until')
    repeat_x_times = fields.Integer(
        string='Number of Repeats',
        default=1
    )
    
    # Weekday selection for weekly repeat
    repeat_monday = fields.Boolean(
        string='Monday',
        default=True
    )
    repeat_tuesday = fields.Boolean(
        string='Tuesday',
        default=True
    )
    repeat_wednesday = fields.Boolean(
        string='Wednesday',
        default=True
    )
    repeat_thursday = fields.Boolean(
        string='Thursday',
        default=True
    )
    repeat_friday = fields.Boolean(
        string='Friday',
        default=True
    )
    repeat_saturday = fields.Boolean(
        string='Saturday',
        default=False
    )
    repeat_sunday = fields.Boolean(
        string='Sunday',
        default=False
    )
    
    company_id = fields.Many2one(
        'res.company',
        string='Company',
        default=lambda self: self.env.company
    )
    
    def _generate_slots(self, base_slot):
        """Generate recurring slots based on base slot"""
        self.ensure_one()
        
        # Get selected weekdays (0=Monday, 6=Sunday)
        selected_weekdays = []
        if self.repeat_monday:
            selected_weekdays.append(0)
        if self.repeat_tuesday:
            selected_weekdays.append(1)
        if self.repeat_wednesday:
            selected_weekdays.append(2)
        if self.repeat_thursday:
            selected_weekdays.append(3)
        if self.repeat_friday:
            selected_weekdays.append(4)
        if self.repeat_saturday:
            selected_weekdays.append(5)
        if self.repeat_sunday:
            selected_weekdays.append(6)
        
        # If no weekdays selected, default to all weekdays
        if not selected_weekdays:
            selected_weekdays = [0, 1, 2, 3, 4]  # Monday to Friday
        
        # Determine frequency
        freq_map = {
            'day': DAILY,
            'week': WEEKLY,
            'month': MONTHLY,
        }
        freq = freq_map.get(self.repeat_unit, WEEKLY)
        
        # For daily recurrence, we use DAILY and filter by weekdays
        # For weekly, we generate daily dates and filter
        use_daily_generation = self.repeat_unit == 'week' or self.repeat_unit == 'day'
        
        # Parameters for generation
        if self.repeat_type == 'until' and self.repeat_until:
            if use_daily_generation:
                # Generate all days then filter by weekday
                all_dates = list(rrule(
                    DAILY,
                    dtstart=base_slot.start_datetime,
                    until=datetime.combine(self.repeat_until, time.max)
                ))
            else:
                all_dates = list(rrule(
                    freq,
                    interval=self.repeat_interval,
                    dtstart=base_slot.start_datetime,
                    until=datetime.combine(self.repeat_until, time.max)
                ))
        elif self.repeat_type == 'x_times':
            if use_daily_generation:
                # Generate more dates than needed then filter
                all_dates = list(rrule(
                    DAILY,
                    dtstart=base_slot.start_datetime,
                    count=self.repeat_x_times * 7 + 10  # Extra buffer for filtering
                ))
            else:
                all_dates = list(rrule(
                    freq,
                    interval=self.repeat_interval,
                    dtstart=base_slot.start_datetime,
                    count=self.repeat_x_times + 1
                ))
        else:
            # Forever - limit to reasonable number
            if use_daily_generation:
                all_dates = list(rrule(
                    DAILY,
                    dtstart=base_slot.start_datetime,
                    count=365  # Max 1 year
                ))
            else:
                all_dates = list(rrule(
                    freq,
                    interval=self.repeat_interval,
                    dtstart=base_slot.start_datetime,
                    count=52
                ))
        
        # Filter dates by selected weekdays for daily/weekly recurrence
        if use_daily_generation:
            filtered_dates = [dt for dt in all_dates if dt.weekday() in selected_weekdays]
            
            # For weekly recurrence, apply interval (every N weeks)
            if self.repeat_unit == 'week' and self.repeat_interval > 1:
                base_week = base_slot.start_datetime.isocalendar()[1]
                base_year = base_slot.start_datetime.isocalendar()[0]
                valid_dates = []
                for dt in filtered_dates:
                    dt_week = dt.isocalendar()[1]
                    dt_year = dt.isocalendar()[0]
                    weeks_diff = (dt_year - base_year) * 52 + (dt_week - base_week)
                    if weeks_diff % self.repeat_interval == 0:
                        valid_dates.append(dt)
                filtered_dates = valid_dates
            
            # Limit by x_times if applicable
            if self.repeat_type == 'x_times':
                filtered_dates = filtered_dates[:self.repeat_x_times + 1]
            
            dates = filtered_dates
        else:
            dates = all_dates
        
        # Skip first date (already exists as base)
        duration = base_slot.end_datetime - base_slot.start_datetime
        
        slots = []
        for dt in dates[1:]:
            slots.append({
                'employee_id': base_slot.employee_id.id,
                'role_id': base_slot.role_id.id,
                'template_id': base_slot.template_id.id,
                'start_datetime': dt,
                'end_datetime': dt + duration,
                'recurrency_id': self.id,
                'repeat': False,  # Don't cascade recurrence
                'name': base_slot.name,
                'company_id': base_slot.company_id.id,
            })
        
        if slots:
            self.env['planning.slot'].create(slots)
        
        return True
