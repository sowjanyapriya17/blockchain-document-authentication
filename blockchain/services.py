import hashlib

from django.db import transaction

from .models import LedgerEntry


GENESIS_HASH = "0" * 64


def calculate_entry_hash(
    document_id,
    version,
    document_hash,
    previous_hash
):

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

    if not isinstance(document_hash, str):
        raise ValueError("Document hash must be a string.")

    try:
        hash_bytes = bytes.fromhex(document_hash)

    except ValueError:
        raise ValueError("Invalid document hash.")

    if len(hash_bytes) != 32:
        raise ValueError("Invalid SHA-256 hash.")

    return document_hash.lower()


def verify_ledger_integrity():

    previous_hash = GENESIS_HASH

    entries = LedgerEntry.objects.order_by("id")

    for entry in entries:

        if entry.previous_entry_hash != previous_hash:
            return False

        expected_hash = calculate_entry_hash(
            entry.document_id,
            entry.version_number,
            entry.document_hash,
            entry.previous_entry_hash
        )

        if entry.entry_hash != expected_hash:
            return False

        previous_hash = entry.entry_hash

    return True


@transaction.atomic
def register_document(
    document_id,
    document_hash,
    version,
    issuer=None
):

    document_id = str(document_id)

    document_hash = validate_document_hash(
        document_hash
    )

    version = int(version)

    if version < 1:
        raise ValueError("Version must be at least 1.")

    if not verify_ledger_integrity():
        raise ValueError(
            "Ledger integrity verification failed."
        )

    existing_entry = LedgerEntry.objects.filter(
        document_id=document_id,
        version_number=version
    ).first()

    if existing_entry:

       if existing_entry.document_hash != document_hash:
        raise ValueError(
            "This document version is already registered "
            "with a different hash."
        )

    # Attach issuer information to older entries
    # when it is available.
       if issuer and existing_entry.issuer_id is None:
        existing_entry.issuer = issuer

        existing_entry.save(
            update_fields=['issuer']
        )

       return {
        "transaction_hash": existing_entry.entry_hash,
        "block_number": existing_entry.id,
        "status": 1,
        "gas_used": 0,
        "contract_address": "LOCAL_HASH_CHAIN"
    }

    previous_entry = (
        LedgerEntry.objects
        .order_by("-id")
        .first()
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
        previous_hash
    )

    entry = LedgerEntry.objects.create(
        document_id=document_id,
        version_number=version,
        document_hash=document_hash,
        previous_entry_hash=previous_hash,
        entry_hash=entry_hash,
        issuer=issuer
    )

    return {
        "transaction_hash": entry.entry_hash,
        "block_number": entry.id,
        "status": 1,
        "gas_used": 0,
        "contract_address": "LOCAL_HASH_CHAIN"
    }


def verify_document(
    document_id,
    document_hash,
    version
):

    document_id = str(document_id)

    document_hash = validate_document_hash(
        document_hash
    )

    version = int(version)

    if version < 1:
        return False

    if not verify_ledger_integrity():
        return False

    entry = LedgerEntry.objects.filter(
        document_id=document_id,
        version_number=version
    ).first()

    if entry is None:
        return False

    return entry.document_hash == document_hash