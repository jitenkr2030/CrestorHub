from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from core.models import CreatorProfile, BrandProfile, Campaign, SocialAccount

class Command(BaseCommand):
    help = "Create demo CreatorHub users and a campaign (password: DemoPass123!); do not use demo credentials in production."
    def handle(self, *args, **options):
        User = get_user_model()
        creator, made = User.objects.get_or_create(username="demo_creator", defaults={
            "email": "creator@example.test", "display_name": "Aarav Creates", "role": "creator"})
        if made: creator.set_password("DemoPass123!"); creator.save()
        cp, _ = CreatorProfile.objects.get_or_create(user=creator, defaults={
            "bio": "Demo creator profile for product walkthroughs.", "location": "Delhi, India",
            "niches": "technology, education, lifestyle", "languages": "Hindi, English", "rate_from": 5000})
        SocialAccount.objects.get_or_create(creator=cp, platform="youtube", handle="@aaravcreates",
            defaults={"followers": 12000, "average_views": 4500, "engagement_rate": 4.2})
        brand_user, made = User.objects.get_or_create(username="demo_brand", defaults={
            "email": "brand@example.test", "display_name": "Demo Brand", "role": "brand"})
        if made: brand_user.set_password("DemoPass123!"); brand_user.save()
        brand, _ = BrandProfile.objects.get_or_create(user=brand_user, defaults={
            "company_name": "Demo Brand India", "industry": "Technology", "location": "Delhi"})
        Campaign.objects.get_or_create(title="Launch a new productivity app", brand=brand, defaults={
            "brief": "Create authentic short-form content introducing a productivity app to Indian students and professionals.",
            "objectives": "Awareness and app visits", "niches": "technology, education", "target_location": "India",
            "budget": 25000, "deliverables": "1 short video and 2 story posts", "status": "open", "is_public": True})
        self.stdout.write(self.style.SUCCESS("Demo data ready. Demo users: demo_creator / demo_brand; password: DemoPass123!"))
