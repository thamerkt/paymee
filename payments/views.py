import json
import logging
import requests
import pika

from django.conf import settings
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

logger = logging.getLogger(__name__)

# -------------------- RabbitMQ Utilities --------------------

def get_rabbitmq_channel():
    try:
        connection = pika.BlockingConnection(
            pika.ConnectionParameters(
                host='host.docker.internal',
                port=5672,
                heartbeat=600,
                blocked_connection_timeout=300
            )
        )
        channel = connection.channel()
        channel.queue_declare(queue='generate_contract', durable=True)
        return channel, connection
    except Exception as e:
        logger.error("Failed to connect to RabbitMQ", exc_info=True)
        raise

# -------------------- Flouci Payment Start --------------------

@csrf_exempt
@require_POST
def start_payment(request):
    """
    Initiate payment with Flouci payment gateway
    """
    flouci_config = {
        "app_token": getattr(settings, 'FLOUCI_APP_TOKEN', ''),
        "app_secret": getattr(settings, 'FLOUCI_APP_SECRET', ''),
        "redirect_url": getattr(settings, 'FLOUCI_REDIRECT_URL', ''),
    }
    

    # Check config values
    if not all(flouci_config.values()):
        logger.error("Flouci configuration missing in settings")
        return JsonResponse(
            {"error": "Payment gateway configuration error"},
            status=500
        )

    payload = {
        "app_token": flouci_config['app_token'],
        "app_secret": flouci_config['app_secret'],
        "amount": "30500",  # Consider making this dynamic
        "accept_card": "true",
        "session_timeout_secs": 1200,
        "success_link": f"{flouci_config['redirect_url']}?status=success",
        "fail_link": f"{flouci_config['redirect_url']}?status=fail",
        "developer_tracking_id": "tracking_001"
    }

    headers = {'Content-Type': 'application/json'}
    api_url = 'https://developers.flouci.com/api/generate_payment'

    try:
        response = requests.post(api_url, json=payload, headers=headers, timeout=10)
        response.raise_for_status()
        response_data = response.json()

        payment_url = response_data.get("result", {}).get("link")
        if payment_url:
            logger.info("Flouci payment initiated successfully")
            return JsonResponse({
                "status": "success",
                "payment_url": payment_url,
                "details": response_data
            })

        logger.error("No payment URL in Flouci response", extra={'response': response_data})
        return JsonResponse({
            "error": "No payment URL returned by Flouci",
            "details": response_data
        }, status=500)

    except requests.exceptions.RequestException as e:
        logger.error("Flouci API request failed", exc_info=True)
        return JsonResponse({
            "error": "Payment gateway communication error",
            "details": str(e)
        }, status=500)

    except json.JSONDecodeError:
        logger.error("Invalid JSON response from Flouci", exc_info=True)
        return JsonResponse({
            "error": "Invalid response from payment gateway",
            "raw_response": response.text
        }, status=500)

# -------------------- Flouci Callback Handler --------------------

@csrf_exempt
@require_POST
def payment_callback(request):
    try:
        data = json.loads(request.body)

        required_fields = [
            "requestId", "equipmentId", "rentalId",
            "amount", "startDate", "endDate"
        ]
        if not all(field in data for field in required_fields):
            return JsonResponse({
                "error": "Missing required fields",
                "received": data
            }, status=400)

        message = {
            "client": data["requestId"],
            "equipment": data["equipmentId"],
            "rental": data["rentalId"],
            "total_price": data["amount"],
            "start_date": data["startDate"],
            "end_date": data["endDate"],
            "status": "pending"
        }

        channel, connection = get_rabbitmq_channel()
        channel.basic_publish(
            exchange='',
            routing_key='generate_contract',
            body=json.dumps(message),
            properties=pika.BasicProperties(
                delivery_mode=2  # Persistent delivery
            )
        )
        connection.close()

        logger.info("Published contract message to RabbitMQ", extra={"message": message})

        return JsonResponse({
            "status": "received",
            "published": True,
            "sent_message": message
        })

    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON"}, status=400)

    except Exception as e:
        logger.error("Callback processing failed", exc_info=True)
        return JsonResponse({"error": str(e)}, status=500)
