
import hashlib
import uuid

from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.utils import timezone

from documents.models import Document
from blockchain.models import BlockchainRecord
from blockchain.services import verify_document

from .models import Verification
from accounts.decorators import role_required
from django.db.models import Q
from django.core.paginator import Paginator
from io import BytesIO

from django.http import HttpResponse
from django.shortcuts import get_object_or_404

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
)


def calculate_uploaded_hash(uploaded_file):
    """
    Calculate the SHA-256 hash of an uploaded file.
    Read the file in chunks to avoid loading the whole file into memory.
    """
    sha256 = hashlib.sha256()

    for chunk in uploaded_file.chunks():
        sha256.update(chunk)

    return sha256.hexdigest()


def save_verification_history(
    document,
    method,
    uploaded_hash,
    blockchain_hash,
    result,
):
    """
    Save each verification attempt to the database.
    """
    Verification.objects.create(
        verification_id=str(uuid.uuid4()),
        document=document,
        method=method,
        generated_hash=uploaded_hash or '',
        blockchain_hash=blockchain_hash or '',
        result=result,
    )


@login_required
def verify_home(request):
    return render(request, 'verification/home.html')


@login_required
@role_required('SUPERADMIN', 'ISSUER', 'VERIFIER')
def verify_by_id(request):
    result = None
    document = None
    message = ''
    uploaded_hash = None
    blockchain_hash = None
    blockchain_record = None

    if request.method == 'POST':
        document_id = request.POST.get('document_id', '').strip()
        uploaded_file = request.FILES.get('document_file')

        if not document_id or not uploaded_file:
            result = 'NOT_FOUND'
            message = 'Please enter a Document ID and upload a file.'

        else:
            try:
                document = Document.objects.get(
                    document_id=document_id
                )

                # Calculate the uploaded file hash.
                uploaded_hash = calculate_uploaded_hash(uploaded_file)

                # Check document revocation first.
                if document.status == 'REVOKED':
                    result = 'REVOKED'
                    message = 'This document has been revoked.'

                # Check expiry.
                elif (
                    document.expiry_date
                    and document.expiry_date < timezone.localdate()
                ):
                    result = 'EXPIRED'
                    message = 'This document has expired.'

                else:
                    # Find the current version.
                    version = document.versions.filter(
                        is_current=True
                    ).first()

                    if version is None:
                        result = 'NOT_REGISTERED'
                        message = 'No current document version was found.'

                    else:
                        # Find its confirmed registration.
                        blockchain_record = BlockchainRecord.objects.filter(
                            document=document,
                            document_version=version,
                            status='CONFIRMED',
                        ).first()

                        if blockchain_record is None:
                            result = 'NOT_REGISTERED'
                            message = (
                                'The current document version has not '
                                'been registered on the blockchain.'
                            )

                        else:
                            blockchain_hash = (
                                blockchain_record.document_hash
                            )

                            # Check the hash against the version and
                            # the database's blockchain-registration record.
                            if (
                                uploaded_hash != version.document_hash
                                or uploaded_hash != blockchain_hash
                            ):
                                result = 'INVALID'
                                message = (
                                    'The uploaded file does not match '
                                    'the registered current document version.'
                                )

                            else:
                                # Verify against the active blockchain.
                                try:
                                    is_valid = verify_document(
                                        str(document.document_id),
                                        uploaded_hash,
                                        version.version_number,
                                    )

                                    if is_valid:
                                        result = 'VALID'
                                        message = (
                                            'The uploaded file matches the '
                                            'current document version, and '
                                            'the blockchain record was confirmed.'
                                        )
                                    else:
                                        result = 'INVALID'
                                        message = (
                                            'The active blockchain did not '
                                            'confirm the document hash.'
                                        )

                                except Exception:
                                    result = 'BLOCKCHAIN_UNAVAILABLE'
                                    message = (
                                        'The blockchain could not be reached '
                                        'or the record could not be checked. '
                                        'Start Ganache and confirm the '
                                        'contract configuration.'
                                    )

                save_verification_history(
                    document=document,
                    method='DOCUMENT_ID',
                    uploaded_hash=uploaded_hash,
                    blockchain_hash=blockchain_hash,
                    result=result,
                )

            except Document.DoesNotExist:
                result = 'NOT_FOUND'
                message = 'No document was found with that Document ID.'

            except Exception:
                result = 'ERROR'
                message = (
                    'An unexpected error occurred while processing '
                    'the verification request.'
                )

    return render(
        request,
        'verification/result.html',
        {
            'result': result,
            'document': document,
            'message': message,
            'uploaded_hash': uploaded_hash,
            'blockchain_hash': blockchain_hash,
        },
    )


