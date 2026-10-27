from django.shortcuts import render, redirect, get_object_or_404

from django.contrib.auth.models import User
from django.db.models import Q
from django.core.exceptions import PermissionDenied
from django.contrib.auth import (
    authenticate,
    login,
    logout
)

from django.contrib.auth.decorators import login_required

from django.contrib import messages

from .forms import SignupForm

from django.core.exceptions import PermissionDenied

from .models import Profile
from accounts.decorators import role_required

from django.db.models import Count
from documents.models import Document
from blockchain.models import BlockchainRecord
from audit.services import create_audit_log
from django.utils import timezone
from datetime import timedelta


def signup_view(request):

    if request.method == 'POST':

        form = SignupForm(request.POST)

        if form.is_valid():

            user = form.save(commit=False)

            user.set_password(
                form.cleaned_data['password']
            )

            user.save()

            selected_role = form.cleaned_data['role']

            Profile.objects.update_or_create(
                user=user,
                defaults={
                    'role': selected_role,
                    'is_approved': False
                }
            )

            messages.success(
                request,
                "Account created successfully. "
                "Please wait for SUPERADMIN approval."
            )

            return redirect('login')

    else:

        form = SignupForm()

    return render(
        request,
        'accounts/signup.html',
        {'form': form}
    )



def login_view(request):

    if request.method == 'POST':

        username = request.POST.get('username')
        password = request.POST.get('password')

        user = authenticate(
            request,
            username=username,
            password=password
        )

        if user is not None:

            # Superusers must have a profile too.
            profile, created = Profile.objects.get_or_create(
                user=user,
                defaults={
                    'role': 'SUPERADMIN' if user.is_superuser else 'VERIFIER',
                    'is_approved': user.is_superuser
                }
            )

            # Only Django superusers are automatically treated as
            # administrators. Ordinary users need an assigned role.
            if user.is_superuser:
                profile.role = 'SUPERADMIN'
                profile.is_approved = True
                profile.save()

            if not profile.is_approved:
                messages.error(
                    request,
                    "Your account is awaiting approval."
                )

                return redirect('login')

            login(request, user)
            
            create_audit_log(
                user=user,
                action='LOGIN',
                description='User logged in successfully.'
            )

            if profile.role == 'SUPERADMIN':
                return redirect('admin_dashboard')

            elif profile.role == 'ISSUER':
                return redirect('issuer_dashboard')

            elif profile.role == 'VERIFIER':
                return redirect('verifier_dashboard')

            messages.error(
                request,
                "Your account does not have a valid role."
            )

            logout(request)

            return redirect('login')

        messages.error(
            request,
            "Invalid username or password."
        )

    return render(request, 'accounts/login.html')




@login_required
def logout_view(request):

    logout(request)

    return redirect('login')


@login_required
def profile_view(request):

    return render(
        request,
        'accounts/profile.html'
    )
    



@login_required
def admin_dashboard(request):

    # Allow only the Super Admin
    profile = Profile.objects.filter(user=request.user).first()

    if not request.user.is_superuser:
        if not profile or profile.role != 'SUPERADMIN':
            raise PermissionDenied(
                "Only Super Admins can access this dashboard."
            )

    # User statistics
    profiles = Profile.objects.all()

    total_users = profiles.count()
    pending_users = profiles.filter(is_approved=False).count()
    approved_users = profiles.filter(is_approved=True).count()

    total_issuers = profiles.filter(role='ISSUER').count()
    total_verifiers = profiles.filter(role='VERIFIER').count()

    # Document statistics
    total_documents = Document.objects.count()

    active_documents = Document.objects.filter(
        status='ACTIVE'
    ).count()

    revoked_documents = Document.objects.filter(
        status='REVOKED'
    ).count()

    expired_documents = Document.objects.filter(
        status='EXPIRED'
    ).count()

    # Blockchain statistics
    confirmed_records = BlockchainRecord.objects.filter(
        status='CONFIRMED'
    )

    confirmed_documents = confirmed_records.values(
        'document_id'
    ).distinct().count()

    total_blockchain_records = BlockchainRecord.objects.count()

    pending_registrations = BlockchainRecord.objects.filter(
        status='PENDING'
    ).count()

    failed_registrations = BlockchainRecord.objects.filter(
        status='FAILED'
    ).count()

    # Documents that do not have a confirmed blockchain record
    documents_without_confirmation = Document.objects.exclude(
        id__in=confirmed_records.values('document_id')
    ).count()

    context = {
        # User statistics
        'total_users': total_users,
        'pending_users': pending_users,
        'approved_users': approved_users,
        'total_issuers': total_issuers,
        'total_verifiers': total_verifiers,

        # Document statistics
        'total_documents': total_documents,
        'active_documents': active_documents,
        'revoked_documents': revoked_documents,
        'expired_documents': expired_documents,

        # Blockchain statistics
        'confirmed_documents': confirmed_documents,
        'total_blockchain_records': total_blockchain_records,
        'pending_registrations': pending_registrations,
        'failed_registrations': failed_registrations,
        'documents_without_confirmation':
            documents_without_confirmation,
    }

    return render(
        request,
        'accounts/admin_dashboard.html',
        context
    )


