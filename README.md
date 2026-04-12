# Odoo 18 — Custom Modules & Docker Setup

Dockerized Odoo 18 Community with custom addons for **sales commission tracking**, **Telegram order notifications**, a **Time Off dashboard fix**, and a **custom website theme**.

## Architecture

```
├── addons/              # Custom addons (mounted into Odoo 18 container)
│   ├── hr_sale_commission/           # Commission tracking
│   ├── sale_telegram_notification/   # Telegram alerts
│   ├── hr_holidays_fix/              # Time Off dashboard patch
│   ├── hustle_website/               # Custom website pages
│   └── muk_web_theme/                # MuK backend theme (3rd-party)
├── addons2/             # Addons for Odoo 17 (secondary instance)
├── cloudflared/         # Cloudflare Tunnel config
├── config/
│   └── odoo.conf        # Odoo server config
├── compose.yml          # Docker Compose (Odoo 18 + 17 + Postgres + Tunnel)
└── .env                 # Environment variables (not committed)
```

## Services

| Service       | Image                     | Port  | Notes                            |
|---------------|---------------------------|-------|----------------------------------|
| **db**        | `postgres:16`             | 5433  | Shared database                  |
| **odoo18**    | `odoo:18.0`               | 8068  | Main instance with custom addons |
| **odoo17**    | `odoo:17.0`               | 8067  | Secondary instance               |
| **cloudflared** | `cloudflare/cloudflared` | —     | Exposes Odoo via Cloudflare Tunnel |

## Business Logic Documentation

The custom modules come with detailed business logic documentation covering workflows, internal calculations, and user manuals. You can refer to the following Markdown files directly in the repository:

- **[Employee Custom (`hr_employee_custom`)](addons/hr_employee_custom/EMPLOYEE_FLOW.md)**: Employee profile setup, hierarchy organization, and integration metrics (PIN configuration for Kiosks, dependents for PIT calculation, and ABC performance rating).
- **[Recruitment Custom (`hr_recruitment_custom`)](addons/hr_recruitment_custom/RECRUITMENT_FLOW.md)**: Customized applicant tracking pipeline, collaborative review and interview scheduling, status flagging, and direct employee onboarding conversion.
- **[Attendance Custom (`hr_attendance_custom`)](addons/hr_attendance_custom/ATTENDANCE_FLOW.md)**: Kiosk check-in/out procedures via PIN, automated status flagging (Late In / Early Out / Forgot Checkout) based on work schedules, and a multi-level approval workflow for Attendance Correction Requests.
- **[Payroll Custom (`hr_payroll_custom`)](addons/hr_payroll_custom/PAYROLL_FLOW.md)**: Salary computation formulas (Basic, OT, Allowances), performance-based bonuses (Sales, Livestream, ABC rating), penalty approval systems, Social Insurances deductions, and progressive Personal Income Tax (PIT) processing.
- **[Contract Custom (`hr_contract_custom`)](addons/hr_contract_custom/CONTRACT_FLOW.md)**: Three-tier approval workflow for contracts (Branch Manager $\rightarrow$ HR $\rightarrow$ Director), detailed allowance tracking, automated contract expiry alerts via cron jobs, and employee electronic confirmation processes.
- **[Offboarding & Asset Recovery (`hr_offboarding`)](addons/hr_offboarding/OFFBOARDING_FLOW.md)**: Automates employee resignation procedures, asset collection check-listing, financial compensation computation for lost/damaged hardware, and final employee archiving.
- **[POS Sales Sync (`pos_sales_sync`)](addons/pos_sales_sync/POS_SALES_SYNC_FLOW.md)**: Auto-syncs Point of Sale session data strictly categorizing total sales logic directly into HR Payroll tracking tables solving data isolation per cashier.
- **[Shipping API Integration (`delivery_ghn`)](addons/delivery_ghn/DELIVERY_GHN_FLOW.md)**: Pushes warehouse Delivery Orders to GHN & GHTK web portals tracking physical orders directly over Odoo.
- **[COD Reconciliation (`account_cod_reconcile`)](addons/account_cod_reconcile/ACCOUNT_COD_RECONCILE_FLOW.md)**: Intake spreadsheet logic mapping tracking numbers directly into the native accounting ledger reconciling paid COD figures implicitly. 
- **[Tailoring / Alterations Point of Sale (`pos_tailoring`)](addons/pos_tailoring/POS_TAILORING_FLOW.md)**: Owl-based GUI buttons appending Deposit logic arrays tracking tailoring instructions mapped to backend workshop fulfillment.

---

## Custom Modules

### 1. HR Sales Commission (`hr_sale_commission`)

Tracks sales commissions per employee based on delivered orders.

- **Commission Rules** — tiered rates (1%–4%) based on order count and/or revenue thresholds
- **Commission Records** — monthly aggregation per employee with Draft → Confirmed → Locked workflow
- **Commission Lines** — links each sale order to its commission record
- **Auto-trigger** — commission is created automatically when a stock picking (delivery) is marked as done

### 2. Sale Telegram Notification (`sale_telegram_notification`)

Sends real-time order notifications to a Telegram group/channel.

- **Events**: new website order, order confirmed, delivery completed
- **Config**: Bot Token, Chat ID, and Base URL via Settings → Sales → Telegram
- **Message format**: customer info, product lines, totals, and a direct link to the order

### 3. Time Off Dashboard Fix (`hr_holidays_fix`)

Patches the default Time Off Dashboard so it shows **all employees' leave entries** instead of only the current user's. Useful for managers/admins who need a full overview.

### 4. Hustle Website (`hustle_website`)

Custom website pages (landing, login, register, contact, 404, password reset) using a Bootstrap-based template.

## Quick Start

### Prerequisites

- Docker & Docker Compose
- (Optional) Cloudflare Tunnel token

### Setup

1. **Clone the repo**

   ```bash
   git clone https://github.com/yunsi2606/domo-odoo.git && cd odoo
   ```

2. **Create `.env`** from the example

   ```bash
   cp .env.example .env
   # Edit .env and set your CLOUDFLARE_TUNNEL_TOKEN (or remove the cloudflared service)
   ```

3. **Start services**

   ```bash
   docker compose up -d
   ```

4. **Access Odoo 18** at [http://localhost:8068](http://localhost:8068)

5. **Install custom modules**

   - Go to **Apps**, remove the "Apps" filter, search for the module name
   - Click **Install**

### Telegram Setup

1. Create a bot via [@BotFather](https://t.me/BotFather) and get the token
2. Add the bot to your group and get the Chat ID
3. In Odoo: **Settings → Sales → Telegram** — enable and paste token + chat ID

## Configuration

### `config/odoo.conf`

Standard Odoo config — addons path, data directory, and admin password.

### Commission Rules (default data)

| Tier       | Min Orders | Min Revenue | Rate |
|------------|-----------|-------------|------|
| Entry      | 0         | 0           | 1%   |
| Bronze     | 5 / 5M₫   | —           | 1.5% |
| Silver     | 10 / 15M₫  | —           | 2%   |
| Gold       | 20 / 30M₫  | —           | 2.5% |
| Platinum   | 30 + 50M₫  | Both        | 3%   |
| Diamond    | 50 + 100M₫ | Both        | 4%   |

Rules can be customized in Odoo: **Sales → Commissions → Configuration → Commission Rules**.

## License

LGPL-3 (same as Odoo Community).
