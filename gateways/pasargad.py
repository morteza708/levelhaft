import requests
from django.conf import settings
from datetime import datetime
import jdatetime

def get_token():
    response = requests.post(
        'https://pep.shaparak.ir/dorsa1/token/getToken',
        json={
            "username": settings.PEP_USERNAME,
            "password": settings.PEP_PASSWORD
        },
        timeout=15
    )
    response.raise_for_status()
    data = response.json()
    if data.get("resultCode") != 0:
        raise Exception(f"Token Error: {data.get('resultMsg')}")
    return data["token"]

def request_payment_url(invoice_id, amount, callback_url, description, phone_number, return_full=False):
    token = get_token()
    headers = {"Authorization": f"Bearer {token}"}
    payload = {
        "invoice": str(invoice_id),
        "invoiceDate": jdatetime.date.today().strftime("%Y/%m/%d"),
        "amount": int(amount),
        "callbackApi": callback_url,
        "mobileNumber": phone_number,
        "serviceCode": "8",
        "serviceType": "PURCHASE",
        "terminalNumber": settings.PEP_TERMINAL_NO,
        "description": description,
        "payerMail": "",
        "payerName": "",
        "pans": "",
        "nationalCode": ""
    }
    response = requests.post(
        'https://pep.shaparak.ir/dorsa1/api/payment/purchase',
        json=payload,
        headers=headers,
        timeout=15
    )
    data = response.json()
    if data.get("resultCode") != 0:
        raise Exception(f"Purchase Error: {data.get('resultMsg')}")
    
    if return_full:
        return data["data"]   # شامل "urlId" و "url"
    return data["data"]["url"]
