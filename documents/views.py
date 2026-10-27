from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required

from .forms import DocumentForm
from .services import generate_document_hash
from .models import Document, DocumentVersion
from accounts.decorators import role_required
from .models import Document


from django.contrib import messages

from blockchain.services import register_document
from django.db.models import Count
from blockchain.models import BlockchainRecord

from audit.services import create_audit_log
from verification.qr_service import generate_qr
from django.views.decorators.http import require_POST


@role_required('ISSUER')
def create_document(request):

    if request.method == 'POST':

        form = DocumentForm(
            request.POST,
            request.FILES
        )

        if form.is_valid():

            document = form.save(commit=False)

            document.owner = request.user

            uploaded_file = request.FILES['file']

            document.document_hash = generate_document_hash(
                uploaded_file
            )

            document.save()

            DocumentVersion.objects.create(
                document=document,
                version_number=1,
                file=document.file,
                document_hash=document.document_hash,
                is_current=True
            )
            
            create_audit_log(
                user=request.user,
                document=document,
                action='UPLOAD',
                description=(
                    f"Document {document.document_id} "
                    f"uploaded successfully."
                )
            )

            return redirect(
                'document_detail',
                document_id=document.document_id
            )

    else:

        form = DocumentForm()

    return render(
        request,
        'documents/create.html',
        {'form': form}
    )


@role_required('ISSUER')
def document_list(request):

    documents = Document.objects.filter(
        owner=request.user
    ).order_by('-created_at')

    return render(
        request,
        'documents/list.html',
        {'documents': documents}
    )

@role_required('ISSUER')
def document_detail(request, document_id):

    document = get_object_or_404(
        Document,
        document_id=document_id,
        owner=request.user
    )

    versions = document.versions.all().order_by(
        '-version_number'
    )

    current_version = document.versions.filter(
        is_current=True
    ).first()

    blockchain_record = None
    qr_url = None

    if current_version:
        blockchain_record = BlockchainRecord.objects.filter(
            document=document,
            document_version=current_version,
            status='CONFIRMED'
        ).first()

    if blockchain_record:
        qr_url = generate_qr(document.document_id)

    return render(
        request,
        'documents/detail.html',
        {
            'document': document,
            'versions': versions,
            'current_version': current_version,
            'qr_url': qr_url,
            'blockchain_record': blockchain_record,
        }
    )



@role_required('ISSUER')
@require_POST
def register_on_blockchain(request, document_id):

    document = get_object_or_404(
        Document,
        document_id=document_id,
        owner=request.user
    )

    try:
        version = document.versions.filter(
            is_current=True
        ).first()

        if version is None:
            raise ValueError(
                "No current document version found."
            )

        existing_record = BlockchainRecord.objects.filter(
            document=document,
            document_version=version,
            status='CONFIRMED'
        ).first()

        if existing_record:
            messages.info(
                request,
                "This document version is already registered."
            )

        else:
            transaction_data = register_document(
                document.document_id,
                version.document_hash,
                version.version_number
            )

            BlockchainRecord.objects.create(
                document=document,
                document_version=version,
                document_hash=version.document_hash,
                transaction_hash=transaction_data[
                    'transaction_hash'
                ],
                block_number=transaction_data['block_number'],
                status='CONFIRMED'
            )

            # Record successful blockchain registration
            create_audit_log(
                user=request.user,
                document=document,
                action='BLOCKCHAIN',
                description=(
                    f"Document {document.document_id}, "
                    f"version {version.version_number}, "
                    f"registered on blockchain. "
                    f"Transaction: "
                    f"{transaction_data['transaction_hash']}"
                )
            )

            messages.success(
                request,
                "Document registered successfully!"
            )

    except Exception as error:

        # Record the failure without using an undefined variable
        try:
            create_audit_log(
                user=request.user,
                document=document,
                action='BLOCKCHAIN',
                description=(
                    f"Blockchain registration failed for "
                    f"document {document.document_id}: "
                    f"{error}"
                )
            )
        except Exception:
            pass

        messages.error(
            request,
            f"Blockchain registration failed: {error}"
        )

    return redirect(
        'document_detail',
        document_id=document.document_id
    )
    
    
