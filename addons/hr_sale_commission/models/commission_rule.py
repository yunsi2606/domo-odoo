# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.exceptions import ValidationError


class CommissionRule(models.Model):
    """Tiered commission rules."""
    _name = 'hr.commission.rule'
    _description = 'Commission Rule'
    _order = 'priority desc, id'

    name = fields.Char(string='Rule Name', required=True)
    min_order_count = fields.Integer(string='Minimum Orders', default=0, required=True)
    min_revenue = fields.Float(string='Minimum Revenue', digits='Product Price', default=0.0, required=True)
    commission_rate = fields.Float(string='Commission Rate (%)', digits=(5, 2), default=0.0, required=True)
    priority = fields.Integer(string='Priority', default=10, required=True,
                              help='Higher priority rules are applied first when multiple match.')
    active = fields.Boolean(string='Active', default=True)
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company)
    notes = fields.Text(string='Notes')

    @api.constrains('commission_rate')
    def _check_commission_rate(self):
        for rule in self:
            if rule.commission_rate < 0 or rule.commission_rate > 100:
                raise ValidationError('Commission rate must be between 0 and 100.')

    @api.constrains('min_order_count')
    def _check_min_order_count(self):
        for rule in self:
            if rule.min_order_count < 0:
                raise ValidationError('Minimum order count cannot be negative.')

    @api.constrains('min_revenue')
    def _check_min_revenue(self):
        for rule in self:
            if rule.min_revenue < 0:
                raise ValidationError('Minimum revenue cannot be negative.')

    @api.model
    def get_matching_rule(self, order_count, total_revenue, company_id=None):
        """Return the highest-priority rule matching the given counts."""
        domain = [
            ('active', '=', True),
            ('min_order_count', '<=', order_count),
            ('min_revenue', '<=', total_revenue),
        ]
        if company_id:
            domain.extend(['|', ('company_id', '=', False), ('company_id', '=', company_id)])
        
        return self.search(domain, limit=1) or False
