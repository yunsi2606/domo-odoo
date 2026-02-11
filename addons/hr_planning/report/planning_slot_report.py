# -*- coding: utf-8 -*-
from odoo import api, fields, models, tools


class PlanningSlotReport(models.Model):
    """
    Planning Slot Report - SQL View for advanced reporting
    """
    _name = 'planning.slot.report'
    _description = 'Planning Analysis Report'
    _auto = False
    _order = 'start_datetime desc'

    # Dimensions
    employee_id = fields.Many2one(
        'hr.employee',
        string='Employee',
        readonly=True
    )
    role_id = fields.Many2one(
        'planning.role',
        string='Role',
        readonly=True
    )
    department_id = fields.Many2one(
        'hr.department',
        string='Department',
        readonly=True
    )
    company_id = fields.Many2one(
        'res.company',
        string='Company',
        readonly=True
    )
    
    # Time dimensions
    start_datetime = fields.Datetime(
        string='Start Date',
        readonly=True
    )
    end_datetime = fields.Datetime(
        string='End Date',
        readonly=True
    )
    start_date = fields.Date(
        string='Date',
        readonly=True
    )
    
    # Status
    state = fields.Selection([
        ('draft', 'Draft'),
        ('published', 'Published'),
        ('done', 'Done'),
        ('cancel', 'Cancelled'),
    ], string='Status', readonly=True)
    
    # Measures
    allocated_hours = fields.Float(
        string='Allocated Hours',
        readonly=True
    )
    slot_count = fields.Integer(
        string='Shift Count',
        readonly=True
    )
    conflict_count = fields.Integer(
        string='Conflicts',
        readonly=True
    )
    
    def init(self):
        tools.drop_view_if_exists(self._cr, self._table)
        self._cr.execute("""
            CREATE OR REPLACE VIEW %s AS (
                SELECT
                    ps.id AS id,
                    ps.employee_id AS employee_id,
                    ps.role_id AS role_id,
                    e.department_id AS department_id,
                    ps.company_id AS company_id,
                    ps.start_datetime AS start_datetime,
                    ps.end_datetime AS end_datetime,
                    ps.start_datetime::date AS start_date,
                    ps.state AS state,
                    ps.allocated_hours AS allocated_hours,
                    1 AS slot_count,
                    CASE WHEN ps.has_conflict THEN 1 ELSE 0 END AS conflict_count
                FROM planning_slot ps
                LEFT JOIN hr_employee e ON ps.employee_id = e.id
                WHERE ps.active = TRUE
            )
        """ % self._table)
