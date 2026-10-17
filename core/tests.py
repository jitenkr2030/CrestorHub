from datetime import date
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from .models import CreatorProfile, BrandProfile, Campaign, CampaignApplication, Collaboration, Deliverable

User = get_user_model()

class CreatorHubTests(TestCase):
    def setUp(self):
        self.creator_user = User.objects.create_user(username="creator1", email="creator@example.com", password="StrongPass123!", role="creator", display_name="Creator One")
        self.creator = CreatorProfile.objects.create(user=self.creator_user, niches="technology, education", location="Delhi")
        self.brand_user = User.objects.create_user(username="brand1", email="brand@example.com", password="StrongPass123!", role="brand", display_name="Brand One")
        self.brand = BrandProfile.objects.create(user=self.brand_user, company_name="Brand One")
        self.campaign = Campaign.objects.create(brand=self.brand, title="Test Campaign", brief="A test brief", budget=10000, status="open", is_public=True)
        self.client = Client()

    def test_home_and_directories(self):
        self.assertEqual(self.client.get(reverse("home")).status_code, 200)
        self.assertEqual(self.client.get(reverse("creator_directory")).status_code, 200)
        self.assertEqual(self.client.get(reverse("campaign_list")).status_code, 200)

    def test_signup_creates_role_profile(self):
        response = self.client.post(reverse("signup"), {
            "username": "newcreator", "display_name": "New Creator", "email": "new@example.com",
            "role": "creator", "password1": "AnotherStrongPass123!", "password2": "AnotherStrongPass123!"
        })
        self.assertEqual(response.status_code, 302)
        self.assertTrue(CreatorProfile.objects.filter(user__username="newcreator").exists())

    def test_creator_can_apply_and_brand_can_accept(self):
        self.client.force_login(self.creator_user)
        response = self.client.post(reverse("campaign_apply", args=[self.campaign.slug]), {"pitch": "I fit this campaign", "proposed_rate": "4500"})
        self.assertEqual(response.status_code, 302)
        app = CampaignApplication.objects.get(campaign=self.campaign, creator=self.creator)
        self.client.force_login(self.brand_user)
        response = self.client.post(reverse("application_status", args=[app.pk, "accepted"]))
        self.assertEqual(response.status_code, 302)
        app.refresh_from_db()
        self.assertEqual(app.status, "accepted")
        self.assertTrue(Collaboration.objects.filter(application=app).exists())

    def test_non_owner_cannot_create_campaign(self):
        self.client.force_login(self.creator_user)
        self.assertEqual(self.client.get(reverse("campaign_create")).status_code, 403)

    def test_creator_directory_search(self):
        response = self.client.get(reverse("creator_directory"), {"q": "Creator One"})
        self.assertContains(response, "Creator One")

    def test_health(self):
        self.assertEqual(self.client.get(reverse("health")).content, b"ok")
