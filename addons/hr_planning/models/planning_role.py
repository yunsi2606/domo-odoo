# -*- coding: utf-8 -*-
from odoo import api, fields, models, _


class PlanningRole(models.Model):
    """
    Planning Role - Defines job roles/positions for shift planning
    e.g., Cashier, Cook, Waiter, Manager, etc.
    """
    _name = 'planning.role'
    _description = 'Planning Role'
    _order = 'sequence, name'

    name = fields.Char(
        string='Role Name',
        required=True,
        translate=True
    )
    sequence = fields.Integer(
        string='Sequence',
        default=10
    )
    color = fields.Integer(
        string='Color',
        default=0
    )
    active = fields.Boolean(
        string='Active',
        default=True
    )
    company_id = fields.Many2one(
        'res.company',
        string='Company',
        default=lambda self: self.env.company
    )
    
    # Resource related
    resource_ids = fields.Many2many(
        'hr.employee',
        'planning_role_employee_rel',
        'role_id',
        'employee_id',
        string='Employees with this Role',
        help='Employees that can be assigned to shifts with this role'
    )
    
    # Statistics
    slot_count = fields.Integer(
        string='Shift Count',
        compute='_compute_slot_count'
    )
    
    @api.depends('name')
    def _compute_slot_count(self):
        """Compute number of slots assigned to this role"""
        for role in self:
            role.slot_count = self.env['planning.slot'].search_count([
                ('role_id', '=', role.id)
            ])
    
    def action_view_slots(self):
        """Open view with all slots for this role"""
        self.ensure_one()
        return {
            'name': _('Shifts for %s', self.name),
            'type': 'ir.actions.act_window',
            'res_model': 'planning.slot',
            'view_mode': 'gantt,tree,form,calendar',
            'domain': [('role_id', '=', self.id)],
            'context': {'default_role_id': self.id},
        }

    _sql_constraints = [
        ('name_company_uniq', 'unique(name, company_id)', 
         'Role name must be unique per company!'),
    ]
