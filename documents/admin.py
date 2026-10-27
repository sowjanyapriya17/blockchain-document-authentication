from django.contrib import admin
from .models import Document, DocumentVersion


@admin.register(Document)
class DocumentAdmin(admin.ModelAdmin):

    list_display = (
        'document_id',
        'title',
        'document_type',
        'status',
        'issue_date',
    )

    search_fields = (
        'document_id',
        'title',
    )

    list_filter = (
        'document_type',
        'status',
    )


@admin.register(DocumentVersion)
class DocumentVersionAdmin(admin.ModelAdmin):

    list_display = (
        'document',
        'version_number',
        'is_current',
        'created_at',
    )
    