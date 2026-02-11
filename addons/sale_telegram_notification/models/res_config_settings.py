# -*- coding: utf-8 -*-
from odoo import models, fields, api


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    telegram_bot_token = fields.Char(
        string='Telegram Bot Token',
        config_parameter='sale_telegram_notification.bot_token',
        help='Get from @BotFather on Telegram'
    )
    telegram_chat_id = fields.Char(
        string='Telegram Chat ID',
        config_parameter='sale_telegram_notification.chat_id',
        help='Group/Channel ID (negative number for groups)'
    )
    telegram_enabled = fields.Boolean(
        string='Enable Telegram Notifications',
        config_parameter='sale_telegram_notification.enabled',
        default=False
    )
    telegram_base_url = fields.Char(
        string='Odoo Base URL',
        config_parameter='sale_telegram_notification.base_url',
        help='Your Odoo URL (e.g., https://yourdomain.com). Leave empty to auto-detect.'
    )
