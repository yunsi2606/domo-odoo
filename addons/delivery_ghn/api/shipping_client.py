# -*- coding: utf-8 -*-
import requests
import json
import logging

_logger = logging.getLogger(__name__)

GHN_API_BASE = 'https://online-gateway.ghn.vn/shiip/public-api/v2'
GHTK_API_BASE = 'https://services.giaohangtietkiem.vn'


class GHNClient:
    def __init__(self, token, shop_id):
        self.token = token
        self.shop_id = shop_id
        self.headers = {
            'Token': token,
            'ShopId': str(shop_id),
            'Content-Type': 'application/json',
        }

    def create_order(self, payload):
        url = f'{GHN_API_BASE}/shipping-order/create'
        try:
            resp = requests.post(url, json=payload, headers=self.headers, timeout=15)
            resp.raise_for_status()
            return resp.json()
        except Exception as e:
            _logger.error('GHN create_order error: %s', e)
            raise

    def get_order_info(self, order_code):
        url = f'{GHN_API_BASE}/shipping-order/detail'
        try:
            resp = requests.post(url, json={'order_code': order_code},
                                 headers=self.headers, timeout=10)
            resp.raise_for_status()
            return resp.json()
        except Exception as e:
            _logger.error('GHN get_order_info error: %s', e)
            raise

    def cancel_order(self, order_codes):
        url = f'{GHN_API_BASE}/switch-status/cancel'
        resp = requests.post(url, json={'order_codes': order_codes},
                             headers=self.headers, timeout=10)
        resp.raise_for_status()
        return resp.json()

    def get_available_services(self, from_district, to_district):
        url = f'{GHN_API_BASE}/shipping-order/available-services'
        payload = {
            'shop_id': int(self.shop_id),
            'from_district': from_district,
            'to_district': to_district,
        }
        resp = requests.post(url, json=payload, headers=self.headers, timeout=10)
        resp.raise_for_status()
        return resp.json()


class GHTKClient:
    def __init__(self, token):
        self.token = token
        self.headers = {
            'Token': token,
            'Content-Type': 'application/json',
        }

    def create_order(self, payload):
        url = f'{GHTK_API_BASE}/services/shipment/order'
        try:
            resp = requests.post(url, json=payload, headers=self.headers, timeout=15)
            resp.raise_for_status()
            return resp.json()
        except Exception as e:
            _logger.error('GHTK create_order error: %s', e)
            raise

    def get_order_status(self, label_id):
        url = f'{GHTK_API_BASE}/services/shipment/v2/{label_id}'
        resp = requests.get(url, headers=self.headers, timeout=10)
        resp.raise_for_status()
        return resp.json()

    def cancel_order(self, label_id):
        url = f'{GHTK_API_BASE}/services/shipment/cancel/{label_id}'
        resp = requests.post(url, headers=self.headers, timeout=10)
        resp.raise_for_status()
        return resp.json()
