from typing import Dict, Any
from models import OrderNotificationMessage


class EmailService:
    def __init__(self, table, ses_client, from_email: str):
        self.table = table
        self.ses = ses_client
        self.from_email = from_email
        
        self.event_templates = {
            'ORDER_CREATED': self._order_created_template,
            'PAYMENT_CONFIRMED': self._payment_confirmed_template,
            'FULFILLMENT_STARTED': self._fulfillment_started_template,
            'FULFILLED': self._fulfilled_template,
            'PAYMENT_FAILED': self._payment_failed_template,
            'FULFILLMENT_CANCELED': self._fulfillment_cancelled_template,
        }

    def process_event(self, notification: OrderNotificationMessage) -> None:
        user = self._get_user(notification.user_id)
        if not user:
            print(f"User not found: {notification.user_id}")
            return
        
        template_fn = self.event_templates.get(notification.event_type)
        if not template_fn:
            print(f"Unknown event type: {notification.event_type}")
            return
        
        subject, body = template_fn(user, notification)
        self._send_email(user['email'], subject, body)

    def _get_user(self, user_id: str) -> Dict[str, Any]:
        response = self.table.query(
            KeyConditionExpression='PK = :pk AND SK = :sk',
            ExpressionAttributeValues={
                ':pk': f'USER#{user_id}',
                ':sk': 'PROFILE'
            }
        )
        items = response.get('Items', [])
        return items[0] if items else None

    def _send_email(self, to_email: str, subject: str, body: str) -> None:
        try:
            self.ses.send_email(
                Source=self.from_email,
                Destination={'ToAddresses': [to_email]},
                Message={
                    'Subject': {'Data': subject, 'Charset': 'UTF-8'},
                    'Body': {'Html': {'Data': body, 'Charset': 'UTF-8'}}
                }
            )
            print(f"Email sent to {to_email}: {subject}")
        except Exception as e:
            print(f"Failed to send email to {to_email}: {str(e)}")
            raise

    def _order_created_template(self, user: Dict, notification: OrderNotificationMessage) -> tuple:
        subject = f"Order Confirmation - {notification.order_id}"
        body = f"""
        <html>
        <body>
            <h2>Order Confirmation</h2>
            <p>Hello {user['first_name']} {user['last_name']},</p>
            <p>Thank you for your order!</p>
            <p><strong>Order ID:</strong> {notification.order_id}</p>
            <p>We'll notify you when your payment is confirmed.</p>
        </body>
        </html>
        """
        return subject, body

    def _payment_confirmed_template(self, user: Dict, notification: OrderNotificationMessage) -> tuple:
        subject = f"Payment Confirmed - Order {notification.order_id}"
        body = f"""
        <html>
        <body>
            <h2>Payment Confirmed</h2>
            <p>Hello {user['first_name']},</p>
            <p>Your payment has been successfully processed!</p>
            <p><strong>Order ID:</strong> {notification.order_id}</p>
            <p>Your order is now being prepared for fulfillment.</p>
        </body>
        </html>
        """
        return subject, body

    def _fulfillment_started_template(self, user: Dict, notification: OrderNotificationMessage) -> tuple:
        subject = f"Order Fulfillment Started - {notification.order_id}"
        body = f"""
        <html>
        <body>
            <h2>Order Fulfillment Started</h2>
            <p>Hello {user['first_name']},</p>
            <p>Great news! Your order is now being processed.</p>
            <p><strong>Order ID:</strong> {notification.order_id}</p>
            <p>We'll notify you once your order is fulfilled.</p>
        </body>
        </html>
        """
        return subject, body

    def _fulfilled_template(self, user: Dict, notification: OrderNotificationMessage) -> tuple:
        subject = f"Order Fulfilled - {notification.order_id}"
        body = f"""
        <html>
        <body>
            <h2>Order Fulfilled</h2>
            <p>Hello {user['first_name']},</p>
            <p>Your order has been successfully fulfilled!</p>
            <p><strong>Order ID:</strong> {notification.order_id}</p>
            <p>Thank you for your business!</p>
        </body>
        </html>
        """
        return subject, body

    def _payment_failed_template(self, user: Dict, notification: OrderNotificationMessage) -> tuple:
        subject = f"Payment Failed - Order {notification.order_id}"
        body = f"""
        <html>
        <body>
            <h2>Payment Failed</h2>
            <p>Hello {user['first_name']},</p>
            <p>Unfortunately, we couldn't process your payment.</p>
            <p><strong>Order ID:</strong> {notification.order_id}</p>
            <p>Please try again or contact support for assistance.</p>
        </body>
        </html>
        """
        return subject, body

    def _fulfillment_cancelled_template(self, user: Dict, notification: OrderNotificationMessage) -> tuple:
        subject = f"Order Fulfillment Cancelled - {notification.order_id}"
        body = f"""
        <html>
        <body>
            <h2>Order Fulfillment Cancelled</h2>
            <p>Hello {user['first_name']},</p>
            <p>We regret to inform you that your order fulfillment has been cancelled.</p>
            <p><strong>Order ID:</strong> {notification.order_id}</p>
            <p>Please contact support for more information.</p>
        </body>
        </html>
        """
        return subject, body