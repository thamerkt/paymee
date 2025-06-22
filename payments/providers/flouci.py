import requests
from django.conf import settings

def generate_payment(payment):
    url = "https://developers.flouci.com/api/generate_payment"
    payload = {
        "app_token": settings.FLOUCI_APP_TOKEN,
        "app_secret": settings.FLOUCI_APP_SECRET,
        "amount": str(int(payment.amount * 100)),  # Flouci expects amount in cents
        "accept_card": "true",
        "session_timeout_secs": 1200,
        "success_link": "https://example.website.com/success",
        "fail_link": "https://example.website.com/fail",
        "developer_tracking_id": str(payment.id),
    }
    headers = {
        "Content-Type": "application/json"
    }

    response = requests.post(url, json=payload, headers=headers)
    response.raise_for_status()
    data = response.json()

    # Optionally, save transaction_id
    payment.transaction_id = data.get('payment_token')
    payment.save()

    return {
        "redirect_url": data.get('redirect_url'),
    }
