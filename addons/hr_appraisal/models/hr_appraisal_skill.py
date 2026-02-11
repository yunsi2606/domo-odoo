# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class HrAppraisalSkill(models.Model):
    """
    HR Appraisal Skill - Skills assessment for employee
    """
    _name = 'hr.appraisal.skill'
    _description = 'Appraisal Skill Assessment'
    _order = 'category, name'

    name = fields.Char(
        string='Skill',
        required=True
    )
    description = fields.Text(
        string='Description',
        help='Description of the skill'
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
    
    # Category
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
    
    # Ratings
    employee_rating = fields.Selection([
        ('1', '1 - Needs Development'),
        ('2', '2 - Below Expectations'),
        ('3', '3 - Meets Expectations'),
        ('4', '4 - Exceeds Expectations'),
        ('5', '5 - Expert Level'),
    ], string='Self Rating', help='Employee self-assessment of this skill')
    
    manager_rating = fields.Selection([
        ('1', '1 - Needs Development'),
        ('2', '2 - Below Expectations'),
        ('3', '3 - Meets Expectations'),
        ('4', '4 - Exceeds Expectations'),
        ('5', '5 - Expert Level'),
    ], string='Manager Rating', help='Manager assessment of this skill')
    
    rating = fields.Selection([
        ('1', '1 - Needs Development'),
        ('2', '2 - Below Expectations'),
        ('3', '3 - Meets Expectations'),
        ('4', '4 - Exceeds Expectations'),
        ('5', '5 - Expert Level'),
    ], string='Final Rating', help='Final agreed rating')
    
    rating_score = fields.Float(
        string='Rating Score',
        compute='_compute_rating_score',
        store=True
    )
    
    # Weight for calculation
    weight = fields.Float(
        string='Weight (%)',
        default=100.0,
        help='Weight of this skill in overall score'
    )
    
    # Comments
    employee_comment = fields.Text(
        string='Employee Comment'
    )
    manager_comment = fields.Text(
        string='Manager Comment'
    )
    
    # Previous rating for comparison
    previous_rating = fields.Selection([
        ('1', '1 - Needs Development'),
        ('2', '2 - Below Expectations'),
        ('3', '3 - Meets Expectations'),
        ('4', '4 - Exceeds Expectations'),
        ('5', '5 - Expert Level'),
    ], string='Previous Rating', readonly=True)
    
    improvement = fields.Float(
        string='Improvement',
        compute='_compute_improvement',
        store=True,
        help='Change from previous rating'
    )
    
    # Constraints
    @api.constrains('weight')
    def _check_weight(self):
        for skill in self:
            if skill.weight < 0 or skill.weight > 100:
                raise ValidationError(_('Weight must be between 0 and 100.'))
    
    # Compute Methods
    @api.depends('rating')
    def _compute_rating_score(self):
        for skill in self:
            if skill.rating:
                skill.rating_score = float(skill.rating)
            else:
                skill.rating_score = 0.0
    
    @api.depends('rating', 'previous_rating')
    def _compute_improvement(self):
        for skill in self:
            if skill.rating and skill.previous_rating:
                skill.improvement = float(skill.rating) - float(skill.previous_rating)
            else:
                skill.improvement = 0.0


class HrAppraisalSkillCategory(models.Model):
    """
    Skill Categories for organization
    """
    _name = 'hr.appraisal.skill.category'
    _description = 'Skill Category'
    _order = 'sequence, name'

    name = fields.Char(
        string='Category Name',
        required=True
    )
    sequence = fields.Integer(
        string='Sequence',
        default=10
    )
    description = fields.Text(
        string='Description'
    )
    color = fields.Integer(
        string='Color'
    )
    active = fields.Boolean(
        default=True
    )
