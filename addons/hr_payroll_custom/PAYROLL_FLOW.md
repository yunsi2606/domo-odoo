# Payroll Business Logic (`hr_payroll_custom`)

The `hr_payroll_custom` module for Odoo 18 Community automates the payroll processing by integrating data from the Attendances (`hr_attendance`), Contracts (`hr_contract`), and Sales modules (or manually imported Excel files).

## 1. Salary Components
*   **Basic Salary**: `(min(Actual Work Days, 26) + min(Valid Leave Days, 4)) × Daily Wage`
*   **Overtime (OT) Salary**: `(Normal OT Hours × 27,000 VND) + (Holiday OT Hours × 27,000 VND × 3)`
*   **Allowances**: Includes Position Allowance and Job Allowance (configured in the Employee Contract). Managers can apply a percentage reduction to the total allowance for poor performance.
*   **Sales Bonus (Hot Bonus)**: 
    *   Sales per shift $\geq$ 7.5 million VND: +150,000 VND
    *   Sales per shift $\geq$ 10 million VND: +200,000 VND
*   **Livestream Bonus**: Selling > 50 products per shift: +200,000 VND
*   **ABC Performance Rating**: Rated monthly by the manager. Grade A (+500k VND), B (+200k VND), C (No bonus).

## 2. Deductions & Taxes
*   **Social Insurances (BHXH, BHYT, BHTN)**: The system automatically deducts 10.5% of the basic salary from the employee and records 21.5% as the employer's contribution.
*   **Personal Income Tax (PIT)**: 
    *   Calculated based on the Vietnam 7-tier progressive tax rate.
    *   Exemptions: 11 million VND/month for the employee + (4.4 million VND × number of dependents).
*   **Advances & Penalties**: 
    *   **Penalties**: Handled via the Penalty form (`hr.payslip.penalty`) with an approval workflow (Manager Approval $\rightarrow$ Automatically deducted in the next payslip).
    *   **Advances**: Manually inputted as a direct deduction amount.

## 3. Execution Workflow
1.  **Data Preparation**:
    *   Accountants import shift-based sales data from Excel via the `hr.sales.import.wizard` (or enter it manually).
    *   Update employee ABC ratings and number of dependents.
    *   Managers approve any pending penalty requests.
2.  **Batch Payroll Generation**: 
    *   Use the `Generate Payslips` wizard to create draft payslips for a selected department or specific employees for the current period.
    *   The system uses the date range to pull actual "work days" and "OT hours" from the attendance records.
3.  **Review and Validation**:
    *   Accountants review the Draft payslips. Click `Compute Salary` to recalculate if manual overrides are made.
    *   Confirm and Mark as Done when the salary is paid.
4.  **Payslip Printing**:
    *   Export the Payslip PDF detailing all earnings, deductions, taxes, and net pay in a transparent format.

## 4. Access Rights
*   **Payroll User (Accountant)**: Can view/create payslips, import sales records, and propose penalty deductions.
*   **Payroll Manager (Director/Head of Dept)**: Can approve penalties, run batch payroll generation, and override critical system configurations.

---

## 5. Important Notes & System Automations

**Prerequisites for Users**:
- Employees MUST have an active (Running) employment contract with defined `wage`, `position_allowance`, and `job_allowance` configured.
- Employee profiles MUST have their `num_dependents` and `abc_rating` filled out accurately before running the monthly payslips to ensure PIT and Bonuses are aggregated accurately.

**What the System Does Automatically**:
- **Automatic Attendance Data Pull**: When generating Payslips (via wizard or manually), filling the `Date From` and `Date To` fields automatically queries the `hr.attendance` module to compute `Actual Work Days` and `OT Hours`.
- **Automatic Deductions**: Approved `Penalty` records within the date period are automatically aggregated and deducted into a `Total Penalty` line on the next generated payslip.
- **Tax & Insurance Calculations**: 10.5% default employee SI deduction and dynamic 7-Tier Personal Income Tax deduction thresholds are completely processed in the backend when the Compute Salary button is clicked.
