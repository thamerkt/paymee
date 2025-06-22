def create_payment(payment):
    # Call Konnect API here
    payment.transaction_id = "konnect98765"
    payment.status = "pending"
    payment.save()

    return {
        "payment_url": f"https://konnect.network/pay/{payment.transaction_id}",
        "status": payment.status
    }
