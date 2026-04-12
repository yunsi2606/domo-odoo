# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError
from datetime import datetime, timedelta
import pytz


class HrAttendance(models.Model):
    """
    Mở rộng hr.attendance để thêm:
    - Phân loại trạng thái: đi trễ, về sớm, quên check-out
    - Liên kết với ca làm việc (resource.calendar.attendance)
    - Lý do vắng mặt / ghi chú
    - Phân biệt nguồn chấm công: kiosk, manual, correction
    """
    _inherit = 'hr.attendance'

    # ──────────────────────────────────────────────────────────────
    # Status Flags — Phân loại trạng thái chấm công
    # ──────────────────────────────────────────────────────────────
    attendance_status = fields.Selection([
        ('normal', 'Normal'),
        ('late_in', 'Late Check-in'),
        ('early_out', 'Early Check-out'),
        ('late_in_early_out', 'Late & Early'),
        ('forgot_checkout', 'Forgot Check-out'),
        ('manual', 'Manual Entry'),
        ('corrected', 'Corrected'),
    ], string='Attendance Status',
       compute='_compute_attendance_status',
       store=True,
       tracking=True,
       help='Phân loại trạng thái chấm công tự động')

    late_minutes = fields.Float(
        string='Late (minutes)',
        compute='_compute_late_minutes',
        store=True,
        help='Số phút đi trễ so với giờ vào ca',
    )
    early_out_minutes = fields.Float(
        string='Early Out (minutes)',
        compute='_compute_early_out_minutes',
        store=True,
        help='Số phút về sớm so với giờ kết thúc ca',
    )

    # ──────────────────────────────────────────────────────────────
    # Work Schedule Link — Liên kết ca làm việc
    # ──────────────────────────────────────────────────────────────
    work_schedule_shift = fields.Char(
        string='Shift',
        compute='_compute_work_schedule_shift',
        store=True,
        help='Ca làm việc dự kiến trong ngày',
    )
    planned_check_in = fields.Datetime(
        string='Planned Check-in',
        compute='_compute_planned_times',
        store=True,
        help='Giờ vào ca theo lịch',
    )
    planned_check_out = fields.Datetime(
        string='Planned Check-out',
        compute='_compute_planned_times',
        store=True,
        help='Giờ ra ca theo lịch',
    )
    planned_hours = fields.Float(
        string='Planned Hours',
        compute='_compute_planned_times',
        store=True,
        help='Số giờ làm việc dự kiến theo ca',
    )

    # ──────────────────────────────────────────────────────────────
    # Source & Notes
    # ──────────────────────────────────────────────────────────────
    source = fields.Selection([
        ('kiosk', 'Kiosk'),
        ('mobile', 'Mobile'),
        ('manual', 'Manual (Manager)'),
        ('correction', 'Correction Request'),
    ], string='Source', default='kiosk', tracking=True,
       help='Nguồn gốc dữ liệu chấm công')

    note = fields.Text(string='Note', help='Ghi chú thêm về bản ghi chấm công')

    # ──────────────────────────────────────────────────────────────
    # Correction Request Link
    # ──────────────────────────────────────────────────────────────
    correction_id = fields.Many2one(
        'hr.attendance.correction',
        string='Correction Request',
        readonly=True,
        help='Yêu cầu sửa công liên quan (nếu có)',
    )

    # ──────────────────────────────────────────────────────────────
    # Compute: Planned Times from Work Schedule
    # ──────────────────────────────────────────────────────────────
    @api.depends('employee_id', 'check_in')
    def _compute_planned_times(self):
        for record in self:
            record.planned_check_in = False
            record.planned_check_out = False
            record.planned_hours = 0.0
            if not record.employee_id or not record.check_in:
                continue

            employee = record.employee_id
            resource_calendar = employee.resource_calendar_id
            if not resource_calendar:
                continue

            # Lấy timezone của công ty
            tz = pytz.timezone(resource_calendar.tz or 'UTC')
            check_in_local = record.check_in.astimezone(tz)
            weekday = check_in_local.weekday()  # 0=Monday, 6=Sunday

            # Tìm ca làm việc trong ngày theo weekday
            day_shifts = resource_calendar.attendance_ids.filtered(
                lambda a: int(a.dayofweek) == weekday
            )
            if not day_shifts:
                continue

            # Lấy ca đầu tiên phù hợp (có thể có sáng/chiều)
            # Giờ vào = giờ nhỏ nhất, giờ ra = giờ lớn nhất
            min_hour_from = min(day_shifts.mapped('hour_from'))
            max_hour_to = max(day_shifts.mapped('hour_to'))
            planned_date = check_in_local.date()

            def hours_to_datetime(date, hours_float, tz):
                h = int(hours_float)
                m = int(round((hours_float - h) * 60))
                naive = datetime(date.year, date.month, date.day, h, m, 0)
                aware = tz.localize(naive)
                return aware.astimezone(pytz.utc).replace(tzinfo=None)

            record.planned_check_in = hours_to_datetime(planned_date, min_hour_from, tz)
            record.planned_check_out = hours_to_datetime(planned_date, max_hour_to, tz)
            record.planned_hours = max_hour_to - min_hour_from

    @api.depends('employee_id', 'check_in')
    def _compute_work_schedule_shift(self):
        for record in self:
            record.work_schedule_shift = ''
            if not record.employee_id or not record.check_in:
                continue
            cal = record.employee_id.resource_calendar_id
            if not cal:
                continue
            tz = pytz.timezone(cal.tz or 'UTC')
            check_in_local = record.check_in.astimezone(tz)
            weekday = check_in_local.weekday()
            day_shifts = cal.attendance_ids.filtered(
                lambda a: int(a.dayofweek) == weekday
            )
            if day_shifts:
                shifts_str = ', '.join(
                    f"{s.name or 'Shift'} ({_hour_to_str(s.hour_from)}-{_hour_to_str(s.hour_to)})"
                    for s in day_shifts
                )
                record.work_schedule_shift = shifts_str

    # ──────────────────────────────────────────────────────────────
    # Compute: Late / Early Out Minutes
    # ──────────────────────────────────────────────────────────────
    @api.depends('check_in', 'planned_check_in')
    def _compute_late_minutes(self):
        for record in self:
            record.late_minutes = 0.0
            if record.check_in and record.planned_check_in:
                diff = (record.check_in - record.planned_check_in).total_seconds() / 60
                record.late_minutes = max(0.0, diff)

    @api.depends('check_out', 'planned_check_out')
    def _compute_early_out_minutes(self):
        for record in self:
            record.early_out_minutes = 0.0
            if record.check_out and record.planned_check_out:
                diff = (record.planned_check_out - record.check_out).total_seconds() / 60
                record.early_out_minutes = max(0.0, diff)

    # ──────────────────────────────────────────────────────────────
    # Compute: Attendance Status
    # ──────────────────────────────────────────────────────────────
    @api.depends(
        'late_minutes', 'early_out_minutes',
        'check_out', 'source',
    )
    def _compute_attendance_status(self):
        # Ngưỡng đi trễ / về sớm (phút)
        late_threshold = self.env['ir.config_parameter'].sudo().get_param(
            'hr_attendance_custom.late_threshold_minutes', default='5'
        )
        early_threshold = self.env['ir.config_parameter'].sudo().get_param(
            'hr_attendance_custom.early_threshold_minutes', default='5'
        )
        late_threshold = float(late_threshold)
        early_threshold = float(early_threshold)

        for record in self:
            if record.source == 'correction':
                record.attendance_status = 'corrected'
                continue
            if record.source == 'manual':
                record.attendance_status = 'manual'
                continue

            is_late = record.late_minutes > late_threshold
            is_early_out = record.early_out_minutes > early_threshold
            forgot_checkout = not record.check_out

            if forgot_checkout:
                record.attendance_status = 'forgot_checkout'
            elif is_late and is_early_out:
                record.attendance_status = 'late_in_early_out'
            elif is_late:
                record.attendance_status = 'late_in'
            elif is_early_out:
                record.attendance_status = 'early_out'
            else:
                record.attendance_status = 'normal'

    # ──────────────────────────────────────────────────────────────
    # Cron: Auto-flag forgot check-out
    # ──────────────────────────────────────────────────────────────
    @api.model
    def _cron_flag_forgot_checkout(self):
        """
        Chạy hàng ngày để gắn cờ 'forgot_checkout' cho các bản ghi
        không có check-out từ ngày hôm trước trở về trước.
        """
        yesterday_end = fields.Datetime.now().replace(
            hour=0, minute=0, second=0, microsecond=0
        )
        unchecked = self.search([
            ('check_out', '=', False),
            ('check_in', '<', yesterday_end),
            ('attendance_status', '!=', 'forgot_checkout'),
        ])
        if unchecked:
            unchecked.write({'attendance_status': 'forgot_checkout'})
        return True

    # ──────────────────────────────────────────────────────────────
    # Action: Open Correction Request
    # ──────────────────────────────────────────────────────────────
    def action_request_correction(self):
        """Mở form tạo yêu cầu sửa công từ bản ghi chấm công"""
        self.ensure_one()
        return {
            'name': _('Request Attendance Correction'),
            'type': 'ir.actions.act_window',
            'res_model': 'hr.attendance.correction',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_employee_id': self.employee_id.id,
                'default_attendance_id': self.id,
                'default_date': self.check_in.date() if self.check_in else fields.Date.today(),
                'default_actual_check_in': self.check_in,
                'default_actual_check_out': self.check_out,
            },
        }


# ──────────────────────────────────────────────────────────────
# Utility
# ──────────────────────────────────────────────────────────────
def _hour_to_str(hour_float):
    h = int(hour_float)
    m = int(round((hour_float - h) * 60))
    return f"{h:02d}:{m:02d}"