@login_required
def issuer_dashboard(request):

    # Check issuer role and approval
    profile = Profile.objects.filter(
        user=request.user
    ).first()

    if (
        not profile
        or profile.role != 'ISSUER'
        or not profile.is_approved
    ):
        raise PermissionDenied

    # Get documents belonging to this issuer
    documents = Document.objects.filter(
        owner=request.user
    )

    # Total documents
    total_documents = documents.count()

    # Count documents whose current version has a confirmed
    # blockchain registration
    registered_documents = BlockchainRecord.objects.filter(
        document__owner=request.user,
        document_version__is_current=True,
        status='CONFIRMED'
    ).values('document_id').distinct().count()

    # Documents awaiting registration
    pending_documents = max(
        total_documents - registered_documents,
        0
    )

    # Documents expiring within the next 30 days
    today = timezone.localdate()

    expiring_documents = documents.filter(
        expiry_date__gte=today,
        expiry_date__lte=today + timedelta(days=30),
        status='ACTIVE'
    ).order_by('expiry_date')

    # Send data to the dashboard template
    context = {
        'total_documents': total_documents,
        'registered_documents': registered_documents,
        'pending_documents': pending_documents,
        'expiring_documents': expiring_documents,
    }

    return render(
        request,
        'accounts/issuer_dashboard.html',
        context
    )



from verification.models import Verification

@login_required
def verifier_dashboard(request):

  profile = getattr(request.user, 'profile', None)

  if not profile or profile.role != 'VERIFIER':
    return redirect('login')

  if not profile.is_approved:
    return redirect('login')

# Count all saved verification attempts.
  total_verifications = Verification.objects.count()

# Count successful verifications.
  successful_verifications = Verification.objects.filter(
    result='VALID'
).count()

# Count unsuccessful verification attempts.
  failed_verifications = Verification.objects.filter(
    Q(result='INVALID') |
    Q(result='EXPIRED') |
    Q(result='REVOKED') |
    Q(result='NOT_REGISTERED') |
    Q(result='NOT_FOUND') |
    Q(result='BLOCKCHAIN_UNAVAILABLE') |
    Q(result='ERROR')
).count()

  context = {
    'total_verifications': total_verifications,
    'successful_verifications': successful_verifications,
    'failed_verifications': failed_verifications,
}

  return render(
    request,
    'accounts/verifier_dashboard.html',
    context
  )




@role_required('SUPERADMIN')
def superadmin_dashboard(request):
    profiles = Profile.objects.select_related('user').all()

    context = {
        'total_users': profiles.count(),
        'pending_users': profiles.filter(
            is_approved=False
        ).count(),
        'approved_users': profiles.filter(
            is_approved=True
        ).count(),
        'profiles': profiles,
    }

    return render(
        request,
        'accounts/superadmin_dashboard.html',
        context
    )


@login_required
def manage_users(request):

    # Check Super Admin permission
    profile = Profile.objects.filter(
        user=request.user
    ).first()

    if not request.user.is_superuser:
        if not profile or profile.role != 'SUPERADMIN':
            raise PermissionDenied(
                "Only Super Admins can manage users."
            )

        if not profile.is_approved:
            raise PermissionDenied(
                "Your account has not been approved."
            )

    # Get all user profiles except the logged-in administrator
    profiles = Profile.objects.select_related(
        'user'
    ).exclude(
        user=request.user
    ).order_by('-user__date_joined')

    # Search by username, email, first name, or last name
    search_query = request.GET.get('q', '').strip()

    if search_query:
        profiles = profiles.filter(
            Q(user__username__icontains=search_query)
            | Q(user__email__icontains=search_query)
            | Q(user__first_name__icontains=search_query)
            | Q(user__last_name__icontains=search_query)
        )

    # Filter by role
    role_filter = request.GET.get('role', '').strip()

    allowed_roles = [
        'SUPERADMIN',
        'ISSUER',
        'VERIFIER',
    ]

    if role_filter in allowed_roles:
        profiles = profiles.filter(role=role_filter)

    # Filter by approval status
    status_filter = request.GET.get(
        'status', ''
    ).strip()

    if status_filter == 'approved':
        profiles = profiles.filter(is_approved=True)

    elif status_filter == 'pending':
        profiles = profiles.filter(is_approved=False)

    # Handle approval, rejection, and role changes
    if request.method == 'POST':

        user_id = request.POST.get('user_id')
        action = request.POST.get('action', '').strip()

        target_profile = get_object_or_404(
            Profile.objects.select_related('user'),
            user_id=user_id
        )

        target_user = target_profile.user

        # Do not allow changing the current administrator
        if target_user == request.user:
            messages.error(
                request,
                "You cannot change your own account here."
            )
            return redirect('manage_users')

        # Protect Django superuser accounts
        if target_user.is_superuser:
            messages.error(
                request,
                "Django superuser accounts cannot be modified here."
            )
            return redirect('manage_users')

        # Approve a user
        if action == 'approve':

            target_profile.is_approved = True
            target_profile.save(
                update_fields=['is_approved']
            )

            messages.success(
                request,
                f"{target_user.username} has been approved."
            )

        # Reject or suspend a user
        elif action == 'reject':

            target_profile.is_approved = False
            target_profile.save(
                update_fields=['is_approved']
            )

            messages.success(
                request,
                f"{target_user.username} has been marked as unapproved."
            )

        # Change a user's role
        elif action == 'change_role':

            new_role = request.POST.get(
                'role', ''
            ).strip()

            if new_role not in ['ISSUER', 'VERIFIER']:

                messages.error(
                    request,
                    "Invalid role selected."
                )

            else:

                target_profile.role = new_role
                target_profile.save(
                    update_fields=['role']
                )

                messages.success(
                    request,
                    f"{target_user.username}'s role has been updated."
                )

        else:

            messages.error(
                request,
                "Invalid user management action."
            )

        return redirect('manage_users')

    # Statistics for the filtered results
    context = {
        'profiles': profiles,
        'search_query': search_query,
        'role_filter': role_filter,
        'status_filter': status_filter,
        'result_count': profiles.count(),
    }

    return render(
        request,
        'accounts/manage_users.html',
        context
    )

  