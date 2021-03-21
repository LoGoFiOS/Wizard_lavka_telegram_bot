import json

import requests
from bot import config


def get_invoice(billid: str, amount: float):
    s = requests.Session()
    s.headers['Accept'] = 'application/json'
    s.headers['Authorization'] = 'Bearer ' + config.Q_SECRETKEY
    s.headers['Content-Type'] = 'application/json'
    p = {
        "amount": {
            "currency": "RUB",
            "value": f"{amount}"
        },
        "expirationDateTime": "2025-12-10T09:02:00+03:00",
    }
    payload = json.dumps(p)
    link = f'https://api.qiwi.com/partner/bill/v1/bills/{billid}'
    response = s.put(url=link, data=payload)
    return response.json()['payUrl']


def is_bill_paid(billid: str):
    s = requests.Session()
    s.headers['Accept'] = 'application/json'
    s.headers['Authorization'] = 'Bearer ' + config.Q_SECRETKEY
    link = f'https://api.qiwi.com/partner/bill/v1/bills/{billid}'
    response = s.get(url=link)
    status = response.json()['status']['value']
    if status == "PAID":
        return True
    else:
        return False
