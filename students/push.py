"""Web Push + in-app notification helpers.

Everything here is best-effort and fail-safe: if pywebpush isn't installed, if
VAPID keys aren't configured, or if a push send fails, we swallow the error so
the calling flow (sending an email, saving a payment, etc.) is never affected.
"""
import json

from django.conf import settings

# Guarded import — if the package isn't available, push is simply disabled.
try:
    from pywebpush import webpush, WebPushException
except Exception:  # pragma: no cover
    webpush = None
    WebPushException = Exception


def push_enabled():
    return bool(webpush and getattr(settings, 'VAPID_PRIVATE_KEY', '') and getattr(settings, 'VAPID_PUBLIC_KEY', ''))


def send_web_push(user, title, body='', url='/', icon=''):
    """Send a web-push message to all of a user's subscriptions. Best-effort."""
    if not push_enabled() or user is None:
        return
    try:
        from students.models import PushSubscription
    except Exception:
        return

    vapid_claims = {'sub': 'mailto:' + getattr(settings, 'VAPID_ADMIN_EMAIL', 'admin@example.com')}
    payload = json.dumps({
        'title': title,
        'body': body or '',
        'url': url or '/',
        'icon': icon or '/static/images/email_logo.png',
    })

    for sub in PushSubscription.objects.filter(user=user):
        try:
            webpush(
                subscription_info={
                    'endpoint': sub.endpoint,
                    'keys': {'p256dh': sub.p256dh, 'auth': sub.auth},
                },
                data=payload,
                vapid_private_key=settings.VAPID_PRIVATE_KEY,
                vapid_claims=dict(vapid_claims),
            )
        except WebPushException as exc:
            # 404/410 mean the subscription is dead — clean it up.
            status = getattr(getattr(exc, 'response', None), 'status_code', None)
            if status in (404, 410):
                sub.delete()
        except Exception:
            # Never let a push failure bubble up.
            pass


def notify(user, notification_type, title, message='', icon='notifications',
           action_url='', action_label=''):
    """Create an in-app Notification AND fire a web push. Fully fail-safe."""
    try:
        from students.models import Notification
        Notification.objects.create(
            user=user,
            notification_type=notification_type,
            title=title,
            message=message,
            icon=icon,
            action_url=action_url,
            action_label=action_label,
        )
    except Exception:
        pass

    try:
        send_web_push(user, title, message, url=action_url or '/', icon='')
    except Exception:
        pass