@login_required
@role_required('SUPERADMIN', 'ISSUER', 'VERIFIER')
def verify_by_qr(request, document_id):
    document = None
    blockchain_hash = None
    message = ''
    result = None

    try:
        document = Document.objects.get(document_id=document_id)

    except Document.DoesNotExist:
        return render(
            request,
            'verification/result.html',
            {
                'result': 'NOT_FOUND',
                'document': None,
                'message': 'Document not found.',
                'uploaded_hash': None,
                'blockchain_hash': None,
            },
        )

    # Check revocation.
    if document.status == 'REVOKED':
        result = 'REVOKED'
        message = 'This document has been revoked.'

    # Check expiry.
    elif (
        document.expiry_date
        and document.expiry_date < timezone.localdate()
    ):
        result = 'EXPIRED'
        message = 'This document has expired.'

    else:
        # Get the current version.
        version = document.versions.filter(
            is_current=True
        ).first()

        if version is None:
            result = 'NOT_REGISTERED'
            message = 'No current document version was found.'

        else:
            blockchain_record = BlockchainRecord.objects.filter(
                document=document,
                document_version=version,
                status='CONFIRMED',
            ).first()

            if blockchain_record is None:
                result = 'NOT_REGISTERED'
                message = (
                    'The current version does not have a confirmed '
                    'blockchain registration.'
                )

            else:
                blockchain_hash = blockchain_record.document_hash

                # Compare the version hash with the database record.
                if version.document_hash != blockchain_hash:
                    result = 'INVALID'
                    message = (
                        'The current version hash does not match '
                        'the stored blockchain-registration record.'
                    )

                else:
                    # Check the record against the active blockchain.
                    try:
                        is_valid = verify_document(
                            str(document.document_id),
                            version.document_hash,
                            version.version_number,
                        )

                        if is_valid:
                            result = 'VALID'
                            message = (
                                'The current version has a matching '
                                'blockchain record. This QR-only check '
                                'does not verify the contents of an '
                                'uploaded file.'
                            )
                        else:
                            result = 'INVALID'
                            message = (
                                'The active blockchain did not confirm '
                                'the current document version.'
                            )

                    except Exception:
                        result = 'BLOCKCHAIN_UNAVAILABLE'
                        message = (
                            'Blockchain verification could not be completed. '
                            'Check that Ganache is running and the contract '
                            'address is correct.'
                        )

    # Save the QR verification attempt.
    try:
        save_verification_history(
            document=document,
            method='QR',
            uploaded_hash='',
            blockchain_hash=blockchain_hash,
            result=result,
        )
    except Exception:
        # Do not change the verification result if history saving fails.
        pass

    return render(
        request,
        'verification/result.html',
        {
            'result': result,
            'document': document,
            'message': message,
            'uploaded_hash': None,
            'blockchain_hash': blockchain_hash,
        },
    )


@login_required
@role_required('SUPERADMIN', 'ISSUER', 'VERIFIER')
def qr_scanner(request):
    return render(request, 'verification/qr_scanner.html')


