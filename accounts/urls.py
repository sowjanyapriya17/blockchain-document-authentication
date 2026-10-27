from django.urls import path

from . import views


urlpatterns = [

    # User Authentication
    path('signup/',views.signup_view,name='signup'),

    path('login/',views.login_view,name='login'),

    path('logout/',views.logout_view,name='logout'),

    path('profile/',views.profile_view,name='profile'),

    # Role-Based Dashboards
    path('admin-dashboard/',views.admin_dashboard,name='admin_dashboard'),

    path('issuer-dashboard/',views.issuer_dashboard,name='issuer_dashboard'),

    path('verifier-dashboard/',views.verifier_dashboard,name='verifier_dashboard'),
    
    path('manage-users/',views.manage_users,name='manage_users'),

]