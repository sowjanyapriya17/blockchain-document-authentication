from django.urls import path
from . import views


urlpatterns = [

path('create/',views.create_document,name='create_document'),

path('list/',views.document_list,name='document_list'),

path('search/',views.search_documents,name='search_documents'),

path('qr-codes/',views.qr_documents,name='qr_documents'),

path('versions/', views.version_documents, name='version_documents'),

path('registered/', views.registered_documents, name='registered_documents'),
    
path('<str:document_id>/blockchain/',views.register_on_blockchain,name='register_blockchain'),

path('<str:document_id>/version/create/', views.create_version, name='create_version'),
    
path('<str:document_id>/revoke/', views.revoke_document, name='revoke_document'),    

path('<str:document_id>/',views.document_detail,name='document_detail'),

]