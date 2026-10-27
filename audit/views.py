from django.shortcuts import render


from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.db.models import Q

from accounts.models import Profile
from .models import AuditLog


@login_required
def audit_logs_view(request):

    profile = Profile.objects.filter(user=request.user).first()

    # Only approved Super Admins can view audit logs
    if (
        not request.user.is_superuser
        and (
            profile is None
            or profile.role != 'SUPERADMIN'
            or not profile.is_approved
        )
    ):
        raise PermissionDenied(
            "Only an approved Super Admin can view audit logs."
        )

    logs = AuditLog.objects.select_related(
        'user', 'document'
    ).order_by('-timestamp')

    # Search by username, document ID, action, or description
    query = request.GET.get('q', '').strip()

    if query:
        logs = logs.filter(
            Q(user__username__icontains=query)
            | Q(document__document_id__icontains=query)
            | Q(action__icontains=query)
            | Q(description__icontains=query)
        )

    # Filter by action
    action = request.GET.get('action', '').strip()

    valid_actions = {
        value for value, label in AuditLog.ACTION_CHOICES
    }

    if action in valid_actions:
        logs = logs.filter(action=action)

    context = {
        'logs': logs[:200],
        'query': query,
        'selected_action': action,
        'action_choices': AuditLog.ACTION_CHOICES,
    }

    return render(request, 'audit/audit_logs.html', context)