@role_required('ISSUER')
def create_version(
    request,
    document_id
):

    document = get_object_or_404(
        Document,
        document_id=document_id,
        owner=request.user
    )

    if request.method == 'POST':

        uploaded_file = request.FILES.get(
            'file'
        )

        if uploaded_file:

            current_versions = (
                document.versions.all()
            )

            if current_versions.exists():

                next_version = (
                    max(
                        v.version_number
                        for v in current_versions
                    ) + 1
                )

            else:

                next_version = 1


            current_versions.update(
                is_current=False
            )


            document_hash = (
                generate_document_hash(
                    uploaded_file
                )
            )


            DocumentVersion.objects.create(

                document=document,

                version_number=next_version,

                file=uploaded_file,

                document_hash=document_hash,

                is_current=True

            )


            document.file = uploaded_file

            document.document_hash = document_hash

            document.status = 'ACTIVE'

            document.save()
            create_audit_log(
                user=request.user,
                document=document,
                action='UPDATE',
                description=(
                   f"Document {document.document_id} "
                   f"updated to version {next_version}."
                )
            )
            
            return redirect(
                'document_detail',
                document_id=document_id
            )


    return render(
        request,
        'documents/create_version.html',
        {'document': document}
    )    

@role_required('ISSUER')
@require_POST
def revoke_document(request, document_id):
    document = get_object_or_404(
        Document,
        document_id=document_id,
        owner=request.user
    )

    document.status = 'REVOKED'
    document.save()

    create_audit_log(
        user=request.user,
        document=document,
        action='REVOKE',
        description=(
            f"Document {document.document_id} "
            f"was marked as revoked by the issuer."
        )
    )

    messages.success(request, "Document marked as revoked.")

    return redirect('document_detail', document_id=document_id)

@role_required('ISSUER')
def search_documents(request):

    query = request.GET.get('q', '').strip()

    documents = Document.objects.filter(
        owner=request.user
    )

    if query:
        documents = documents.filter(
            document_id__icontains=query
        ) | documents.filter(
            title__icontains=query
        )
    documents=documents.order_by('-created_at') 

    return render(
        request,
        'documents/list.html',
        {
            'documents': documents,
            'query': query
        }
    )


@role_required('ISSUER')
def registered_documents(request):
    records = BlockchainRecord.objects.filter(
        document__owner=request.user,
        document_version__is_current=True,
        status='CONFIRMED'
    ).select_related(
        'document',
        'document_version'
    ).order_by('-block_number')

    documents = []
    seen_ids = set()

    for record in records:
        if record.document_id in seen_ids:
            continue

        seen_ids.add(record.document_id)

        documents.append({
            'document': record.document,
            'blockchain_record': record,
        })

    return render(
        request,
        'documents/registered_documents.html',
        {'documents': documents}
    )




@role_required('ISSUER')
def version_documents(request):
    documents = (
        Document.objects
        .filter(owner=request.user)
        .annotate(total_versions=Count('versions'))
        .filter(total_versions__gt=1)
        .order_by('-created_at')
    )

    return render(
        request,
        'documents/version_documents.html',
        {'documents': documents}
    )

   
@role_required('ISSUER')
def qr_documents(request):
    records = BlockchainRecord.objects.filter(
        document__owner=request.user,
        document_version__is_current=True,
        status='CONFIRMED'
    ).select_related(
        'document',
        'document_version'
    ).order_by('-block_number')

    documents = []
    seen_ids = set()

    for record in records:
        document = record.document

        if document.pk in seen_ids:
            continue

        seen_ids.add(document.pk)

        qr_url = generate_qr(document.document_id)

        if qr_url:
            documents.append({
                'document': document,
                'blockchain_record': record,
                'qr_url': qr_url,
            })

    return render(
        request,
        'documents/qr_documents.html',
        {'qr_documents': documents}
    )