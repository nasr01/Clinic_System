"""
Notification Views
Views for doctor notification management
"""
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import render

from accounts.decorators import doctor_required
from patients.models import Notification


@login_required
@doctor_required
def doctor_notifications(request):
    """
    Doctor view to see all notifications
    """
    notifications = Notification.objects.filter(
        recipient=request.user
    ).order_by("-created_at")
    
    unread_count = notifications.filter(is_read=False).count()

    context = {
        "notifications": notifications,
        "unread_count": unread_count,
    }

    return render(request, "patients/doctor_notifications.html", context)


@login_required
@doctor_required
def mark_notification_read(request, notification_id):
    """
    API endpoint to mark a single notification as read
    """
    try:
        notification = Notification.objects.get(
            id=notification_id, 
            recipient=request.user
        )
        notification.is_read = True
        notification.save(update_fields=["is_read"])
        return JsonResponse({"success": True})
    except Notification.DoesNotExist:
        return JsonResponse(
            {"success": False, "error": "Notification not found"}, 
            status=404
        )


@login_required
@doctor_required
def mark_all_notifications_read(request):
    """
    API endpoint to mark all notifications as read
    """
    Notification.objects.filter(
        recipient=request.user, 
        is_read=False
    ).update(is_read=True)
    
    return JsonResponse({"success": True})


@login_required
@doctor_required
def notification_count(request):
    """
    API endpoint to get unread notification count
    """
    count = Notification.objects.filter(
        recipient=request.user, 
        is_read=False
    ).count()
    
    return JsonResponse({"count": count})


@login_required
@doctor_required
def delete_notification(request, notification_id):
    """
    API endpoint to delete a read notification
    """
    try:
        notification = Notification.objects.get(
            id=notification_id, 
            recipient=request.user
        )
        
        if not notification.is_read:
            return JsonResponse(
                {"success": False, "error": "Cannot delete unread notification"}, 
                status=400
            )
        
        notification.delete()
        return JsonResponse({"success": True})
    except Notification.DoesNotExist:
        return JsonResponse(
            {"success": False, "error": "Notification not found"}, 
            status=404
        )


@login_required
@doctor_required
def clear_read_notifications(request):
    """
    API endpoint to delete all read notifications
    """
    deleted_count, _ = Notification.objects.filter(
        recipient=request.user,
        is_read=True
    ).delete()
    
    return JsonResponse({"success": True, "deleted_count": deleted_count})
