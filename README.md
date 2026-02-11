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
