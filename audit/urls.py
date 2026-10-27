
from django.urls import path
from . import views

urlpatterns = [
    path(
        'logs/',
        views.audit_logs_view,
        name='audit_logs'
    ),
]
