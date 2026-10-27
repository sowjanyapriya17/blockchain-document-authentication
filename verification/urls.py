from django.urls import path
from . import views

urlpatterns = [
    path('', views.verify_home, name='verify_home'),

    path('id/',views.verify_by_id,name='verify_by_id'),

    path('document/<str:document_id>/',views.verify_by_qr,name='qr_verify' ),
    
    path('history/', views.verification_history, name='verification_history'),

    path('scan/',views.qr_scanner,name='qr_scanner'),
    
    path('records/',views.verification_records,name='verification_records'),
    
    path('report/<str:verification_id>/', views.download_verification_report, name='download_verification_report'),
    
]