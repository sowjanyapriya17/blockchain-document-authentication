from django.contrib import admin

from .models import AuditLog


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):

    list_display = (
        'user',
        'document',
        'action',
        'timestamp',
    )

    search_fields = (
        'user__username',
        'document__document_id',
        'description',
    )

    list_filter = (
        'action',
    )