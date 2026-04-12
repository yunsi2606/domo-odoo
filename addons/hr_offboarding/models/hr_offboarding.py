# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import UserError
from datetime import date, timedelta


class HrOffboarding(models.Model):
    _name = 'hr.offboarding'
    _description = 'Employee Offboarding & Asset Recovery'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'date_resign desc'

    name = fields.Char('Reference', copy=False, default=lambda s: _('New'), readonly=True)
    employee_id = fields.Many2one('hr.employee', 'Employee', required=True, tracking=True,
                                  domain=[('active', '=', True)])
    department_id = fields.Many2one(related='employee_id.department_id', store=True)
    branch_manager_id = fields.Many2one('hr.employee', 'Branch Manager', tracking=True)
    contract_id = fields.Many2one('hr.contract', 'Related Contract', tracking=True)
    company_id = fields.Many2one('res.company', default=lambda s: s.env.company)

    date_resign = fields.Date('Resignation Date', required=True, tracking=True)
    date_last_work = fields.Date('Last Working Day', required=True, tracking=True)
    date_asset_deadline = fields.Date('Asset Return Deadline', tracking=True,
                                      help='Deadline for employee to return all assets')
    resign_reason = fields.Selection([
        ('resignation', 'Resignation'),
        ('termination', 'Termination'),
        ('contract_end', 'Contract End'),
        ('other', 'Other'),
    ], string='Reason', required=True, default='resignation', tracking=True)
    resign_note = fields.Text('Notes')

    state = fields.Selection([
        ('draft', 'Draft'),
        ('notified', 'Notified'),
        ('in_progress', 'In Progress'),
        ('review', 'Pending Director Approval'),
        ('done', 'Completed'),
        ('cancelled', 'Cancelled'),
    ], default='draft', tracking=True)

    line_ids = fields.One2many('hr.offboarding.line', 'offboarding_id', 'Asset Checklist')

    # Summary stats
    total_assets = fields.Integer(compute='_compute_summary', store=True)
    returned_assets = fields.Integer(compute='_compute_summary', store=True)
    damaged_assets = fields.Integer(compute='_compute_summary', store=True)
    missing_assets = fields.Integer(compute='_compute_summary', store=True)
    compensation_amount = fields.Monetary('Compensation Amount', compute='_compute_summary',
                                          store=True, currency_field='currency_id',
                                          help='Total compensation required for damaged/missing assets')
    currency_id = fields.Many2one('res.currency', default=lambda s: s.env.company.currency_id)

    # Confirmation
    manager_confirmed = fields.Boolean('Manager Confirmed', tracking=True)
    director_approved_by = fields.Many2one('res.users', readonly=True)
    director_approved_date = fields.Date(readonly=True)
    minutes_signed = fields.Boolean('Minutes Signed', tracking=True,
                                    help='Physical or electronic signature confirmed')
    settlement_done = fields.Boolean('Financial Settlement Done', tracking=True)

    @api.depends('line_ids', 'line_ids.return_state', 'line_ids.compensation_amount')
    def _compute_summary(self):
        for r in self:
            lines = r.line_ids
            r.total_assets = len(lines)
            r.returned_assets = len(lines.filtered(lambda l: l.return_state == 'returned_ok'))
            r.damaged_assets = len(lines.filtered(lambda l: l.return_state == 'returned_damaged'))
            r.missing_assets = len(lines.filtered(lambda l: l.return_state == 'missing'))
            r.compensation_amount = sum(lines.filtered(
                lambda l: l.return_state in ('returned_damaged', 'missing')
            ).mapped('compensation_amount'))

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', _('New')) == _('New'):
                vals['name'] = self.env['ir.sequence'].next_by_code('hr.offboarding') or _('New')
        return super().create(vals_list)

    @api.onchange('employee_id')
    def _onchange_employee(self):
        if not self.employee_id:
            return
        # Auto-populate assigned assets
        assigned_assets = self.env['hr.asset'].search([
            ('assigned_employee_id', '=', self.employee_id.id),
            ('state', '=', 'assigned'),
        ])
        lines = [(5, 0, 0)]
        for asset in assigned_assets:
            lines.append((0, 0, {
                'asset_id': asset.id,
                'return_state': 'pending',
            }))
        self.line_ids = lines

        # Default contract
        contract = self.env['hr.contract'].search([
            ('employee_id', '=', self.employee_id.id),
            ('state', '=', 'open'),
        ], limit=1)
        if contract:
            self.contract_id = contract.id

    def action_notify(self):
        """Send notification to employee and manager"""
        self.ensure_one()
        if not self.line_ids:
            raise UserError('No assets to recover. Please add asset lines first.')
        template = self.env.ref('hr_offboarding.mail_template_asset_notify', raise_if_not_found=False)
        if template:
            template.send_mail(self.id, force_send=True)
        self.write({'state': 'notified'})

    def action_start(self):
        self.write({'state': 'in_progress'})

    def action_submit_review(self):
        """Submit to Director for final approval"""
        pending = self.line_ids.filtered(lambda l: l.return_state == 'pending')
        if pending:
            raise UserError(f'{len(pending)} asset(s) still pending. Please update their return status first.')
        self.write({'state': 'review'})
        template = self.env.ref('hr_offboarding.mail_template_director_review', raise_if_not_found=False)
        if template:
            template.send_mail(self.id, force_send=True)

    def action_director_approve(self):
        self.write({
            'state': 'done',
            'director_approved_by': self.env.user.id,
            'director_approved_date': date.today(),
        })
        # Mark all returned assets as available
        for line in self.line_ids.filtered(lambda l: l.return_state == 'returned_ok'):
            if line.asset_id:
                line.asset_id.action_return()
                # Log return in assignment history
                assignment = self.env['hr.asset.assignment'].search([
                    ('asset_id', '=', line.asset_id.id),
                    ('employee_id', '=', self.employee_id.id),
                    ('date_return', '=', False),
                ], limit=1)
                if assignment:
                    assignment.write({
                        'date_return': date.today(),
                        'return_condition': 'good',
                    })
        # Update damaged/missing assignments
        for line in self.line_ids.filtered(lambda l: l.return_state in ('returned_damaged', 'missing')):
            assignment = self.env['hr.asset.assignment'].search([
                ('asset_id', '=', line.asset_id.id),
                ('employee_id', '=', self.employee_id.id),
                ('date_return', '=', False),
            ], limit=1)
            if assignment:
                assignment.write({
                    'date_return': date.today(),
                    'return_condition': 'damaged' if line.return_state == 'returned_damaged' else 'lost',
                    'note': line.note,
                })
        # Update contract state
        if self.contract_id:
            self.contract_id.write({'state': 'close'})
        # Archive employee
        self.employee_id.write({'active': False})

    def action_cancel(self):
        self.write({'state': 'cancelled'})

    def action_reset_draft(self):
        self.write({'state': 'draft'})

    def action_print_minutes(self):
        return self.env.ref('hr_offboarding.action_report_offboarding').report_action(self)


