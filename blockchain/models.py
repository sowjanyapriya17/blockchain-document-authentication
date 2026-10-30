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
    
    
class LedgerEntry(models.Model):

    document_id = models.CharField(max_length=50)

    version_number = models.PositiveIntegerField()

    document_hash = models.CharField(max_length=64)

    issuer = models.ForeignKey(
        'auth.User',
        on_delete=models.PROTECT,
        null=True,
        blank=True
    )

    previous_entry_hash = models.CharField(
        max_length=64,
        default="0" * 64
    )

    entry_hash = models.CharField(
        max_length=64,
        unique=True
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    class Meta:

        ordering = ["id"]

        constraints = [
            models.UniqueConstraint(
                fields=["document_id", "version_number"],
                name="unique_ledger_document_version",
            )
        ]

    def __str__(self):

        return (
            f"{self.document_id} - "
            f"Version {self.version_number}"
        )

