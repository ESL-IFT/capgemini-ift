def launch_confetti(request):
    """Show launch-day celebratory confetti from 29 Jul 2026 11:00 AM IST onwards.

    Server-side gate so all users get a consistent trigger regardless of their
    device clock. The once-per-user behaviour is handled client-side via
    localStorage in templates/partials/launch_confetti.html.
    """
    from datetime import datetime
    from django.utils import timezone
    try:
        launch = timezone.make_aware(datetime(2026, 7, 29, 11, 0, 0))
        return {'launch_confetti_active': timezone.now() >= launch}
    except Exception:
        return {'launch_confetti_active': False}


def unread_notification_count(request):
    if request.user.is_authenticated:
        try:
            from students.models import Notification
            from admins.models import Content
            notif_count = Notification.objects.filter(user=request.user, is_read=False).count()
            announcement_count = Content.objects.filter(
                status='published', content_type='announcement',
                visibility__in=['all', 'students']
            ).count()
            recent_notifs = list(Notification.objects.filter(user=request.user).order_by('-created_at')[:5])
            recent_announcements = list(Content.objects.filter(
                status='published', content_type='announcement',
                visibility__in=['all', 'students']
            ).order_by('-created_at')[:3])
            return {
                'unread_notification_count': notif_count + announcement_count,
                'header_notifications': recent_notifs,
                'header_announcements': recent_announcements,
            }
        except Exception:
            pass
    return {'unread_notification_count': 0, 'header_notifications': [], 'header_announcements': []}


def user_role(request):
    if request.user.is_authenticated:
        try:
            return {'user_role': request.user.profile.role}
        except Exception:
            return {'user_role': 'student'}
    return {'user_role': None}


def student_has_submission(request):
    if request.user.is_authenticated:
        try:
            profile = request.user.profile
            if profile.role == 'student':
                from students.models import IdeaSubmission
                has_sub = IdeaSubmission.objects.filter(student=request.user.student_profile).exists()
                return {'student_has_submission': has_sub}
        except Exception:
            pass
    return {'student_has_submission': False}
