# Employee Profiling Business Logic (`hr_employee_custom`)

The `hr_employee_custom` module extends the standard Odoo employee directory. It transforms an employee's basic profile into a central node that connects directly with HR operations (Contracts, Attendance, and Payroll).

## 1. Core Profile Details and Organization
- **Hierarchical Structuring**: Organizes employees into Branches, Departments, and specific Job Titles. This defines logical reporting lines and simplifies permission matrices (e.g., Branch Manager vs. Department Head).
- **Personal and Work Information Consolidation**: Fields include full name, contact information, emergency contacts, banking details, and comprehensive HR settings (Timezone, Work Schedule).

## 2. Integrated Points for Payroll and Attendance
This module injects specific dependencies into `hr.employee` necessary for smooth downstream HR processes:

### a) Kiosk & Attendance Integration
- **PIN Authorization**: Introduces a secure `attendance_pin` field restricted strictly to HR Managers and the employee. This PIN is mandatory for Kiosk check-in/out procedures in the custom Attendance module.
- **Access to the Correction Workflow**: Links `Correction Request Counts` directly to the employee's profile to alert management dynamically.

### b) Payroll Integration
- **Tax Dependencies**: Tracks the explicit `Number of Dependents` (`num_dependents`), applying precise Personal Income Tax (PIT) exemption rules per dependent (e.g., 4.4 million VND deduction each).
- **Performance Rating**: Integrates a monthly `ABC Rating` field evaluated by managers (A, B, C). This value automatically translates into structured financial bonuses within the Payroll computational generation process.
- **Sales Record Connections**: A relationship mapped precisely back to imported or logged Shift-based Sales, ensuring correct `Hot Bonus` and `Livestream Bonus` evaluations.

## 3. Onboarding & Offboarding State Tracking
- The system registers when an employee is actively working or dismissed.
- Inactive personnel profiles disable corresponding authentication properties (disallowing PIN and Attendance usages) and cease contract generation parameters.

---

## 4. Important Notes & System Automations

**Prerequisites for Users**:
- Managers must ensure the employee profile is tied accurately to a configured `User` account if backend Odoo access is required. Mere inclusion in `hr.employee` does NOT grant system access.
- `attendance_pin` must be uniquely set up; duplicates might compromise kiosk check-in tracking.

**What the System Does Automatically**:
- **Cross-module Data Propagation**: Once `num_dependents` or `abc_rating` is modified on the Employee profile, the subsequent generation of an `hr.payslip.custom` record instantaneously pulls these updated figures without needing any sync action.
- **Auto-Archiving via Offboarding**: The Employee's `Active` toggle is automatically set to `False` (thus archiving the employee) immediately upon a Director clicking "Approve & Finalize" within the connected `hr.offboarding` document. No manual HR data cleanup is needed.
