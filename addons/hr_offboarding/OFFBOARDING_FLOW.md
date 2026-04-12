# Offboarding and Asset Recovery Business Logic (`hr_offboarding`)

The `hr_offboarding` module manages the complete employee resignation workflow, focusing heavily on generating electronic recovery minutes, calculating asset damages, and automating system wrap-ups (like archiving the employee profile).

## 1. Initiation and Asset Listing
- **Start the Process**: When an employee resigns or is terminated, the Branch Manager initiates an Offboarding Record. 
- **Automated Asset Listing**: The system automatically pulls every company asset currently assigned to that specific employee (`hr.asset` in 'assigned' state) and populates the Asset Return Checklist.

## 2. Notification and Communication
- **Return Request Alert**: A single click sends an automated email to the resigning employee. The email includes a tabulated list of all assets they must return, their monetary values, and the hard deadline for hand-over.

## 3. Asset Recovery and Compensation
- **Inspection**: The employee hands over the assets to the Branch Manager, who logs the return status directly on the checklist for each item:
  - `Good Condition`: No further action required.
  - `Damaged`: Automatically calculates a 50% compensation penalty based on the asset's original value (modifiable).
  - `Missing`: Automatically demands 100% compensation for the asset's value. 
- **Financial Settlement**: The total required compensation is aggregated. This info is automatically highlighted for the accounting/payroll team to deduct from the final salary payout.

## 4. Digital Signatures and Minutes
- The system generates an official **Asset Recovery Minutes (Biên Bản Thu Hồi Tài Sản)** PDF document containing a full summary of the returned/missing items and compensation applied. It features three sign-off blocks (Employee, Manager, Director) for formal filing.

---

## 5. Important Notes & System Automations

**Prerequisites for Users**:
- Before initiating an offboarding process, you **must** assign assets to the employee via `Offboarding -> Assets -> Company Assets`. If no assets are assigned in the system, the recovery checklist will be empty.

**What the System Does Automatically**:
- **Final Approval Automation**: When the Director clicks the `Approve & Finalize` button:
    1.  The employee's profile is entirely **Archived** (`Active = False`).
    2.  The employee's active Employment Contract is moved to a **Closed** (`close`) state.
    3.  All assets checked as "Good Condition" are stripped from the employee and returned to the **Available** state in the inventory.
    4.  All returned/missing actions are permanently logged in the specific Asset's assignment history tab.
