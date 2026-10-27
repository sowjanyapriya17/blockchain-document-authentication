from django.contrib import admin

from .models import Verification


@admin.register(Verification)
class VerificationAdmin(admin.ModelAdmin):

    list_display = (
        'verification_id',
        'document',
        'method',
        'result',
        'verified_at',
    )

    search_fields = (
        'verification_id',
        'document__document_id',
    )

    list_filter = (
        'method',
        'result',
    )