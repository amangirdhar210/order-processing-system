from typing import Dict, Any
from models import OrderNotificationMessage
from repository import UserRepository, OrderRepository


class EmailService:
    def __init__(self, user_repository: UserRepository, order_repository: OrderRepository, ses_client, from_email: str):
        self.user_repo = user_repository
        self.order_repo = order_repository
        self.ses = ses_client
        self.from_email = from_email
        
        self.event_templates = {
            'ORDER_CREATED': self._order_created_template,
            'PAYMENT_CONFIRMED': self._payment_confirmed_template,
            'FULFILLMENT_STARTED': self._fulfillment_started_template,
            'FULFILLED': self._fulfilled_template,
            'PAYMENT_FAILED': self._payment_failed_template,
            'FULFILLMENT_CANCELED': self._fulfillment_cancelled_template,
            'ORDER_CANCELLED': self._order_cancelled_template,
        }

    def process_event(self, notification: OrderNotificationMessage) -> None:
        user = self.user_repo.get_user(notification.user_id)
        if not user:
            print(f"User not found: {notification.user_id}")
            return
        
        order = self.order_repo.get_order(notification.order_id)
        if not order:
            print(f"Order not found: {notification.order_id}")
            return
        
        template_fn = self.event_templates.get(notification.event_type)
        if not template_fn:
            print(f"Unknown event type: {notification.event_type}")
            return
        
        subject, body = template_fn(user, order, notification)
        self._send_email(user['email'], subject, body)

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

    def _format_order_items(self, order: Dict) -> str:
        """Format order items as HTML table"""
        items_html = """
        <table style="width: 100%; border-collapse: collapse; margin: 20px 0;">
            <thead>
                <tr style="background-color: #f8f9fa;">
                    <th style="padding: 10px; text-align: left; border-bottom: 2px solid #dee2e6;">Item</th>
                    <th style="padding: 10px; text-align: center; border-bottom: 2px solid #dee2e6;">Qty</th>
                    <th style="padding: 10px; text-align: right; border-bottom: 2px solid #dee2e6;">Price</th>
                    <th style="padding: 10px; text-align: right; border-bottom: 2px solid #dee2e6;">Subtotal</th>
                </tr>
            </thead>
            <tbody>
        """
        
        for item in order.get('items', []):
            items_html += f"""
                <tr>
                    <td style="padding: 10px; border-bottom: 1px solid #dee2e6;">{item['product_name']}</td>
                    <td style="padding: 10px; text-align: center; border-bottom: 1px solid #dee2e6;">{item['quantity']}</td>
                    <td style="padding: 10px; text-align: right; border-bottom: 1px solid #dee2e6;">${item['unit_price']}</td>
                    <td style="padding: 10px; text-align: right; border-bottom: 1px solid #dee2e6;">${item['subtotal']}</td>
                </tr>
            """
        
        items_html += f"""
            </tbody>
            <tfoot>
                <tr>
                    <td colspan="3" style="padding: 10px; text-align: right; font-weight: bold;">Total:</td>
                    <td style="padding: 10px; text-align: right; font-weight: bold; color: #28a745;">${order.get('total_amount', '0.00')}</td>
                </tr>
            </tfoot>
        </table>
        """
        return items_html

    def _order_created_template(self, user: Dict, order: Dict, notification: OrderNotificationMessage) -> tuple:
        subject = f"Order Confirmation - {notification.order_id}"
        items_table = self._format_order_items(order)
        body = f"""
        <html>
        <body style="font-family: Arial, sans-serif; background-color: #f4f4f4; padding: 20px;">
            <div style="max-width: 600px; margin: 0 auto; background-color: #ffffff; border-radius: 8px; padding: 30px; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
                <h2 style="color: #28a745; border-bottom: 2px solid #28a745; padding-bottom: 10px;">Order Confirmation</h2>
                <p style="color: #333; font-size: 16px;">Hello {user['first_name']} {user['last_name']},</p>
                <p style="color: #555; font-size: 14px;">Thank you for your order!</p>
                <div style="background-color: #f8f9fa; border-left: 4px solid #28a745; padding: 15px; margin: 20px 0;">
                    <p style="margin: 0; color: #333;"><strong>Order ID:</strong> {notification.order_id}</p>
                    <p style="margin: 10px 0 0 0; color: #333;"><strong>Status:</strong> {order.get('order_status', 'N/A')}</p>
                </div>
                <h3 style="color: #333; margin-top: 30px;">Order Details</h3>
                {items_table}
                <p style="color: #555; font-size: 14px; margin-top: 20px;">We'll notify you when your payment is confirmed.</p>
            </div>
        </body>
        </html>
        """
        return subject, body

    def _payment_confirmed_template(self, user: Dict, order: Dict, notification: OrderNotificationMessage) -> tuple:
        subject = f"Payment Confirmed - Order {notification.order_id}"
        items_table = self._format_order_items(order)
        payment_details = order.get('payment_details', {})
        body = f"""
        <html>
        <body style="font-family: Arial, sans-serif; background-color: #f4f4f4; padding: 20px;">
            <div style="max-width: 600px; margin: 0 auto; background-color: #ffffff; border-radius: 8px; padding: 30px; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
                <h2 style="color: #007bff; border-bottom: 2px solid #007bff; padding-bottom: 10px;">Payment Confirmed</h2>
                <p style="color: #333; font-size: 16px;">Hello {user['first_name']},</p>
                <p style="color: #555; font-size: 14px;">Your payment has been successfully processed!</p>
                <div style="background-color: #f8f9fa; border-left: 4px solid #007bff; padding: 15px; margin: 20px 0;">
                    <p style="margin: 0; color: #333;"><strong>Order ID:</strong> {notification.order_id}</p>
                    <p style="margin: 10px 0 0 0; color: #333;"><strong>Payment Method:</strong> {payment_details.get('payment_method', 'N/A')}</p>
                    <p style="margin: 10px 0 0 0; color: #333;"><strong>Transaction ID:</strong> {payment_details.get('transaction_id', 'N/A')}</p>
                </div>
                <h3 style="color: #333; margin-top: 30px;">Order Details</h3>
                {items_table}
                <p style="color: #555; font-size: 14px; margin-top: 20px;">Your order is now being prepared for fulfillment.</p>
            </div>
        </body>
        </html>
        """
        return subject, body

    def _fulfillment_started_template(self, user: Dict, order: Dict, notification: OrderNotificationMessage) -> tuple:
        subject = f"Order Fulfillment Started - {notification.order_id}"
        items_table = self._format_order_items(order)
        body = f"""
        <html>
        <body style="font-family: Arial, sans-serif; background-color: #f4f4f4; padding: 20px;">
            <div style="max-width: 600px; margin: 0 auto; background-color: #ffffff; border-radius: 8px; padding: 30px; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
                <h2 style="color: #17a2b8; border-bottom: 2px solid #17a2b8; padding-bottom: 10px;">Order Fulfillment Started</h2>
                <p style="color: #333; font-size: 16px;">Hello {user['first_name']},</p>
                <p style="color: #555; font-size: 14px;">Great news! Your order is now being processed.</p>
                <div style="background-color: #f8f9fa; border-left: 4px solid #17a2b8; padding: 15px; margin: 20px 0;">
                    <p style="margin: 0; color: #333;"><strong>Order ID:</strong> {notification.order_id}</p>
                    <p style="margin: 10px 0 0 0; color: #333;"><strong>Delivery Address:</strong> {order.get('delivery_address', 'N/A')}</p>
                </div>
                <h3 style="color: #333; margin-top: 30px;">Order Details</h3>
                {items_table}
                <p style="color: #555; font-size: 14px; margin-top: 20px;">We'll notify you once your order is fulfilled.</p>
            </div>
        </body>
        </html>
        """
        return subject, body

    def _fulfilled_template(self, user: Dict, order: Dict, notification: OrderNotificationMessage) -> tuple:
        subject = f"Order Fulfilled - {notification.order_id}"
        items_table = self._format_order_items(order)
        body = f"""
        <html>
        <body style="font-family: Arial, sans-serif; background-color: #f4f4f4; padding: 20px;">
            <div style="max-width: 600px; margin: 0 auto; background-color: #ffffff; border-radius: 8px; padding: 30px; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
                <h2 style="color: #28a745; border-bottom: 2px solid #28a745; padding-bottom: 10px;">Order Fulfilled</h2>
                <p style="color: #333; font-size: 16px;">Hello {user['first_name']},</p>
                <p style="color: #555; font-size: 14px;">Your order has been successfully fulfilled!</p>
                <div style="background-color: #f8f9fa; border-left: 4px solid #28a745; padding: 15px; margin: 20px 0;">
                    <p style="margin: 0; color: #333;"><strong>Order ID:</strong> {notification.order_id}</p>
                    <p style="margin: 10px 0 0 0; color: #333;"><strong>Delivered To:</strong> {order.get('delivery_address', 'N/A')}</p>
                </div>
                <h3 style="color: #333; margin-top: 30px;">Order Summary</h3>
                {items_table}
                <p style="color: #555; font-size: 14px; margin-top: 20px;">Thank you for your business!</p>
            </div>
        </body>
        </html>
        """
        return subject, body

    def _payment_failed_template(self, user: Dict, order: Dict, notification: OrderNotificationMessage) -> tuple:
        subject = f"Payment Failed - Order {notification.order_id}"
        items_table = self._format_order_items(order)
        body = f"""
        <html>
        <body style="font-family: Arial, sans-serif; background-color: #f4f4f4; padding: 20px;">
            <div style="max-width: 600px; margin: 0 auto; background-color: #ffffff; border-radius: 8px; padding: 30px; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
                <h2 style="color: #dc3545; border-bottom: 2px solid #dc3545; padding-bottom: 10px;">Payment Failed</h2>
                <p style="color: #333; font-size: 16px;">Hello {user['first_name']},</p>
                <p style="color: #555; font-size: 14px;">Unfortunately, we couldn't process your payment.</p>
                <div style="background-color: #f8f9fa; border-left: 4px solid #dc3545; padding: 15px; margin: 20px 0;">
                    <p style="margin: 0; color: #333;"><strong>Order ID:</strong> {notification.order_id}</p>
                </div>
                <h3 style="color: #333; margin-top: 30px;">Order Details</h3>
                {items_table}
                <p style="color: #555; font-size: 14px; margin-top: 20px;">Please try again or contact support for assistance.</p>
            </div>
        </body>
        </html>
        """
        return subject, body

    def _fulfillment_cancelled_template(self, user: Dict, order: Dict, notification: OrderNotificationMessage) -> tuple:
        subject = f"Order Fulfillment Cancelled - {notification.order_id}"
        items_table = self._format_order_items(order)
        body = f"""
        <html>
        <body style="font-family: Arial, sans-serif; background-color: #f4f4f4; padding: 20px;">
            <div style="max-width: 600px; margin: 0 auto; background-color: #ffffff; border-radius: 8px; padding: 30px; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
                <h2 style="color: #ffc107; border-bottom: 2px solid #ffc107; padding-bottom: 10px;">Order Fulfillment Cancelled</h2>
                <p style="color: #333; font-size: 16px;">Hello {user['first_name']},</p>
                <p style="color: #555; font-size: 14px;">We regret to inform you that your order fulfillment has been cancelled.</p>
                <div style="background-color: #f8f9fa; border-left: 4px solid #ffc107; padding: 15px; margin: 20px 0;">
                    <p style="margin: 0; color: #333;"><strong>Order ID:</strong> {notification.order_id}</p>
                </div>
                <h3 style="color: #333; margin-top: 30px;">Order Details</h3>
                {items_table}
                <p style="color: #555; font-size: 14px; margin-top: 20px;">Please contact support for more information.</p>
            </div>
        </body>
        </html>
        """
        return subject, body

    def _order_cancelled_template(self, user: Dict, order: Dict, notification: OrderNotificationMessage) -> tuple:
        subject = f"Order Cancelled - {notification.order_id}"
        items_table = self._format_order_items(order)
        body = f"""
        <html>
        <body style="font-family: Arial, sans-serif; background-color: #f4f4f4; padding: 20px;">
            <div style="max-width: 600px; margin: 0 auto; background-color: #ffffff; border-radius: 8px; padding: 30px; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
                <h2 style="color: #6c757d; border-bottom: 2px solid #6c757d; padding-bottom: 10px;">Order Cancelled</h2>
                <p style="color: #333; font-size: 16px;">Hello {user['first_name']},</p>
                <p style="color: #555; font-size: 14px;">Your order has been cancelled as requested.</p>
                <div style="background-color: #f8f9fa; border-left: 4px solid #6c757d; padding: 15px; margin: 20px 0;">
                    <p style="margin: 0; color: #333;"><strong>Order ID:</strong> {notification.order_id}</p>
                    <p style="margin: 10px 0 0 0; color: #333;"><strong>Cancellation Status:</strong> Confirmed</p>
                </div>
                <h3 style="color: #333; margin-top: 30px;">Cancelled Order Details</h3>
                {items_table}
                <p style="color: #555; font-size: 14px; margin-top: 20px;">If you have any questions, please contact our support team.</p>
            </div>
        </body>
        </html>
        """
        return subject, body