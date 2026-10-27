from django.contrib import admin

from .models import BlockchainRecord


@admin.register(BlockchainRecord)
class BlockchainRecordAdmin(admin.ModelAdmin):

    list_display = (
        'document',
        'document_version',
        'status',
        'transaction_hash',
        'block_number',
        'created_at',
    )

    search_fields = (
        'document__document_id',
        'transaction_hash',
    )

    list_filter = (
        'status',
    )