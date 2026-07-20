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
