import requests
from django.conf import settings
from datetime import datetime

BASE_URL = 'https://pep.shaparak.ir/api/payment'
TOKEN_URL = 'https://mmsapi.pep.co.ir/api/Account/getToken'


def get_token():
    response = requests.post(TOKEN_URL, json={
        "username": settings.PEP_USERNAME,
        "password": settings.PEP_PASSWORD
    })
    response.raise_for_status()
    data = response.json()
    if data.get("resultCode") != 0:
        raise Exception(f"Token Error: {data.get('resultMsg')}")
    return data['token']


def request_payment_url(invoice_id, amount, callback_url, description, phone_number):
    token = get_token()
    headers = {"Authorization": f"Bearer {token}"}
    payload = {
        "invoice": str(invoice_id),
        "invoiceDate": datetime.now().strftime("%Y/%m/%d"),
        "amount": int(amount),
        "callbackApi": callback_url,
        "mobileNumber": phone_number,
        "serviceCode": "8",
        "serviceType": "PURCHASE",
        "terminalNumber": settings.PEP_TERMINAL_NO,
        "description": f"Invoice {invoice_id} for {description}",
        "payerMail": "",
        "payerName": "",
        "pans": "",
        "nationalCode": ""
    }
    response = requests.post(f"{BASE_URL}/purchase", json=payload, headers=headers)
    data = response.json()
    if data.get("resultCode") != 0:
        raise Exception(f"Purchase Error: {data.get('resultMsg')}")
    return data["data"]["url"]
