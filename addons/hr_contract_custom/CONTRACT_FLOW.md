# Contract Business Logic (`hr_contract_custom`)

The `hr_contract_custom` module extends Odoo's contract management system to support a robust, multi-level approval workflow, an improved allowance structure, automated tracking mechanisms, and electronic signatures for digitized document handling.

## 1. Multi-tier Approval Workflow
All newly created or modified employment contracts follow a strict, linear approval hierarchy before becoming active ("Running"). This replaces Odoo's default open-state system.
- **Draft**: The contract is drafted by a lower-level HR administrator or Branch Manager. Allowances and base wages are laid out here.
- **Submitted**: The contract request is forwarded to the HR Manager.
- **HR Approval**: The HR Manager verifies the employee's assigned schedule, basic wage conditions, and compliance with internal protocols.
- **Director Approval**: Final approval is given by the Director. Upon approval, the contract is locked into an "Approved" state, and modifying the compensation details becomes restricted to authorized roles.

## 2. Allowance Structure Tracking
The default `hr_contract` model handles flat salary rates well, but this expansion adds specific monetary fields that deeply integrate with the `hr_payroll_custom` module:
- **Position Allowance (`position_allowance`)**: Represents the monetary bonus designated for management or specialized operations (e.g., specific store heads).
- **Job Allowance (`job_allowance`)**: Represents Task-based allowances given to staff carrying out extra responsibilities outside their standard job description.
The Payroll module retrieves these values directly when calculating the `Total Allowance` per month.

## 3. Automated Expiry & Transition Management
- **Expiry Alerts via Cron jobs**: A daily scheduled automation script checks the `date_end` of all "Running" contracts. If a contract is approaching expiration (e.g., 30 days prior), an internal notification and/or email is sent to the HR Department and the Branch Manager to begin contract renewal talks.

## 4. Electronic Confirmation
- Employees are able to digitally review their contract details and append electronic confirmations (either checking a confirmation field or through a simplified portal view depending on configuration) indicating their acceptance of the contract terms directly in the system, maintaining digital compliance.

---

## 5. Important Notes & System Automations

**Prerequisites for Users**:
- Ensure correctly categorized Employee profiles limit contract creation visibility explicitly to HR personnel.

**What the System Does Automatically**:
- **Cron Job Checks**: Without user intervention, an automated cron job scripts daily scans across all explicitly "Running" contracts. If the script matches the `date_end` variable within the 30-day proximity buffer, the system automatically emits a notification alerting configured HR officers.
- **Access Hierarchy Restrictions**: Odoo automatically blocks editing attempts on an "Approved" contract if the trying user simply holds standard permission subsets. Revisions necessitate specific manager roles or creating a renewed contract instance.
