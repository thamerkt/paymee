import pika
import json

def test_rabbitmq():
    try:
        connection = pika.BlockingConnection(
            pika.ConnectionParameters(
                host='host.docker.internal',  # change if needed
                port=5672,
                heartbeat=600,
                blocked_connection_timeout=300
            )
        )
        channel = connection.channel()

        # Declare the queue (durable = survive RabbitMQ restart)
        channel.queue_declare(queue='generate_contract', durable=True)
        print("Queue declared successfully")

        # Publish a test message
        message = {"test": "hello rabbitmq!"}
        channel.basic_publish(
            exchange='',
            routing_key='generate_contract',
            body=json.dumps(message),
            properties=pika.BasicProperties(delivery_mode=2)  # persistent
        )
        print("Test message published")

        connection.close()
        print("Connection closed")

    except Exception as e:
        print(f"Failed to connect or publish: {e}")

if __name__ == "__main__":
    test_rabbitmq()
