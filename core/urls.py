from django.contrib.auth import views as auth_views
from django.urls import path
from . import views

urlpatterns = [
    path("", views.home, name="home"),
    path("health/", views.health, name="health"),
    path("signup/", views.signup, name="signup"),
    path("login/", auth_views.LoginView.as_view(template_name="registration/login.html"), name="login"),
    path("logout/", auth_views.LogoutView.as_view(), name="logout"),
    path("dashboard/", views.dashboard, name="dashboard"),
    path("profile/edit/", views.profile_edit, name="profile_edit"),
    path("social-accounts/", views.social_accounts, name="social_accounts"),
    path("creators/", views.creator_directory, name="creator_directory"),
    path("creators/<slug:slug>/", views.creator_detail, name="creator_detail"),
    path("campaigns/", views.campaign_list, name="campaign_list"),
    path("campaigns/new/", views.campaign_create, name="campaign_create"),
    path("campaigns/<slug:slug>/", views.campaign_detail, name="campaign_detail"),
    path("campaigns/<slug:slug>/apply/", views.campaign_apply, name="campaign_apply"),
    path("applications/<int:pk>/<str:status>/", views.application_status, name="application_status"),
    path("collaborations/<int:pk>/", views.collaboration_detail, name="collaboration_detail"),
    path("deliverables/<int:pk>/<str:action>/", views.deliverable_review, name="deliverable_review"),
    path("campaigns/<int:campaign_id>/message/", views.message_send, name="message_send"),
    path("inbox/", views.inbox, name="inbox"),
    path("notifications/", views.notifications, name="notifications"),
    path("invoices/", views.invoice_list, name="invoice_list"),
    path("analytics/", views.analytics, name="analytics"),
]
