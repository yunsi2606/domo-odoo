# -*- coding: utf-8 -*-
from odoo import api, fields, models, _


class HrAppraisalTemplate(models.Model):
    """
    HR Appraisal Template - Predefined templates for appraisals
    """
    _name = 'hr.appraisal.template'
    _description = 'Appraisal Template'
    _order = 'name'

    name = fields.Char(
        string='Template Name',
        required=True
    )
    description = fields.Text(
        string='Description'
    )
    active = fields.Boolean(
        default=True
    )
    company_id = fields.Many2one(
        'res.company',
        string='Company',
        required=True,
        default=lambda self: self.env.company
    )
    
    # Skills to be evaluated
    skill_ids = fields.One2many(
        'hr.appraisal.template.skill',
        'template_id',
        string='Skills to Evaluate'
    )
    
    # Default goals
    goal_ids = fields.One2many(
        'hr.appraisal.template.goal',
        'template_id',
        string='Default Goals'
    )
    
    # Settings
    employee_self_assessment = fields.Boolean(
        string='Employee Self-Assessment',
        default=True,
        help='Allow employee self-assessment'
    )
    skills_assessment = fields.Boolean(
        string='Skills Assessment',
        default=True,
        help='Include skills assessment'
    )
    goals_tracking = fields.Boolean(
        string='Goals Tracking',
        default=True,
        help='Include goals tracking'
    )
    
    appraisal_count = fields.Integer(
        string='Appraisals',
        compute='_compute_appraisal_count'
    )
    
    def _compute_appraisal_count(self):
        for template in self:
            template.appraisal_count = self.env['hr.appraisal'].search_count([
                ('template_id', '=', template.id)
            ])
    
    def action_view_appraisals(self):
        """View appraisals using this template"""
        self.ensure_one()
        return {
            'name': _('Appraisals'),
            'type': 'ir.actions.act_window',
            'res_model': 'hr.appraisal',
            'view_mode': 'list,form',
            'domain': [('template_id', '=', self.id)],
        }


class HrAppraisalTemplateSkill(models.Model):
    """
    Template Skills - Skills included in template
    """
    _name = 'hr.appraisal.template.skill'
    _description = 'Template Skill'
    _order = 'category, sequence, name'

    name = fields.Char(
        string='Skill',
        required=True
    )
    description = fields.Text(
        string='Description'
    )
    template_id = fields.Many2one(
        'hr.appraisal.template',
        string='Template',
        required=True,
        ondelete='cascade'
    )
    category = fields.Selection([
        ('technical', 'Technical Skills'),
        ('communication', 'Communication'),
        ('leadership', 'Leadership'),
        ('teamwork', 'Teamwork'),
        ('problem_solving', 'Problem Solving'),
        ('time_management', 'Time Management'),
        ('adaptability', 'Adaptability'),
        ('creativity', 'Creativity'),
        ('other', 'Other'),
    ], string='Category', default='technical', required=True)
    weight = fields.Float(
        string='Weight (%)',
        default=100.0
    )
    sequence = fields.Integer(
        string='Sequence',
        default=10
    )


class HrAppraisalTemplateGoal(models.Model):
    """
    Template Goals - Default goals included in template
    """
    _name = 'hr.appraisal.template.goal'
    _description = 'Template Goal'
    _order = 'sequence, name'

    name = fields.Char(
        string='Goal',
        required=True
    )
    description = fields.Html(
        string='Description'
    )
    template_id = fields.Many2one(
        'hr.appraisal.template',
        string='Template',
        required=True,
        ondelete='cascade'
    )
    category = fields.Selection([
        ('performance', 'Performance'),
        ('development', 'Development'),
        ('project', 'Project'),
        ('learning', 'Learning'),
        ('other', 'Other'),
    ], string='Category', default='performance', required=True)
    weight = fields.Float(
        string='Weight (%)',
        default=100.0
    )
    sequence = fields.Integer(
        string='Sequence',
        default=10
    )
