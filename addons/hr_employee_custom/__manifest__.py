# -*- coding: utf-8 -*-
{
    'name': 'HR Employee Profile Management',
    'version': '18.0.1.0.0',
    'category': 'Human Resources',
    'summary': 'Quản lý Hồ sơ Nhân viên - Tập trung, Chuẩn hóa, Phân quyền theo cấp bậc',
    'description': """
HR Employee Profile Management Module for Odoo 18

Module quản lý hồ sơ nhân viên toàn diện, bao gồm:

Tính năng chính:
* **Mã nhân viên (Employee ID)**: Mỗi nhân viên có một mã duy nhất tự động (EMP/0001).

* **Chuẩn hóa hồ sơ**: Thông tin cá nhân (CMND/CCCD, địa chỉ, liên hệ),
  thông tin công việc (chức danh, chi nhánh, phòng ban), thông tin hợp đồng,
  thông tin ngân hàng và giấy tờ liên quan.

* **Quản lý chi nhánh**: Phân biệt chi nhánh và phòng ban trong cùng model hr.department.

* **Lịch sử vị trí**: Theo dõi mọi thay đổi phòng ban/chức danh theo thời gian.

* **Quản lý giấy tờ**: Lưu trữ và theo dõi hạn hạn các tài liệu như CMND, bằng lái,
  bằng cấp, BHXH.

* **Phân quyền 3 cấp**:
  - Nhân viên: xem/sửa thông tin cá nhân của mình.
  - Quản lý chi nhánh: xem toàn bộ hồ sơ nhân viên thuộc chi nhánh.
  - Giám đốc: toàn quyền xem và phê duyệt.

* **Kết nối liên quy trình**: Liên kết trực tiếp với tuyển dụng (hr_recruitment_custom),
  chấm công, và bảng lương.
    """,
    'author': 'FORHER',
    'website': '',
    'depends': [
        'hr',
        'hr_contract',
        'mail',
        'hr_recruitment_custom',
    ],
    'data': [
        # Security
        'security/hr_employee_custom_security.xml',
        'security/ir.model.access.csv',
        # Data
        'data/sequence_data.xml',
        # Views
        'views/hr_department_views.xml',
        'views/hr_employee_views.xml',
        'views/hr_employee_document_views.xml',
        'views/hr_position_history_views.xml',
        'views/hr_employee_custom_menus.xml',
    ],
    'demo': [],
    'assets': {
        'web.assets_backend': [
            'hr_employee_custom/static/src/css/employee.css',
        ],
    },
    'installable': True,
    'application': False,
    'auto_install': False,
    'license': 'LGPL-3',
}
