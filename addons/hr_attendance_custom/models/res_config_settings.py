# -*- coding: utf-8 -*-
from odoo import api, fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    # ──────────────────────────────────────────────────────────────
    # Ngưỡng đi trễ / về sớm
    # ──────────────────────────────────────────────────────────────
    late_threshold_minutes = fields.Integer(
        string='Late Check-in Threshold (minutes)',
        default=5,
        config_parameter='hr_attendance_custom.late_threshold_minutes',
        help='Số phút tối đa được coi là "đúng giờ" khi vào ca. '
             'Vượt quá ngưỡng này sẽ bị gắn cờ "Đi trễ".',
    )
    early_threshold_minutes = fields.Integer(
        string='Early Check-out Threshold (minutes)',
        default=5,
        config_parameter='hr_attendance_custom.early_threshold_minutes',
        help='Số phút ra trước giờ kết thúc ca được coi là "về sớm".',
    )

    # ──────────────────────────────────────────────────────────────
    # Tự động đánh dấu quên check-out
    # ──────────────────────────────────────────────────────────────
    attendance_forgot_checkout_auto_flag = fields.Boolean(
        string='Auto-flag Forgot Check-out',
        default=True,
        config_parameter='hr_attendance_custom.forgot_checkout_auto_flag',
        help='Tự động gắn cờ "Quên check-out" cho những bản ghi không có giờ ra.',
    )

    # ──────────────────────────────────────────────────────────────
    # PIN cho Kiosk
    # ──────────────────────────────────────────────────────────────
    kiosk_require_pin = fields.Boolean(
        string='Require PIN for Kiosk',
        default=True,
        config_parameter='hr_attendance_custom.kiosk_require_pin',
        help='Bắt buộc nhập mã PIN khi chấm công tại kiosk.',
    )
