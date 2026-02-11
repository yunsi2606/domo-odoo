# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.exceptions import UserError, ValidationError


class CommissionRecord(models.Model):
    """Monthly commission summary for each employee."""
    _name = 'hr.commission.record'
    _description = 'Commission Record'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'year desc, month desc, employee_id'
    _rec_name = 'display_name'

    MONTH_SELECTION = [
        ('1', 'January'), ('2', 'February'), ('3', 'March'), ('4', 'April'),
        ('5', 'May'), ('6', 'June'), ('7', 'July'), ('8', 'August'),
        ('9', 'September'), ('10', 'October'), ('11', 'November'), ('12', 'December'),
    ]

    STATE_SELECTION = [
        ('draft', 'Draft'),
        ('confirmed', 'Confirmed'),
        ('locked', 'Locked'),
    ]

    display_name = fields.Char(string='Name', compute='_compute_display_name', store=True)
    employee_id = fields.Many2one('hr.employee', string='Employee', required=True, ondelete='restrict', index=True)
    user_id = fields.Many2one('res.users', string='User', related='employee_id.user_id', store=True, readonly=True)
    month = fields.Selection(selection=MONTH_SELECTION, string='Month', required=True, index=True)
    year = fields.Integer(string='Year', required=True, index=True)
    
    total_orders = fields.Integer(string='Total Orders', compute='_compute_totals', store=True)
    total_revenue = fields.Float(string='Total Revenue', digits='Product Price', compute='_compute_totals', store=True)
    line_ids = fields.One2many('hr.commission.line', 'commission_record_id', string='Commission Lines')
    
    rule_id = fields.Many2one('hr.commission.rule', string='Applied Rule', readonly=True)
    commission_rate = fields.Float(string='Commission Rate (%)', digits=(5, 2), readonly=True)
    commission_amount = fields.Float(string='Commission Amount', digits='Product Price', readonly=True)
    
    state = fields.Selection(selection=STATE_SELECTION, string='Status', default='draft', required=True, tracking=True)
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company, required=True)
    currency_id = fields.Many2one('res.currency', string='Currency', related='company_id.currency_id', store=True)
    notes = fields.Text(string='Notes')

    _sql_constraints = [
        ('unique_employee_month_year', 'UNIQUE(employee_id, month, year, company_id)',
         'A commission record already exists for this employee in this month!'),
    ]

    @api.constrains('year')
    def _check_year(self):
        for record in self:
            if record.year < 2000 or record.year > 2100:
                raise ValidationError('Year must be between 2000 and 2100.')

    @api.depends('employee_id', 'month', 'year')
    def _compute_display_name(self):
        month_names = dict(self.MONTH_SELECTION)
        for record in self:
            if record.employee_id and record.month and record.year:
                record.display_name = f"{record.employee_id.name} - {month_names.get(record.month, '')} {record.year}"
            else:
                record.display_name = "New Commission Record"

    @api.depends('line_ids', 'line_ids.order_amount')
    def _compute_totals(self):
        for record in self:
            record.total_orders = len(record.line_ids)
            record.total_revenue = sum(record.line_ids.mapped('order_amount'))

    def action_confirm(self):
        """Confirm record and calc commission."""
        for record in self:
            if record.state != 'draft':
                raise UserError('Only draft records can be confirmed.')
            record._calculate_commission()
            record.state = 'confirmed'

    def action_lock(self):
        """Lock (mark as paid)."""
        for record in self:
            if record.state != 'confirmed':
                raise UserError('Only confirmed records can be locked.')
            record.state = 'locked'

    def action_reset_to_draft(self):
        """Back to draft."""
        for record in self:
            if record.state == 'locked':
                raise UserError('Locked records cannot be reset to draft.')
            record.write({'state': 'draft', 'rule_id': False, 'commission_rate': 0.0, 'commission_amount': 0.0})

    def action_recalculate(self):
        """Re-run commission calc (draft only)."""
        for record in self:
            if record.state != 'draft':
                raise UserError('Only draft records can be recalculated.')
            record._calculate_commission()

    def _calculate_commission(self):
        """Apply best matching rule to compute commission."""
        self.ensure_one()
        rule = self.env['hr.commission.rule'].get_matching_rule(
            order_count=self.total_orders,
            total_revenue=self.total_revenue,
            company_id=self.company_id.id
        )
        if rule:
            self.write({
                'rule_id': rule.id,
                'commission_rate': rule.commission_rate,
                'commission_amount': self.total_revenue * (rule.commission_rate / 100.0)
            })
        else:
            self.write({'rule_id': False, 'commission_rate': 0.0, 'commission_amount': 0.0})

    @api.model
    def get_or_create_record(self, employee_id, month, year, company_id=None):
        """Get existing record or create new one for the period."""
        if not company_id:
            company_id = self.env.company.id
        
        record = self.search([
            ('employee_id', '=', employee_id),
            ('month', '=', str(month)),
            ('year', '=', year),
            ('company_id', '=', company_id),
        ], limit=1)
        
        if not record:
            record = self.create({
                'employee_id': employee_id,
                'month': str(month),
                'year': year,
                'company_id': company_id,
                'state': 'draft',
            })
        return record
