# Attendance Business Logic (`hr_attendance_custom`)

The `hr_attendance_custom` module extends Odoo's default Attendance app to support a robust check-in/out process using employee PINs at a kiosk, supplemented by automated attendance anomaly detection and a correction approval workflow.

## 1. Daily Check-in/Check-out Process
- **Preparation**: The attendance system (Kiosk mode) runs continuously on a computer/tablet stationed at the store entrance or office.
- **Starting a Shift (Check-in)**:
  - An employee arrives, selects their name from the list, or enters their employee ID.
  - The employee inputs their personal PIN code for authentication.
  - Upon successful PIN validation, the system records the exact `check_in` time.
- **Ending a Shift (Check-out)**:
  - Before leaving, the employee repeats the authentication process.
  - Clicking the Check-out button records the `check_out` time and calculates the total duration worked.

## 2. Automated Status Flagging and Validation
Once a check-out is recorded, the system compares the actual worked hours against the employee's assigned working schedule (`resource.calendar`) and calculates exactly how many minutes the employee was late or left early.

The attendance record is then assigned one of the following statuses dynamically:
*   **Normal**: Arrived and left within the acceptable grace periods.
*   **Late In**: Arrived after the scheduled start time plus the configured `late_threshold_minutes`.
*   **Early Out**: Left before the scheduled end time minus the configured `early_threshold_minutes`.
*   **Late In & Early Out**: Violated both arrival and departure thresholds.
*   **Forgot Checkout**: A cron job runs nightly (e.g., 01:00 AM) to automatically flag any open check-ins from the previous day.
*   **Manual**: Check-ins created directly by a manager rather than through the Kiosk.
*   **Corrected**: System-flagged when an attendance record is generated or modified via an approved Correction Request.

## 3. Attendance Correction Requests
Since direct modification of attendance records by employees is disabled, any mistakes (e.g., forgot to check out, power outage at kiosk, invalid flags) must go through the correction workflow:
1.  **Draft**: The employee submits a Correction Request indicating the exact date, the expected Check-in and Check-out times, and a detailed reason.
2.  **Submitted**: The request is sent to the manager. An automated email is triggered notifying the manager of a pending request.
3.  **Approved/Rejected**: The manager reviews the request.
    - If **Approved**, the system automatically creates or updates the target `hr.attendance` record with the requested timelines and sets the status flag to `Corrected`. The employee receives an email notification.
    - If **Rejected**, the attendance record remains unchanged, and the employee is notified regarding the reason.

## 4. Configuration Controls
Administrators can dictate leniency rules via the generic settings (`Settings -> Attendance Custom`):
- `late_threshold_minutes`: Grace period (in minutes) for being late before the system flags the arrival.
- `early_threshold_minutes`: Grace period (in minutes) for leaving early before the system flags the departure.

---

## 5. Important Notes & System Automations

**Prerequisites for Users**:
- Employees MUST have a Working Schedule (`resource.calendar`) properly assigned to their contract/profile. If no schedule is found, the system cannot calculate if they are "Late" or "Early".
- `attendance_pin` MUST be configured in the employee's HR Settings for them to use the Kiosk.

**What the System Does Automatically**:
- **Nightly Forgot-Checkout Scan (Cron Job)**: Every night at 01:00 AM, the system runs an automated script (`ir.cron`). It scans for any attendance records from the previous day that do not have a `check_out` time and automatically flags them as `Forgot Checkout`.
- **Auto-Applying Corrections**: When a manager clicks `Approve` on an Attendance Correction Request, the system does not require manual data entry. It automatically targets the specific attendance record in question, forcibly edits the `check_in`/`check_out` times to match the requested times, and permanently changes the record's state to `Corrected`.
