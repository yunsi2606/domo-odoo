# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError
from datetime import datetime, timedelta, date


class HrAppraisal(models.Model):
    """
    HR Appraisal - Main model for employee performance appraisals
    """
    _name = 'hr.appraisal'
    _description = 'Employee Appraisal'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'date_close desc, id desc'
    _rec_name = 'display_name'

    # === Basic Fields ===
    display_name = fields.Char(
        string='Name',
        compute='_compute_display_name',
        store=True
    )
    active = fields.Boolean(default=True)
    company_id = fields.Many2one(
        'res.company',
        string='Company',
        required=True,
        default=lambda self: self.env.company
    )
    
    # === Employee Information ===
    employee_id = fields.Many2one(
        'hr.employee',
        string='Employee',
        required=True,
        tracking=True,
        index=True
    )
    department_id = fields.Many2one(
        'hr.department',
        string='Department',
        related='employee_id.department_id',
        store=True
    )
    job_id = fields.Many2one(
        'hr.job',
        string='Job Position',
        related='employee_id.job_id',
        store=True
    )
    manager_id = fields.Many2one(
        'hr.employee',
        string='Manager',
        compute='_compute_manager_id',
        store=True,
        readonly=False
    )
    manager_user_id = fields.Many2one(
        'res.users',
        string='Manager User',
        related='manager_id.user_id',
        store=True
    )
    
    # === Appraisal Period ===
    date_close = fields.Date(
        string='Appraisal Deadline',
        required=True,
        tracking=True,
        default=lambda self: fields.Date.today() + timedelta(days=30)
    )
    appraisal_period_start = fields.Date(
        string='Period Start',
        required=True,
        default=lambda self: date.today().replace(month=1, day=1)
    )
    appraisal_period_end = fields.Date(
        string='Period End',
        required=True,
        default=lambda self: date.today().replace(month=12, day=31)
    )
    
    # === State Management ===
    state = fields.Selection([
        ('new', 'To Confirm'),
        ('pending', 'Confirmed'),
        ('employee_feedback', 'Employee Feedback'),
        ('manager_feedback', 'Manager Feedback'),
        ('done', 'Done'),
        ('cancel', 'Cancelled'),
    ], string='Status', default='new', tracking=True, required=True, copy=False)
    
    # === Template ===
    template_id = fields.Many2one(
        'hr.appraisal.template',
        string='Appraisal Template',
        help='Template with predefined questions and criteria'
    )
    
    # === Assessment Fields ===
    # Employee Self-Assessment
    employee_self_assessment = fields.Html(
        string='Employee Self-Assessment',
        help='Employee\'s self-evaluation of their performance'
    )
    employee_achievements = fields.Html(
        string='Key Achievements',
        help='Employee\'s key accomplishments during the period'
    )
    employee_challenges = fields.Html(
        string='Challenges Faced',
        help='Challenges and difficulties encountered'
    )
    employee_development = fields.Html(
        string='Development Areas',
        help='Areas where employee wants to develop'
    )
    employee_feedback_date = fields.Datetime(
        string='Employee Feedback Date',
        readonly=True
    )
    
    # Manager Assessment
    manager_assessment = fields.Html(
        string='Manager Assessment',
        help='Manager\'s evaluation of the employee'
    )
    manager_strengths = fields.Html(
        string='Employee Strengths',
        help='Identified strengths of the employee'
    )
    manager_improvements = fields.Html(
        string='Areas for Improvement',
        help='Areas where employee needs to improve'
    )
    manager_recommendations = fields.Html(
        string='Recommendations',
        help='Manager\'s recommendations for career development'
    )
    manager_feedback_date = fields.Datetime(
        string='Manager Feedback Date',
        readonly=True
    )
    
    # === Ratings ===
    employee_rating = fields.Selection([
        ('1', 'Needs Improvement'),
        ('2', 'Below Expectations'),
        ('3', 'Meets Expectations'),
        ('4', 'Exceeds Expectations'),
        ('5', 'Outstanding'),
    ], string='Self Rating', help='Employee\'s self-rating')
    
    manager_rating = fields.Selection([
        ('1', 'Needs Improvement'),
        ('2', 'Below Expectations'),
        ('3', 'Meets Expectations'),
        ('4', 'Exceeds Expectations'),
        ('5', 'Outstanding'),
    ], string='Manager Rating', help='Manager\'s rating of the employee', tracking=True)
    
    final_rating = fields.Selection([
        ('1', 'Needs Improvement'),
        ('2', 'Below Expectations'),
        ('3', 'Meets Expectations'),
        ('4', 'Exceeds Expectations'),
        ('5', 'Outstanding'),
    ], string='Final Rating', help='Final agreed upon rating', tracking=True)
    
    rating_score = fields.Float(
        string='Rating Score',
        compute='_compute_rating_score',
        store=True
    )
    
    # === Goals ===
    goal_ids = fields.One2many(
        'hr.appraisal.goal',
        'appraisal_id',
        string='Goals'
    )
    goal_count = fields.Integer(
        string='Goal Count',
        compute='_compute_goal_count'
    )
    goals_completion = fields.Float(
        string='Goals Completion (%)',
        compute='_compute_goals_completion',
        store=True
    )
    
    # === Skills ===
    skill_ids = fields.One2many(
        'hr.appraisal.skill',
        'appraisal_id',
        string='Skills Assessment'
    )
    skill_count = fields.Integer(
        string='Skill Count',
        compute='_compute_skill_count'
    )
    skills_average = fields.Float(
        string='Skills Average',
        compute='_compute_skills_average',
        store=True
    )
    
    # === Notes ===
    note_ids = fields.One2many(
        'hr.appraisal.note',
        'appraisal_id',
        string='Meeting Notes'
    )
    
    # === Meeting ===
    meeting_id = fields.Many2one(
        'calendar.event',
        string='Appraisal Meeting'
    )
    meeting_date = fields.Datetime(
        string='Meeting Date',
        related='meeting_id.start',
        store=True
    )
    
    # === Computed Fields ===
    can_employee_edit = fields.Boolean(
        string='Can Employee Edit',
        compute='_compute_can_edit'
    )
    can_manager_edit = fields.Boolean(
        string='Can Manager Edit',
        compute='_compute_can_edit'
    )
    is_employee = fields.Boolean(
        string='Is Current User Employee',
        compute='_compute_is_users'
    )
    is_manager = fields.Boolean(
        string='Is Current User Manager',
        compute='_compute_is_users'
    )
    
    # === Constraints ===
    @api.constrains('appraisal_period_start', 'appraisal_period_end')
    def _check_dates(self):
        for appraisal in self:
            if appraisal.appraisal_period_start > appraisal.appraisal_period_end:
                raise ValidationError(_('Period start date must be before end date.'))
    
    @api.constrains('date_close')
    def _check_deadline(self):
        for appraisal in self:
            if appraisal.date_close < fields.Date.today():
                raise ValidationError(_('Deadline cannot be in the past.'))
    
    # === Compute Methods ===
    @api.depends('employee_id', 'date_close')
    def _compute_display_name(self):
        for appraisal in self:
            if appraisal.employee_id and appraisal.date_close:
                appraisal.display_name = f"{appraisal.employee_id.name} - {appraisal.date_close.strftime('%Y-%m')}"
            else:
                appraisal.display_name = _('New Appraisal')
    
    @api.depends('employee_id', 'employee_id.parent_id')
    def _compute_manager_id(self):
        for appraisal in self:
            appraisal.manager_id = appraisal.employee_id.parent_id
    
    @api.depends('final_rating')
    def _compute_rating_score(self):
        for appraisal in self:
            if appraisal.final_rating:
                appraisal.rating_score = float(appraisal.final_rating)
            else:
                appraisal.rating_score = 0.0
    
    def _compute_goal_count(self):
        for appraisal in self:
            appraisal.goal_count = len(appraisal.goal_ids)
    
    @api.depends('goal_ids', 'goal_ids.progress')
    def _compute_goals_completion(self):
        for appraisal in self:
            goals = appraisal.goal_ids
            if goals:
                appraisal.goals_completion = sum(goals.mapped('progress')) / len(goals)
            else:
                appraisal.goals_completion = 0.0
    
    def _compute_skill_count(self):
        for appraisal in self:
            appraisal.skill_count = len(appraisal.skill_ids)
    
    @api.depends('skill_ids', 'skill_ids.rating')
    def _compute_skills_average(self):
        for appraisal in self:
            skills = appraisal.skill_ids.filtered(lambda s: s.rating)
            if skills:
                ratings = [float(s.rating) for s in skills if s.rating]
                appraisal.skills_average = sum(ratings) / len(ratings) if ratings else 0.0
            else:
                appraisal.skills_average = 0.0
    
    def _compute_can_edit(self):
        for appraisal in self:
            user = self.env.user
            appraisal.can_employee_edit = (
                appraisal.employee_id.user_id == user and 
                appraisal.state in ['pending', 'employee_feedback']
            )
            appraisal.can_manager_edit = (
                appraisal.manager_id.user_id == user and 
                appraisal.state in ['manager_feedback']
            ) or user.has_group('hr_appraisal.group_appraisal_manager')
    
    def _compute_is_users(self):
        user = self.env.user
        for appraisal in self:
            appraisal.is_employee = appraisal.employee_id.user_id == user
            appraisal.is_manager = appraisal.manager_id.user_id == user
    
    # === CRUD Methods ===
    @api.model_create_multi
    def create(self, vals_list):
        appraisals = super().create(vals_list)
        for appraisal in appraisals:
            # Auto-populate skills from template
            if appraisal.template_id:
                appraisal._apply_template()
        return appraisals
    
    def write(self, vals):
        if 'template_id' in vals and vals['template_id']:
            old_template_ids = {a.id: a.template_id.id for a in self}
        res = super().write(vals)
        if 'template_id' in vals and vals['template_id']:
            for appraisal in self:
                if old_template_ids.get(appraisal.id) != vals['template_id']:
                    appraisal._apply_template()
        return res
    
    def _apply_template(self):
        """Apply template skills to appraisal"""
        self.ensure_one()
        if not self.template_id:
            return
        
        # Clear existing skills if applying new template
        self.skill_ids.unlink()
        
        # Create skills from template
        for template_skill in self.template_id.skill_ids:
            self.env['hr.appraisal.skill'].create({
                'appraisal_id': self.id,
                'name': template_skill.name,
                'description': template_skill.description,
                'category': template_skill.category,
                'weight': template_skill.weight,
            })
    
    # === Action Methods ===
    def action_confirm(self):
        """Confirm the appraisal and notify employee"""
        for appraisal in self:
            if appraisal.state != 'new':
                raise UserError(_('Only new appraisals can be confirmed.'))
            appraisal.write({'state': 'pending'})
            appraisal._send_notification('confirm')
        return True
    
    def action_start_employee_feedback(self):
        """Move to employee feedback phase"""
        for appraisal in self:
            if appraisal.state != 'pending':
                raise UserError(_('Appraisal must be confirmed first.'))
            appraisal.write({'state': 'employee_feedback'})
            appraisal._send_notification('employee_feedback')
        return True
    
    def action_submit_employee_feedback(self):
        """Employee submits their self-assessment"""
        for appraisal in self:
            if appraisal.state != 'employee_feedback':
                raise UserError(_('Appraisal is not in employee feedback phase.'))
            appraisal.write({
                'state': 'manager_feedback',
                'employee_feedback_date': fields.Datetime.now(),
            })
            appraisal._send_notification('manager_feedback')
        return True
    
    def action_submit_manager_feedback(self):
        """Manager submits their assessment"""
        for appraisal in self:
            if appraisal.state != 'manager_feedback':
                raise UserError(_('Appraisal is not in manager feedback phase.'))
            if not appraisal.manager_rating:
                raise UserError(_('Please provide a manager rating before submitting.'))
            appraisal.write({
                'state': 'done',
                'manager_feedback_date': fields.Datetime.now(),
                'final_rating': appraisal.manager_rating,
            })
            appraisal._send_notification('done')
        return True
    
    def action_cancel(self):
        """Cancel the appraisal"""
        self.write({'state': 'cancel'})
        return True
    
    def action_reset_to_draft(self):
        """Reset appraisal to draft/new state"""
        self.write({'state': 'new'})
        return True
    
    def action_schedule_meeting(self):
        """Open wizard to schedule appraisal meeting"""
        self.ensure_one()
        return {
            'name': _('Schedule Appraisal Meeting'),
            'type': 'ir.actions.act_window',
            'res_model': 'calendar.event',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_name': _('Appraisal Meeting: %s') % self.employee_id.name,
                'default_partner_ids': [(6, 0, [
                    self.employee_id.user_id.partner_id.id,
                    self.manager_id.user_id.partner_id.id,
                ] if self.employee_id.user_id and self.manager_id.user_id else [])],
                'default_description': _('Performance appraisal discussion for period %s to %s') % (
                    self.appraisal_period_start, self.appraisal_period_end
                ),
            },
        }
    
    def action_view_goals(self):
        """View goals for this appraisal"""
        self.ensure_one()
        return {
            'name': _('Goals'),
            'type': 'ir.actions.act_window',
            'res_model': 'hr.appraisal.goal',
            'view_mode': 'list,form',
            'domain': [('appraisal_id', '=', self.id)],
            'context': {'default_appraisal_id': self.id},
        }
    
    def action_view_skills(self):
        """View skills assessment for this appraisal"""
        self.ensure_one()
        return {
            'name': _('Skills Assessment'),
            'type': 'ir.actions.act_window',
            'res_model': 'hr.appraisal.skill',
            'view_mode': 'list,form',
            'domain': [('appraisal_id', '=', self.id)],
            'context': {'default_appraisal_id': self.id},
        }
    
    def action_add_note(self):
        """Add a meeting note"""
        self.ensure_one()
        return {
            'name': _('Add Note'),
            'type': 'ir.actions.act_window',
            'res_model': 'hr.appraisal.note',
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_appraisal_id': self.id},
        }
    
    # === Notification Methods ===
    def _send_notification(self, notification_type):
        """Send email notification based on type"""
        self.ensure_one()
        template_ref = {
            'confirm': 'hr_appraisal.mail_template_appraisal_confirm',
            'employee_feedback': 'hr_appraisal.mail_template_employee_feedback',
            'manager_feedback': 'hr_appraisal.mail_template_manager_feedback',
            'done': 'hr_appraisal.mail_template_appraisal_done',
        }
        
        template_xmlid = template_ref.get(notification_type)
        if template_xmlid:
            template = self.env.ref(template_xmlid, raise_if_not_found=False)
            if template:
                template.send_mail(self.id, force_send=True)
    
    # === Cron Methods ===
    @api.model
    def _cron_send_reminders(self):
        """Send reminders for upcoming deadlines"""
        reminder_days = self.env.company.appraisal_reminder_days or 7
        deadline = fields.Date.today() + timedelta(days=reminder_days)
        
        appraisals = self.search([
            ('state', 'in', ['pending', 'employee_feedback', 'manager_feedback']),
            ('date_close', '=', deadline),
        ])
        
        for appraisal in appraisals:
            template = self.env.ref('hr_appraisal.mail_template_appraisal_reminder', raise_if_not_found=False)
            if template:
                template.send_mail(appraisal.id, force_send=True)
        
        return True
    
    @api.model
    def _cron_create_periodic_appraisals(self):
        """Create periodic appraisals based on company settings"""
        companies = self.env['res.company'].search([
            ('appraisal_auto_create', '=', True)
        ])
        
        for company in companies:
            frequency = company.appraisal_frequency or 365
            last_check = fields.Date.today() - timedelta(days=frequency)
            
            employees = self.env['hr.employee'].search([
                ('company_id', '=', company.id),
                ('active', '=', True),
            ])
            
            for employee in employees:
                # Check if employee already has recent appraisal
                existing = self.search([
                    ('employee_id', '=', employee.id),
                    ('date_close', '>=', last_check),
                ], limit=1)
                
                if not existing:
                    self.create({
                        'employee_id': employee.id,
                        'company_id': company.id,
                        'date_close': fields.Date.today() + timedelta(days=30),
                    })
        
        return True
