from patients.models import Notification


def _user_has_role(user):
    return hasattr(user, 'role')


def notification_context(request):
    """
    Context processor to provide notification data to templates
    """
    if (
        request.user.is_authenticated
        and _user_has_role(request.user)
        and request.user.role == 'doctor'
    ):
        try:
            recent_notifications = Notification.objects.filter(
                recipient=request.user
            ).order_by('-created_at')[:5]
            unread_count = Notification.objects.filter(
                recipient=request.user,
                is_read=False
            ).count()
        except Exception:
            recent_notifications = []
            unread_count = 0

        return {
            'recent_notifications': recent_notifications,
            'unread_notification_count': unread_count,
        }
    return {
        'recent_notifications': [],
        'unread_notification_count': 0,
    }
