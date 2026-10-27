import hashlib

from django.db import transaction

from .models import LedgerEntry


GENESIS_HASH = "0" * 64


def calculate_entry_hash(
    document_id,
    version,
    document_hash,
    previous_hash,
):
    """
    Calculate the hash of a ledger entry.
    Each entry includes the previous entry's hash.
    """

    entry_data = (
        f"{document_id}|"
        f"{version}|"
        f"{document_hash}|"
        f"{previous_hash}"
    )

    return hashlib.sha256(
        entry_data.encode("utf-8")
    ).hexdigest()


def validate_document_hash(document_hash):
    """
    Ensure the document hash is a valid SHA-256 hash.
    """

    if not isinstance(document_hash, str):
        raise ValueError("Document hash must be a string.")

    try:
        hash_bytes = bytes.fromhex(document_hash)
    except ValueError:
        raise ValueError("Document hash must be hexadecimal.")

    if len(hash_bytes) != 32:
        raise ValueError(
            "Document hash must be exactly 32 bytes."
        )

    return document_hash.lower()


def verify_ledger_integrity():
    """
    Verify the previous-hash links and entry hashes
    throughout the entire local ledger.
    """

    previous_hash = GENESIS_HASH

    entries = LedgerEntry.objects.order_by("id")

    for entry in entries:

        # Each entry must point to the preceding entry.
        if entry.previous_entry_hash != previous_hash:
            return False

        # Recalculate the entry's hash.
        expected_hash = calculate_entry_hash(
            entry.document_id,
            entry.version_number,
            entry.document_hash,
            entry.previous_entry_hash,
        )

        if entry.entry_hash != expected_hash:
            return False

        previous_hash = entry.entry_hash

    return True


@transaction.atomic
def register_document(document_id, document_hash, version):
    """
    Register a document version in the local hash-chain ledger.
    No Ganache or external blockchain connection is required.
    """

    document_id = str(document_id)
    document_hash = validate_document_hash(document_hash)
    version = int(version)

    if version < 1:
        raise ValueError("Version must be at least 1.")

    # Refuse to add records to an already inconsistent ledger.
    if not verify_ledger_integrity():
        raise ValueError(
            "Ledger integrity check failed. "
            "Registration has been stopped."
        )

    # Prevent duplicate registration of the same version.
    existing_entry = LedgerEntry.objects.filter(
        document_id=document_id,
        version_number=version,
    ).first()

    if existing_entry:

        if existing_entry.document_hash != document_hash:
            raise ValueError(
                "This document version is already registered "
                "with a different hash."
            )

        return {
            "transaction_hash": existing_entry.entry_hash,
            "block_number": existing_entry.id,
            "status": 1,
            "gas_used": 0,
            "contract_address": "LOCAL_HASH_CHAIN",
        }

    # Link the new entry to the latest ledger entry.
    previous_entry = (
        LedgerEntry.objects.order_by("-id").first()
    )

    previous_hash = (
        previous_entry.entry_hash
        if previous_entry
        else GENESIS_HASH
    )

    entry_hash = calculate_entry_hash(
        document_id,
        version,
        document_hash,
        previous_hash,
    )

    entry = LedgerEntry.objects.create(
        document_id=document_id,
        version_number=version,
        document_hash=document_hash,
        previous_entry_hash=previous_hash,
        entry_hash=entry_hash,
    )

    return {
        "transaction_hash": entry.entry_hash,
        "block_number": entry.id,
        "status": 1,
        "gas_used": 0,
        "contract_address": "LOCAL_HASH_CHAIN",
    }


def verify_document(document_id, document_hash, version):
    """
    Verify a document version against the local ledger.
    Also checks the integrity of the complete ledger.
    """

    document_id = str(document_id)
    document_hash = validate_document_hash(document_hash)
    version = int(version)

    if version < 1:
        return False

    # Check the entire hash chain first.
    if not verify_ledger_integrity():
        return False

    # Find the registered document version.
    entry = LedgerEntry.objects.filter(
        document_id=document_id,
        version_number=version,
    ).first()

    if entry is None:
        return False

    # Compare the uploaded/current version hash.
    if entry.document_hash != document_hash:
        return False

    # Confirm the selected entry's hash independently.
    expected_hash = calculate_entry_hash(
        entry.document_id,
        entry.version_number,
        entry.document_hash,
        entry.previous_entry_hash,
    )

    return entry.entry_hash == expected_hash