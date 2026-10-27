from django.db import models


class BlockchainRecord(models.Model):

    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('CONFIRMED', 'Confirmed'),
        ('FAILED', 'Failed'),
    ]

    document = models.ForeignKey(
        'documents.Document',
        on_delete=models.CASCADE
    )

    document_version = models.ForeignKey(
        'documents.DocumentVersion',
        on_delete=models.CASCADE
    )

    document_hash = models.CharField(
        max_length=64
    )

    transaction_hash = models.CharField(
        max_length=255,
        blank=True
    )

    block_number = models.BigIntegerField(
        null=True,
        blank=True
    )

    blockchain_timestamp = models.DateTimeField(
        null=True,
        blank=True
    )

    status = models.CharField(
        max_length=30,
        choices=STATUS_CHOICES,
        default='PENDING'
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    def __str__(self):

        return self.document.document_id