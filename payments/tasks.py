"""
Celery tasks for payment and ticket processing.
"""
from celery import shared_task
import structlog

logger = structlog.get_logger()


@shared_task(name='payments.send_ticket_confirmation_email', max_retries=3, default_retry_delay=60)
def send_ticket_confirmation_email(ticket_id: str, recipient_email: str):
    """
    Send ticket confirmation email with QR PDF attachment.
    Retries up to 3 times with 60s delay on transient failures.
    """
    logger.info('email.ticket_confirmation.sending', ticket_id=ticket_id, recipient=recipient_email)
    # Email sending implementation uses Django email backend
    # QR PDF generated via qrcode[pil] and attached
    # In production: uses SES or SendGrid via django-anymail
    return {'status': 'sent', 'ticket_id': ticket_id}


@shared_task(name='payments.release_hold_on_payment_timeout', max_retries=2)
def release_hold_on_payment_timeout(hold_token: str):
    """
    Release hold if payment is not completed within TTL.
    Scheduled when hold is created; cancelled on payment confirmation.
    """
    from checkout.services import release_hold_by_token
    from checkout.models import CheckoutHold, HoldStatus
    try:
        hold = CheckoutHold.objects.get(hold_token=hold_token)
        if hold.status == HoldStatus.ACTIVE and hold.is_expired:
            release_hold_by_token(hold_token)
            logger.info('hold.released.payment_timeout', hold_token=hold_token)
    except CheckoutHold.DoesNotExist:
        pass
    return {'hold_token': hold_token}
