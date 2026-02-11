# HR Planning

Employee shift planning and scheduling for Odoo 18 Community Edition.

## Features

### Core Features
- **Planning Slots**: Create and manage work shifts with precise start/end times
- **Planning Roles**: Define job roles/positions (e.g., Cashier, Cook, Manager)
- **Shift Templates**: Pre-configured templates for common shifts (Morning, Day, Night, etc.)
- **Multi-View Support**: Gantt chart, Calendar, List, and Kanban views

### Scheduling Features
- **Drag & Drop**: Easily schedule and reschedule shifts in the Gantt view
- **Recurring Shifts**: Create repeating shift patterns (daily, weekly, monthly)
- **Copy Previous Week**: Quickly duplicate last week's schedule
- **Auto-Planning**: Automatically assign open shifts based on roles

### Conflict Management
- **Conflict Detection**: Automatic warning when employees have overlapping shifts
- **Time Off Integration**: Respects hr_holidays time off records
- **Availability Tracking**: View employee availability in real-time

### Communication
- **Publish & Notify**: Publish schedules and send email notifications
- **Employee Self-Service**: Employees can view their own schedules
- **Self-Unassign**: Allow employees to unassign themselves from shifts

### Reporting & Analytics
- **Planning Analysis**: Pivot and graph views for hours analysis
- **Utilization Tracking**: Monitor employee allocation percentages
- **PDF Reports**: Print schedule reports for employees

## Installation

1. Copy the `hr_planning` folder to your Odoo addons directory
2. Update the apps list: Settings → Apps → Update Apps List
3. Search for "HR Planning" and click Install

## Dependencies

- `hr` (Human Resources)
- `hr_holidays` (Time Off)
- `resource` (Resource)
- `mail` (Discuss)
- `portal` (Portal)

## Configuration

After installation:

1. Go to **Planning → Configuration → Roles** to set up job roles
2. Go to **Planning → Configuration → Shift Templates** to configure templates
3. Assign roles to employees in their employee form (Planning tab)
4. Configure settings in **Settings → Planning**

## Usage

### Creating Shifts

1. Navigate to **Planning → Schedule → Planning**
2. Click **Create** or drag on the Gantt view
3. Select employee, role, and timing
4. Optionally use a template for quick creation

### Publishing Shifts

1. Create shifts in draft status
2. Click **Publish** to make them visible to employees
3. Use **Send** to email notifications to employees

### Copying Schedules

1. Click **Copy Previous** in the Gantt view
2. Select source and target periods
3. Filter by employees or roles if needed
4. Click **Copy Shifts**

## Security Groups

- **Planning / User**: View own shifts, limited access
- **Planning / Manager**: Full access to all planning features

## Technical Details

### Models

| Model | Description |
|-------|-------------|
| `planning.slot` | Main shift/schedule model |
| `planning.role` | Job roles for categorization |
| `planning.template` | Reusable shift templates |
| `planning.slot.recurrency` | Manages recurring shifts |

### Views

- Tree (list) view
- Form view with chatter
- Calendar view (week/month)
- Gantt view (the primary view)
- Kanban view
- Pivot/Graph for analysis

## License

LGPL-3

## Author

Your Company
