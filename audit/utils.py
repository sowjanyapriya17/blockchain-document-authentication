
from .models import AuditLog


def create_audit_log(
    user=None,
    document=None,
    action=None,
    description=''
):
    """
    Create an audit log entry for an important system action.
    """

    if action not in dict(AuditLog.ACTION_CHOICES):
        raise ValueError("Invalid audit log action.")

    return AuditLog.objects.create(
        user=user if getattr(user, 'is_authenticated', False) else None,
        document=document,
        action=action,
        description=description
    )
