import qrcode

from pathlib import Path

from django.conf import settings


def generate_qr(
    document_id
):

    verification_url = (
        f"http://127.0.0.1:8000/"
        f"verify/document/{document_id}/"
    )

    qr = qrcode.make(
        verification_url
    )

    qr_folder = (
        Path(settings.MEDIA_ROOT)
        / 'qr_codes'
    )

    qr_folder.mkdir(
        parents=True,
        exist_ok=True
    )

    qr_path = (
        qr_folder
        / f"{document_id}.png"
    )

    qr.save(qr_path)

    return (
        f"{settings.MEDIA_URL}"
        f"qr_codes/{document_id}.png"
    )