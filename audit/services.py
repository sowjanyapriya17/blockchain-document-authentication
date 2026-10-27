from .models import AuditLog


def create_audit_log(
    user,
    action,
    document=None,
    description=''
):

    AuditLog.objects.create(

        user=user,

        document=document,

        action=action,

        description=description

    )