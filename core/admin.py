from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User, CreatorProfile, SocialAccount, BrandProfile, AgencyProfile, Campaign, CampaignApplication, Collaboration, Deliverable, Message, Invoice, Review, Notification

@admin.register(User)
class CustomUserAdmin(UserAdmin):
    fieldsets = UserAdmin.fieldsets + (("CreatorHub", {"fields": ("role", "display_name")}),)
    list_display = ("username", "email", "display_name", "role", "is_staff")
    list_filter = ("role", "is_staff", "is_active")

for model in [CreatorProfile, SocialAccount, BrandProfile, AgencyProfile, Campaign, CampaignApplication, Collaboration, Deliverable, Message, Invoice, Review, Notification]:
    admin.site.register(model)
