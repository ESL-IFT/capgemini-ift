import base64
import requests
from django.conf import settings
from django.core.mail.backends.base import BaseEmailBackend
from django.utils.module_loading import import_string


class RedirectEmailBackend(BaseEmailBackend):
    """Wraps the real backend (settings.EMAIL_BACKEND_REAL) and rewrites every
    message's to/cc/bcc to settings.EMAIL_REDIRECT_TO before sending, so all
    outgoing mail lands in one inbox regardless of which view/helper sent it."""

    def __init__(self, fail_silently=False, **kwargs):
        super().__init__(fail_silently=fail_silently, **kwargs)
        real_backend_path = getattr(settings, 'EMAIL_BACKEND_REAL', 'django.core.mail.backends.console.EmailBackend')
        self.real_backend = import_string(real_backend_path)(fail_silently=fail_silently, **kwargs)
        self.redirect_to = settings.EMAIL_REDIRECT_TO

    def send_messages(self, email_messages):
        if not email_messages:
            return 0
        for message in email_messages:
            original_recipients = ', '.join(message.to or [])
            if original_recipients:
                message.subject = f'[to: {original_recipients}] {message.subject}'
            message.to = [self.redirect_to]
            message.cc = []
            message.bcc = []
        return self.real_backend.send_messages(email_messages)


class ZeptoMailBackend(BaseEmailBackend):
    """Custom email backend using Zepto Mail Send Email API (HTTP, not SMTP)."""

    API_URL = 'https://api.zeptomail.in/v1.1/email'

    def __init__(self, fail_silently=False, **kwargs):
        super().__init__(fail_silently=fail_silently, **kwargs)
        self.api_key = getattr(settings, 'ZEPTOMAIL_API_KEY', '') or settings.EMAIL_HOST_PASSWORD

    def send_messages(self, email_messages):
        if not email_messages:
            return 0

        sent = 0
        for message in email_messages:
            try:
                if self._send(message):
                    sent += 1
            except Exception:
                if not self.fail_silently:
                    raise
        return sent

    def _send(self, message):
        from_email = message.from_email or settings.DEFAULT_FROM_EMAIL
        # Parse "Name <email>" format
        if '<' in from_email and '>' in from_email:
            from_name = from_email.split('<')[0].strip().strip('"')
            from_addr = from_email.split('<')[1].strip('>')
        else:
            from_name = 'IFT Platform'
            from_addr = from_email

        to_list = []
        for recipient in message.to:
            if '<' in recipient and '>' in recipient:
                to_name = recipient.split('<')[0].strip().strip('"')
                to_addr = recipient.split('<')[1].strip('>')
            else:
                to_name = recipient.split('@')[0]
                to_addr = recipient
            to_list.append({'email_address': {'address': to_addr, 'name': to_name}})

        payload = {
            'from': {'address': from_addr, 'name': from_name},
            'to': to_list,
            'subject': message.subject,
            'textbody': message.body,
        }

        # If HTML content exists
        if message.content_subtype == 'html':
            payload['htmlbody'] = message.body
        elif hasattr(message, 'alternatives') and message.alternatives:
            for content, mimetype in message.alternatives:
                if mimetype == 'text/html':
                    payload['htmlbody'] = content

        # Attachments (e.g. certificate PDFs). Django stores each attachment as a
        # (filename, content, mimetype) tuple; Zepto wants base64 content inline.
        attachments = []
        for att in getattr(message, 'attachments', []) or []:
            if isinstance(att, tuple):
                filename, content, mimetype = att
            else:  # MIMEBase instance
                filename = att.get_filename() or 'attachment'
                content = att.get_payload(decode=True)
                mimetype = att.get_content_type()
            if isinstance(content, str):
                content = content.encode('utf-8')
            attachments.append({
                'content': base64.b64encode(content).decode('ascii'),
                'mime_type': mimetype or 'application/octet-stream',
                'name': filename or 'attachment',
            })
        if attachments:
            payload['attachments'] = attachments

        headers = {
            'Authorization': self.api_key,
            'Content-Type': 'application/json',
            'Accept': 'application/json',
        }

        response = requests.post(self.API_URL, json=payload, headers=headers, timeout=30)

        if response.status_code in (200, 201):
            return True
        else:
            if not self.fail_silently:
                raise Exception(f'Zepto Mail API error: {response.status_code} - {response.text}')
            return False
