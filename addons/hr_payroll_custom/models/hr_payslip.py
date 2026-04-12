# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError
from datetime import date, datetime, timedelta
from dateutil.relativedelta import relativedelta


class HrPayslip(models.Model):
    _name = 'hr.payslip.custom'
    _description = 'Payslip'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'date_from desc, id desc'
    _rec_name = 'name'

    name = fields.Char('Payslip Reference', required=True, copy=False,
                       default=lambda self: _('New'), tracking=True)
    employee_id = fields.Many2one('hr.employee', 'Employee', required=True, tracking=True)
    contract_id = fields.Many2one('hr.contract', 'Contract', tracking=True)
    department_id = fields.Many2one(related='employee_id.department_id', store=True)
    job_id = fields.Many2one(related='employee_id.job_id', store=True)
    company_id = fields.Many2one('res.company', default=lambda s: s.env.company)

    date_from = fields.Date('From', required=True, tracking=True)
    date_to = fields.Date('To', required=True, tracking=True)

    state = fields.Selection([
        ('draft', 'Draft'),
        ('computed', 'Computed'),
        ('confirmed', 'Confirmed'),
        ('done', 'Done'),
        ('cancelled', 'Cancelled'),
    ], default='draft', tracking=True)

    # Input fields (some from attendance, some manual)
    actual_work_days = fields.Float('Actual Work Days', tracking=True)
    valid_leave_days = fields.Float('Valid Leave Days (≤4)', tracking=True)
    ot_hours_normal = fields.Float('OT Hours (Normal)', tracking=True)
    ot_hours_holiday = fields.Float('OT Hours (Holiday/Tet)', tracking=True)

    # Contract values (snapshot)
    wage = fields.Monetary('Monthly Wage', currency_field='currency_id', tracking=True)
    currency_id = fields.Many2one('res.currency', default=lambda s: s.env.company.currency_id)
    daily_wage = fields.Monetary('Daily Wage', compute='_compute_daily_wage', store=True)

    # Allowances
    position_allowance = fields.Monetary('Position Allowance')
    job_allowance = fields.Monetary('Job Allowance')
    allowance_reduction_pct = fields.Float('Allowance Reduction (%)', default=0.0,
                                           help='% giảm phụ cấp (0-100), giám đốc quyết định')

    # Bonuses
    hot_bonus = fields.Monetary('Hot Bonus (Sales)', compute='_compute_hot_bonus', store=True)
    livestream_bonus = fields.Monetary('Livestream Bonus', compute='_compute_livestream_bonus', store=True)
    abc_rating = fields.Selection([('A', 'A (+500K)'), ('B', 'B (+200K)'), ('C', 'C (0)')],
                                  related='employee_id.abc_rating', readonly=True)
    abc_bonus = fields.Monetary('ABC Bonus', compute='_compute_abc_bonus', store=True)

    # Deductions
    advance_amount = fields.Monetary('Advance Deduction')
    penalty_total = fields.Monetary('Total Penalties', compute='_compute_penalty_total', store=True)
    num_dependents = fields.Integer('Dependents', related='employee_id.num_dependents', readonly=True)

    # Computed salary lines
    basic_salary = fields.Monetary('Basic Salary', compute='_compute_basic_salary', store=True)
    ot_salary = fields.Monetary('OT Salary', compute='_compute_ot_salary', store=True)
    total_allowance = fields.Monetary('Total Allowance', compute='_compute_total_allowance', store=True)
    gross_salary = fields.Monetary('Gross Salary', compute='_compute_gross', store=True)

    # Social insurance
    si_employee = fields.Monetary('BHXH/BHYT/BHTN (Employee 10.5%)',
                                  compute='_compute_insurance', store=True)
    si_employer = fields.Monetary('BHXH/BHYT/BHTN (Employer 21.5%)',
                                  compute='_compute_insurance', store=True)

    # PIT
    taxable_income = fields.Monetary('Taxable Income', compute='_compute_pit', store=True)
    pit_amount = fields.Monetary('PIT (Thuế TNCN)', compute='_compute_pit', store=True)
    personal_deduction = fields.Monetary(
        'Personal Deduction (11M)', compute='_compute_pit', store=True,
        help='Giảm trừ bản thân: 11,000,000đ/tháng')
    dependent_deduction_total = fields.Monetary(
        'Dependent Deduction', compute='_compute_pit', store=True,
        help='Giảm trừ người phụ thuộc: số người × 4,400,000đ')

    net_salary = fields.Monetary('Net Salary', compute='_compute_net', store=True)

    line_ids = fields.One2many('hr.payslip.custom.line', 'payslip_id', 'Salary Lines')
    note = fields.Text('Notes')

    # Compute

    @api.depends('wage')
    def _compute_daily_wage(self):
        for r in self:
            r.daily_wage = r.wage / 26.0 if r.wage else 0.0

    def _get_standard_work_days(self, date_from, date_to):
        if not date_from or not date_to:
            return 26.0
        days = 0
        current = date_from
        while current <= date_to:
            if current.weekday() != 6:  # 6 is Sunday
                days += 1
            current += timedelta(days=1)
        return float(days)

    @api.depends('wage', 'actual_work_days', 'valid_leave_days', 'date_from', 'date_to')
    def _compute_basic_salary(self):
        """Lương cơ bản = Lương hợp đồng / Số ngày công chuẩn trong kỳ * (Ngày công thực tế + Phép hợp lệ <= chuẩn)"""
        for r in self:
            wage = r.wage or 0.0
            std_days = r._get_standard_work_days(r.date_from, r.date_to)
            daily_wage = wage / std_days if std_days else 0.0
            
            leave_days = min(r.valid_leave_days or 0.0, 4.0)
            total_paid_days = min((r.actual_work_days or 0.0) + leave_days, std_days)
            
            r.basic_salary = total_paid_days * daily_wage

    @api.depends('ot_hours_normal', 'ot_hours_holiday')
    def _compute_ot_salary(self):
        OT_RATE = 27000.0
        for r in self:
            r.ot_salary = r.ot_hours_normal * OT_RATE + r.ot_hours_holiday * OT_RATE * 3

    @api.depends('position_allowance', 'job_allowance', 'allowance_reduction_pct')
    def _compute_total_allowance(self):
        for r in self:
            raw = r.position_allowance + r.job_allowance
            r.total_allowance = raw * (1 - r.allowance_reduction_pct / 100.0)

    @api.depends('employee_id', 'date_from', 'date_to')
    def _compute_hot_bonus(self):
        SalesRecord = self.env['hr.sales.record']
        for r in self:
            if not r.employee_id or not r.date_from:
                r.hot_bonus = 0.0
                continue
            records = SalesRecord.search([
                ('employee_id', '=', r.employee_id.id),
                ('date', '>=', r.date_from),
                ('date', '<=', r.date_to or r.date_from),
            ])
            total = 0.0
            for rec in records:
                # Dùng total_sales - field lưu thực trong DB
                amount = rec.total_sales or 0.0
                if amount >= 10_000_000:
                    total += 200_000
                elif amount >= 7_500_000:
                    total += 150_000
            r.hot_bonus = total

    @api.depends('employee_id', 'date_from', 'date_to')
    def _compute_livestream_bonus(self):
        SalesRecord = self.env['hr.sales.record']
        for r in self:
            if not r.employee_id or not r.date_from:
                r.livestream_bonus = 0.0
                continue
            # Mỗi ca trên 50 sản phẩm → thưởng 200K
            records = SalesRecord.search([
                ('employee_id', '=', r.employee_id.id),
                ('date', '>=', r.date_from),
                ('date', '<=', r.date_to or r.date_from),
                ('total_products', '>', 50),
            ])
            r.livestream_bonus = len(records) * 200_000

    @api.depends('abc_rating')
    def _compute_abc_bonus(self):
        map_ = {'A': 500_000, 'B': 200_000, 'C': 0}
        for r in self:
            r.abc_bonus = map_.get(r.abc_rating, 0)

    @api.depends('employee_id', 'date_from', 'date_to')
    def _compute_penalty_total(self):
        for r in self:
            penalties = self.env['hr.payslip.penalty'].search([
                ('employee_id', '=', r.employee_id.id),
                ('date', '>=', r.date_from or date.today()),
                ('date', '<=', r.date_to or date.today()),
                ('state', '=', 'approved'),
                ('payslip_id', '=', False),
            ])
            r.penalty_total = sum(penalties.mapped('amount'))
            # Link penalties to this payslip
            penalties.write({'payslip_id': r.id})

    @api.depends('basic_salary', 'ot_salary', 'total_allowance',
                 'hot_bonus', 'livestream_bonus', 'abc_bonus')
    def _compute_gross(self):
        for r in self:
            r.gross_salary = (r.basic_salary + r.ot_salary + r.total_allowance
                              + r.hot_bonus + r.livestream_bonus + r.abc_bonus)

    @api.depends('basic_salary')
    def _compute_insurance(self):
        EMP_RATE = 0.105   # 10.5%
        EMP_RATE_CO = 0.215  # 21.5%
        for r in self:
            base = r.basic_salary
            r.si_employee = base * EMP_RATE
            r.si_employer = base * EMP_RATE_CO

    @api.depends('gross_salary', 'si_employee', 'num_dependents')
    def _compute_pit(self):
        PERSONAL_DEDUCT = 11_000_000
        DEPENDENT_DEDUCT = 4_400_000
        for r in self:
            num_dep = r.num_dependents or 0
            personal = PERSONAL_DEDUCT
            dep_deduct = num_dep * DEPENDENT_DEDUCT
            deduct = personal + dep_deduct
            taxable = max(0, r.gross_salary - r.si_employee - deduct)
            r.personal_deduction = personal
            r.dependent_deduction_total = dep_deduct
            r.taxable_income = taxable
            r.pit_amount = _calc_pit(taxable)

    @api.depends('gross_salary', 'si_employee', 'pit_amount',
                 'advance_amount', 'penalty_total')
    def _compute_net(self):
        for r in self:
            r.net_salary = (r.gross_salary - r.si_employee - r.pit_amount
                            - r.advance_amount - r.penalty_total)

    # CRUD

    @api.constrains('actual_work_days', 'valid_leave_days', 'date_from', 'date_to')
    def _check_work_days(self):
        for r in self:
            std_days = r._get_standard_work_days(r.date_from, r.date_to)
            total = (r.actual_work_days or 0.0) + (r.valid_leave_days or 0.0)
            # Add small epsilon to prevent floating point errors
            if total > std_days + 0.001:
                raise ValidationError(f"Tổng số ngày đi làm thực tế ({r.actual_work_days}) và ngày phép hợp lệ ({r.valid_leave_days}) là {total} ngày.\nCon số này vượt quá số ngày công chuẩn của kỳ lương ({std_days} ngày). Tuyệt đối không được nhập vượt mức!")

    # Fields that affect salary breakdown lines
    _LINE_TRIGGER_FIELDS = {
        'wage', 'actual_work_days', 'valid_leave_days',
        'ot_hours_normal', 'ot_hours_holiday',
        'position_allowance', 'job_allowance', 'allowance_reduction_pct',
        'advance_amount',
    }

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', _('New')) == _('New'):
                vals['name'] = self.env['ir.sequence'].next_by_code('hr.payslip.custom') or _('New')
        records = super().create(vals_list)
        records._generate_lines()
        return records

    def write(self, vals):
        res = super().write(vals)
        # Regenerate lines whenever any key input field changes
        if self._LINE_TRIGGER_FIELDS & set(vals.keys()):
            self._generate_lines()
        return res

    @api.onchange('employee_id', 'date_from', 'date_to')
    def _onchange_employee(self):
        if not self.employee_id:
            return
        emp = self.employee_id
        contract = self.env['hr.contract'].search([
            ('employee_id', '=', emp.id),
            ('state', 'in', ('open', 'close')),
            ('date_start', '<=', self.date_from or date.today()),
            '|', ('date_end', '=', False),
            ('date_end', '>=', self.date_from or date.today()),
        ], limit=1)
        if contract:
            self.contract_id = contract.id
            self.wage = contract.wage
            self.position_allowance = contract.position_allowance
            self.job_allowance = contract.job_allowance
        self.num_dependents = emp.num_dependents
        # Auto-compute attendance and generate lines immediately
        self._compute_attendance_data()
        self._onchange_generate_lines()

    @api.onchange('actual_work_days', 'valid_leave_days', 'ot_hours_normal', 'ot_hours_holiday',
                  'position_allowance', 'job_allowance', 'allowance_reduction_pct',
                  'advance_amount', 'wage', 'num_dependents')
    def _onchange_generate_lines(self):
        """Tính toán tất cả giá trị nội tuyến và cập nhật bảng Salary Breakdown ngay lập tức"""
        OT_RATE = 27000.0
        EMP_INS_RATE = 0.105
        PERSONAL_DEDUCT = 11_000_000
        DEPENDENT_DEDUCT = 4_400_000
        ABC_MAP = {'A': 500_000, 'B': 200_000, 'C': 0}

        for r in self:
            std_days = r._get_standard_work_days(r.date_from, r.date_to)
            daily_wage = (r.wage or 0.0) / std_days if std_days else 0.0
            
            leave_days = min(r.valid_leave_days or 0.0, 4.0)
            total_paid_days = min((r.actual_work_days or 0.0) + leave_days, std_days)
            basic = total_paid_days * daily_wage

            # OT
            ot = (r.ot_hours_normal or 0.0) * OT_RATE + (r.ot_hours_holiday or 0.0) * OT_RATE * 3

            # Allowances
            raw_allowance = (r.position_allowance or 0.0) + (r.job_allowance or 0.0)
            total_allow = raw_allowance * (1 - (r.allowance_reduction_pct or 0.0) / 100.0)

            # Bonuses - tính thẳng từ Sales Records, không đọc từ cached computed field
            hot_bonus = 0.0
            live_bonus = 0.0
            if r.employee_id and r.date_from:
                sales_records = self.env['hr.sales.record'].search([
                    ('employee_id', '=', r.employee_id.id),
                    ('date', '>=', r.date_from),
                    ('date', '<=', r.date_to or r.date_from),
                ])
                for rec in sales_records:
                    amount = rec.total_sales or 0.0
                    # Thưởng nóng theo doanh số/ca
                    if amount >= 10_000_000:
                        hot_bonus += 200_000
                    elif amount >= 7_500_000:
                        hot_bonus += 150_000
                    # Thưởng livestream: trên 50 sản phẩm/ca
                    if (rec.total_products or 0) > 50:
                        live_bonus += 200_000
            # ABC bonus: nhập thủ công cuối tháng
            abc_bonus = ABC_MAP.get(r.abc_rating, 0)

            # Gross = Lương cơ bản + OT + Phụ cấp (sau giảm) + Các khoản thưởng
            gross = basic + ot + total_allow + hot_bonus + live_bonus + abc_bonus

            # Bảo hiểm: 10.5% trên lương cơ bản (không tính OT, thưởng theo luật VN)
            si_emp = basic * EMP_INS_RATE

            # PIT với giảm trừ gia cảnh
            num_dep = (r.employee_id.num_dependents or 0) if r.employee_id else (r.num_dependents or 0)
            personal = PERSONAL_DEDUCT
            dep_deduct = num_dep * DEPENDENT_DEDUCT
            deduct = personal + dep_deduct
            taxable = max(0.0, gross - si_emp - deduct)
            pit = _calc_pit(taxable)

            # Penalty & Advance
            penalty = r.penalty_total or 0.0
            advance = r.advance_amount or 0.0

            # Net
            net = gross - si_emp - pit - advance - penalty

            # Update display fields
            r.daily_wage = daily_wage
            r.basic_salary = basic
            r.ot_salary = ot
            r.total_allowance = total_allow
            r.gross_salary = gross
            r.si_employee = si_emp
            r.personal_deduction = personal
            r.dependent_deduction_total = dep_deduct
            r.taxable_income = taxable
            r.pit_amount = pit
            r.net_salary = net

            # Build Salary Breakdown lines
            lines = [
                ('BASIC', 'Lương cơ bản', basic),
                ('OT', 'Lương làm thêm giờ', ot),
                ('ALLOWANCE', 'Phụ cấp', total_allow),
                ('HOT_BONUS', 'Thưởng nóng doanh số', hot_bonus),
                ('LIVE_BONUS', 'Thưởng livestream', live_bonus),
                ('ABC_BONUS', 'Thưởng ABC', abc_bonus),
                ('SI_EMP', 'Trừ BHXH/BHYT/BHTN (NV)', -si_emp),
                ('PIT', 'Thuế TNCN', -pit),
                ('ADVANCE', 'Tạm ứng', -advance),
                ('PENALTY', 'Phạt', -penalty),
            ]
            r.line_ids = [(5, 0, 0)] + [(0, 0, {
                'code': code, 'name': name, 'amount': amount,
            }) for code, name, amount in lines]

    def action_compute(self):
        self._compute_attendance_data()
        self._generate_lines()
        self.write({'state': 'computed'})

    def _compute_attendance_data(self):
        """Pull actual work days from hr.attendance"""
        for r in self:
            if not r.date_from or not r.date_to:
                continue
            attendances = self.env['hr.attendance'].search([
                ('employee_id', '=', r.employee_id.id),
                ('check_in', '>=', datetime.combine(r.date_from, datetime.min.time())),
                ('check_in', '<=', datetime.combine(r.date_to, datetime.max.time())),
                ('check_out', '!=', False),
            ])
            # Count unique dates worked
            work_dates = set(a.check_in.date() for a in attendances)
            r.actual_work_days = len(work_dates)
            total_ot = sum(
                max(0, (a.worked_hours - 8)) for a in attendances
            )
            r.ot_hours_normal = total_ot

    def _generate_lines(self):
        """Tự động sinh chi tiết tính lương khi bấm Compute"""
        self._onchange_generate_lines()

    def action_confirm(self):
        self.write({'state': 'confirmed'})

    def action_done(self):
        self.write({'state': 'done'})

    def action_cancel(self):
        self.write({'state': 'cancelled'})

    def action_reset_draft(self):
        self.write({'state': 'draft'})

    def action_print_payslip(self):
        return self.env.ref('hr_payroll_custom.action_report_payslip').report_action(self)


class HrPayslipLine(models.Model):
    _name = 'hr.payslip.custom.line'
    _description = 'Payslip Line'
    _order = 'payslip_id, code'

    payslip_id = fields.Many2one('hr.payslip.custom', ondelete='cascade')
    code = fields.Char('Code', required=True)
    name = fields.Char('Description', required=True)
    amount = fields.Monetary('Amount', currency_field='currency_id')
    currency_id = fields.Many2one(related='payslip_id.currency_id')


# PIT Calculator

def _calc_pit(taxable: float) -> float:
    """Vietnam progressive PIT (Thuế TNCN lũy tiến từng phần)"""
    brackets = [
        (5_000_000, 0.05),
        (5_000_000, 0.10),
        (8_000_000, 0.15),
        (14_000_000, 0.20),
        (20_000_000, 0.25),
        (28_000_000, 0.30),
        (float('inf'), 0.35),
    ]
    tax = 0.0
    remaining = taxable
    for limit, rate in brackets:
        chunk = min(remaining, limit)
        tax += chunk * rate
        remaining -= chunk
        if remaining <= 0:
            break
    return tax