class HrOffboardingLine(models.Model):
    _name = 'hr.offboarding.line'
    _description = 'Asset Return Checklist Line'

    offboarding_id = fields.Many2one('hr.offboarding', ondelete='cascade', required=True)
    asset_id = fields.Many2one('hr.asset', 'Asset', required=True,
                               domain="[('assigned_employee_id', '=', parent.employee_id)]")
    asset_code = fields.Char(related='asset_id.code', readonly=True)
    asset_value = fields.Monetary(related='asset_id.value', readonly=True, currency_field='currency_id')
    currency_id = fields.Many2one(related='asset_id.currency_id')

    return_state = fields.Selection([
        ('pending', 'Pending'),
        ('returned_ok', 'Returned – Good Condition'),
        ('returned_damaged', 'Returned – Damaged'),
        ('missing', 'Missing / Lost'),
    ], default='pending', required=True, tracking=True)

    compensation_amount = fields.Monetary('Compensation', currency_field='currency_id',
                                          help='Amount charged to employee for damaged/missing asset')
    compensation_type = fields.Selection([
        ('salary_deduction', 'Salary Deduction'),
        ('direct_payment', 'Direct Payment'),
    ], string='Compensation Method')
    note = fields.Char('Note / Remarks')
    received_date = fields.Date('Received Date')

    @api.onchange('return_state', 'asset_value')
    def _onchange_return_state(self):
        if self.return_state == 'returned_ok':
            self.compensation_amount = 0
        elif self.return_state == 'missing':
            self.compensation_amount = self.asset_value
        elif self.return_state == 'returned_damaged':
            self.compensation_amount = self.asset_value * 0.5  # default 50%, editable