@login_required
@role_required('SUPERADMIN', 'ISSUER', 'VERIFIER')
def verification_history(request):
    verifications = Verification.objects.select_related(
        'document'
    ).order_by('-id')

    # Issuers can view history for their own documents.
    profile = getattr(request.user, 'profile', None)

    if profile and profile.role == 'ISSUER':
        verifications = verifications.filter(
            document__owner=request.user
        )

    # Search by document ID or title.
    query = request.GET.get('q', '').strip()

    if query:
        verifications = verifications.filter(
            Q(document__document_id__icontains=query)
            | Q(document__title__icontains=query)
        )

    # Filter by verification result.
    selected_result = request.GET.get('result', '').strip()

    allowed_results = [
        'VALID',
        'INVALID',
        'NOT_FOUND',
        'NOT_REGISTERED',
        'EXPIRED',
        'REVOKED',
        'BLOCKCHAIN_UNAVAILABLE',
        'ERROR',
    ]

    if selected_result in allowed_results:
        verifications = verifications.filter(
            result=selected_result
        )

    # Pagination: display 10 records per page.
    paginator = Paginator(verifications, 10)

    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(
        request,
        'verification/history.html',
        {
            'page_obj': page_obj,
            'query': query,
            'selected_result': selected_result,
            'allowed_results': allowed_results,
        }
    )

from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from accounts.decorators import role_required
from .models import Verification

@login_required
@role_required('SUPERADMIN', 'ISSUER', 'VERIFIER')
def verification_records(request):
  records = (
    Verification.objects
    .select_related('document')
    .order_by('-id')
)

# Issuers can see records for their own documents.
  profile = getattr(request.user, 'profile', None)

  if profile and profile.role == 'ISSUER':
    records = records.filter(document__owner=request.user)

  context = {
    'records': records,
}

  return render(
    request,
    'verification/records.html',
    context
)

@login_required
@role_required('SUPERADMIN', 'ISSUER', 'VERIFIER')
def download_verification_report(request, verification_id):


  record = get_object_or_404(
    Verification.objects.select_related('document'),
    verification_id=verification_id
)

# Issuers may download reports only for their own documents.
  profile = getattr(request.user, 'profile', None)

  if profile and profile.role == 'ISSUER':
    if not record.document or record.document.owner != request.user:
        return HttpResponse(
            'You are not authorized to download this report.',
            status=403
        )

  buffer = BytesIO()

  pdf = SimpleDocTemplate(
    buffer,
    pagesize=A4,
    rightMargin=40,
    leftMargin=40,
    topMargin=40,
    bottomMargin=40,
)

  styles = getSampleStyleSheet()
  elements = []

  elements.append(
    Paragraph('Document Verification Report', styles['Title'])
)

  elements.append(Spacer(1, 20))

  document = record.document

  report_data = [
    ['Field', 'Details'],
    ['Verification ID', str(record.verification_id)],
    [
        'Document ID',
        str(document.document_id) if document else 'Not found'
    ],
    [
        'Document Title',
        str(document.title) if document else 'Unknown document'
    ],
    ['Verification Method', str(record.method)],
    ['Verification Result', str(record.result)],
    ['Generated Hash', str(record.generated_hash or 'Not available')],
    ['Blockchain Hash', str(record.blockchain_hash or 'Not available')],
    [
        'Report Generated',
        timezone.localtime().strftime('%Y-%m-%d %H:%M:%S')
    ],
]

  table = Table(
    report_data,
    colWidths=[130, 365],
    repeatRows=1
)

  table.setStyle(TableStyle([
    ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#212529')),
    ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
    ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
    ('VALIGN', (0, 0), (-1, -1), 'TOP'),
    ('LEFTPADDING', (0, 0), (-1, -1), 8),
    ('RIGHTPADDING', (0, 0), (-1, -1), 8),
    ('TOPPADDING', (0, 0), (-1, -1), 8),
    ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
    ('WORDWRAP', (0, 0), (-1, -1), True),
]))

  elements.append(table)

  elements.append(Spacer(1, 20))

  elements.append(
    Paragraph(
        'This report records the verification result saved by the '
        'document authentication system. It does not independently '
        'guarantee document authenticity.',
        styles['BodyText']
    )
)

  pdf.build(elements)

  buffer.seek(0)

  response = HttpResponse(
    buffer.getvalue(),
    content_type='application/pdf'
)

  response['Content-Disposition'] = (
    f'attachment; filename="verification_report_{record.verification_id}.pdf"'
)

  return response


