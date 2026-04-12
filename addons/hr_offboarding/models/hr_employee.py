# -*- coding: utf-8 -*-
from odoo import fields, models


class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    asset_ids = fields.One2many('hr.asset', 'assigned_employee_id',
                                string='Assigned Assets',
                                domain=[('state', '=', 'assigned')])
    assigned_asset_count = fields.Integer(compute='_compute_asset_count')
    offboarding_ids = fields.One2many('hr.offboarding', 'employee_id', 'Offboarding Records')

    def _compute_asset_count(self):
        for e in self:
            e.assigned_asset_count = self.env['hr.asset'].search_count([
                ('assigned_employee_id', '=', e.id),
                ('state', '=', 'assigned'),
            ])

    def action_view_assets(self):
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'hr.asset',
            'view_mode': 'list,form',
            'domain': [('assigned_employee_id', '=', self.id)],
            'context': {'default_assigned_employee_id': self.id},
        }

    def action_start_offboarding(self):
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'hr.offboarding',
            'view_mode': 'form',
            'context': {'default_employee_id': self.id},
        }
