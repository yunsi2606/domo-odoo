# -*- coding: utf-8 -*-
{
    'name': 'HR Recruitment Management',
    'version': '18.0.1.0.0',
    'category': 'Human Resources/Recruitment',
    'summary': 'Quản lý Quy trình Tuyển dụng - Yêu cầu, Ứng viên, Phỏng vấn, Thư mời nhận việc',
    'description': """
HR Recruitment Management Module for Odoo 18

Module quản lý quy trình tuyển dụng toàn diện, bao gồm:

Tính năng chính:
* **Yêu cầu tuyển dụng (Recruitment Request)**: Quản lý chi nhánh/trưởng bộ phận tạo yêu cầu tuyển dụng
  với đầy đủ thông tin vị trí, số lượng, mô tả công việc, yêu cầu kỹ năng, ngân sách lương.
  Hỗ trợ quy trình phê duyệt nhiều cấp.

* **Quản lý ứng viên (Applicant Management)**: Tập hợp hồ sơ ứng viên từ nhiều nguồn vào
  cơ sở dữ liệu thống nhất. Sàng lọc, tìm kiếm và phân loại theo kỹ năng, kinh nghiệm,
  vị trí ứng tuyển.

* **Quản lý phỏng vấn (Interview Management)**: Lên lịch phỏng vấn, gửi thư mời tự động
  cho ứng viên và người phỏng vấn. Chấm điểm và nhận xét đánh giá sau phỏng vấn.

* **Thư mời nhận việc (Offer Letter)**: Tạo và gửi thư mời nhận việc theo mẫu chuẩn.
  Theo dõi trạng thái thư mời (đã gửi, chấp nhận, từ chối) theo thời gian thực.

* **Chuyển đổi ứng viên thành nhân viên**: Khi ứng viên chấp nhận, tự động chuyển đổi
  hồ sơ ứng viên thành hồ sơ nhân viên mới, đảm bảo tính liền mạch dữ liệu.

Quy trình:
1. Tạo yêu cầu tuyển dụng → Phê duyệt
2. Đăng tin tuyển dụng → Thu thập hồ sơ ứng viên
3. Sàng lọc → Lên lịch phỏng vấn → Đánh giá
4. Gửi thư mời nhận việc → Ứng viên phản hồi
5. Chuyển đổi ứng viên thành nhân viên
    """,
    'author': 'FORHER',
    'website': '',
    'depends': [
        'hr',
        'hr_recruitment',
        'mail',
        'calendar',
    ],
    'data': [
        # Security
        'security/hr_recruitment_custom_security.xml',
        'security/ir.model.access.csv',
        # Data
        'data/recruitment_stage_data.xml',
        'data/mail_template_data.xml',
        'data/sequence_data.xml',
        # Views
        'views/recruitment_request_views.xml',
        'views/hr_applicant_views.xml',
        'views/interview_views.xml',
        'views/offer_letter_views.xml',
        'views/recruitment_source_views.xml',
        'views/hr_recruitment_custom_menus.xml',
        # Wizards
        'wizard/create_employee_wizard_views.xml',
    ],
    'demo': [],
    'assets': {
        'web.assets_backend': [
            'hr_recruitment_custom/static/src/css/recruitment.css',
        ],
    },
    'installable': True,
    'application': True,
    'auto_install': False,
    'license': 'LGPL-3',
}
