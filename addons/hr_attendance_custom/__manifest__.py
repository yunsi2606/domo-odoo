# -*- coding: utf-8 -*-
{
    'name': 'HR Attendance Custom',
    'version': '18.0.1.0.0',
    'category': 'Human Resources/Attendances',
    'summary': 'Quản lý Chấm công - Kiosk, Phân loại trạng thái, Yêu cầu sửa công',
    'description': """
HR Attendance Custom Module for Odoo 18

Module quản lý chấm công nâng cao, bao gồm:

Tính năng chính:
* **Kiosk Chấm công**: Màn hình chấm công hiển thị danh sách nhân viên theo ca,
  hỗ trợ đăng nhập bằng mã PIN hoặc tài khoản cá nhân.

* **Phân loại trạng thái chấm công**: Tự động gắn cờ đi trễ, về sớm, quên check-out
  dựa trên lịch làm việc của nhân viên.

* **Yêu cầu sửa công (Attendance Correction)**: Nhân viên gửi yêu cầu sửa công
  khi quên check-in/check-out. Quản lý xem xét và phê duyệt.

* **Dashboard & Báo cáo**: Tổng hợp số liệu chấm công theo ngày/tháng,
  theo dõi tỷ lệ đúng giờ và tuân thủ ca làm việc.

Quy trình:
1. Nhân viên check-in (chọn tên → nhập PIN/mật khẩu)
2. Hệ thống ghi nhận thời gian, tính toán so với ca
3. Nhân viên check-out → tính số giờ thực tế
4. Phát hiện lỗi → nhân viên gửi yêu cầu sửa công
5. Quản lý phê duyệt → dữ liệu được cập nhật
    """,
    'author': 'FORHER',
    'website': '',
    'depends': [
        'hr',
        'hr_attendance',
        'resource',
        'mail',
    ],
    'data': [
        # Security
        'security/hr_attendance_custom_security.xml',
        'security/ir.model.access.csv',
        # Data
        'data/sequence_data.xml',
        'data/mail_template_data.xml',
        # Views
        'views/hr_attendance_views.xml',
        'views/attendance_correction_views.xml',
        'views/res_config_settings_views.xml',
        'views/hr_attendance_custom_menus.xml',
    ],
    'demo': [],
    'assets': {
        'web.assets_backend': [
            'hr_attendance_custom/static/src/css/attendance.css',
        ],
    },
    'installable': True,
    'application': False,
    'auto_install': False,
    'license': 'LGPL-3',
}
