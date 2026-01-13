"""
RabbitMQ consumer for order notifications
Listens for order events and broadcasts them via WebSocket
"""
import aio_pika
import json
import asyncio
import os
from typing import Optional
from shared.utils.logger import setup_logger
from .websocket import manager

logger = setup_logger("rabbitmq-consumer")


class OrderNotificationConsumer:
    """Consumes order notification events from RabbitMQ and broadcasts via WebSocket"""

    def __init__(self):
        self.connection: Optional[aio_pika.Connection] = None
        self.channel: Optional[aio_pika.Channel] = None
        self.rabbitmq_host = os.getenv("RABBITMQ_HOST", "rabbitmq-service")
        self.rabbitmq_user = os.getenv("RABBITMQ_USER", "guest")
        self.rabbitmq_password = os.getenv("RABBITMQ_PASSWORD", "guest")

    async def connect(self):
        """Connect to RabbitMQ"""
        try:
            self.connection = await aio_pika.connect_robust(
                f"amqp://{self.rabbitmq_user}:{self.rabbitmq_password}@{self.rabbitmq_host}/"
            )
            self.channel = await self.connection.channel()
            await self.channel.set_qos(prefetch_count=10)

            logger.info("Connected to RabbitMQ successfully")
        except Exception as e:
            logger.error(f"Failed to connect to RabbitMQ: {e}")
            raise

    async def start_consuming(self):
        """Start consuming order notification events"""
        try:
            # Declare exchange
            exchange = await self.channel.declare_exchange(
                "orders",
                aio_pika.ExchangeType.TOPIC,
                durable=True
            )

            # Declare queue
            queue = await self.channel.declare_queue(
                "order_notifications",
                durable=True
            )

            # Bind queue to exchange with routing key pattern
            await queue.bind(exchange, routing_key="order.created.*")

            logger.info("Starting to consume order notifications...")

            # Start consuming messages
            async with queue.iterator() as queue_iter:
                async for message in queue_iter:
                    async with message.process():
                        await self.process_message(message)

        except Exception as e:
            logger.error(f"Error in consuming loop: {e}")
            raise

    async def process_message(self, message: aio_pika.IncomingMessage):
        """Process a single notification message"""
        try:
            body = message.body.decode()
            notification = json.loads(body)

            logger.info(f"Received notification: {notification.get('event')} for order {notification.get('order_number')}")

            # Extract restaurant_id from routing key or payload
            restaurant_id = notification.get("restaurant_id")

            if not restaurant_id:
                logger.warning("No restaurant_id in notification, skipping")
                return

            # Broadcast to all WebSocket clients connected to this restaurant
            await manager.broadcast_to_restaurant(notification, str(restaurant_id))

            logger.info(f"Notification broadcasted for order {notification.get('order_number')}")

        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in message: {e}")
        except Exception as e:
            logger.error(f"Error processing message: {e}")

    async def close(self):
        """Close RabbitMQ connection"""
        try:
            if self.connection:
                await self.connection.close()
                logger.info("RabbitMQ connection closed")
        except Exception as e:
            logger.error(f"Error closing RabbitMQ connection: {e}")


# Global consumer instance
consumer = OrderNotificationConsumer()


async def start_consumer():
    """Start the RabbitMQ consumer in the background"""
    try:
        await consumer.connect()
        await consumer.start_consuming()
    except Exception as e:
        logger.error(f"Consumer failed: {e}")
        # Retry after delay
        await asyncio.sleep(5)
        await start_consumer()
