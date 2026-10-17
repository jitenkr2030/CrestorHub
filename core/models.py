import uuid
from django.conf import settings
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils.text import slugify

class User(AbstractUser):
    ROLE_CHOICES = [
        ("creator", "Creator / Influencer"),
        ("brand", "Brand"),
        ("agency", "Agency"),
    ]
    role = models.CharField(max_length=16, choices=ROLE_CHOICES, default="creator", db_index=True)
    display_name = models.CharField(max_length=140, blank=True)
    email = models.EmailField(unique=True)
    REQUIRED_FIELDS = ["email"]
    def __str__(self):
        return self.display_name or self.username

class TimeStamped(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    class Meta:
        abstract = True

class CreatorProfile(TimeStamped):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="creator_profile")
    slug = models.SlugField(max_length=180, unique=True, blank=True)
    bio = models.TextField(blank=True)
    location = models.CharField(max_length=120, blank=True)
    languages = models.CharField(max_length=200, blank=True)
    niches = models.CharField(max_length=300, blank=True, help_text="Comma-separated niches")
    website = models.URLField(blank=True)
    rate_from = models.DecimalField(max_digits=10, decimal_places=2, default=0, validators=[MinValueValidator(0)])
    is_verified = models.BooleanField(default=False)
    is_public = models.BooleanField(default=True)
    def save(self, *args, **kwargs):
        if not self.slug:
            base = slugify(self.user.display_name or self.user.username) or "creator"
            self.slug = f"{base}-{self.user_id or uuid.uuid4().hex[:8]}"
        super().save(*args, **kwargs)
    def __str__(self):
        return self.user.display_name or self.user.username

class SocialAccount(TimeStamped):
    PLATFORM_CHOICES = [
        ("instagram", "Instagram"), ("youtube", "YouTube"), ("facebook", "Facebook"),
        ("tiktok", "TikTok"), ("linkedin", "LinkedIn"), ("x", "X"),
    ]
    creator = models.ForeignKey(CreatorProfile, on_delete=models.CASCADE, related_name="social_accounts")
    platform = models.CharField(max_length=20, choices=PLATFORM_CHOICES)
    handle = models.CharField(max_length=120)
    profile_url = models.URLField(blank=True)
    followers = models.PositiveBigIntegerField(default=0)
    average_views = models.PositiveBigIntegerField(default=0)
    engagement_rate = models.DecimalField(max_digits=5, decimal_places=2, default=0,
        validators=[MinValueValidator(0), MaxValueValidator(100)])
    verified_connection = models.BooleanField(default=False)
    class Meta:
        ordering = ["platform"]
        constraints = [models.UniqueConstraint(fields=["creator", "platform", "handle"], name="unique_creator_platform_handle")]
    def __str__(self):
        return f"{self.platform}: {self.handle}"

class BrandProfile(TimeStamped):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="brand_profile")
    company_name = models.CharField(max_length=180)
    website = models.URLField(blank=True)
    industry = models.CharField(max_length=120, blank=True)
    description = models.TextField(blank=True)
    location = models.CharField(max_length=120, blank=True)
    def __str__(self): return self.company_name

class AgencyProfile(TimeStamped):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="agency_profile")
    name = models.CharField(max_length=180)
    website = models.URLField(blank=True)
    description = models.TextField(blank=True)
    team_members = models.ManyToManyField(settings.AUTH_USER_MODEL, blank=True, related_name="agency_teams")
    def __str__(self): return self.name

class Campaign(TimeStamped):
    STATUS_CHOICES = [
        ("draft", "Draft"), ("open", "Open"), ("in_progress", "In progress"),
        ("completed", "Completed"), ("cancelled", "Cancelled"),
    ]
    brand = models.ForeignKey(BrandProfile, on_delete=models.CASCADE, related_name="campaigns")
    agency = models.ForeignKey(AgencyProfile, on_delete=models.SET_NULL, null=True, blank=True, related_name="campaigns")
    title = models.CharField(max_length=180)
    slug = models.SlugField(max_length=200, blank=True)
    brief = models.TextField()
    objectives = models.CharField(max_length=300, blank=True)
    niches = models.CharField(max_length=300, blank=True)
    target_location = models.CharField(max_length=120, blank=True)
    budget = models.DecimalField(max_digits=12, decimal_places=2, validators=[MinValueValidator(0)])
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)
    deliverables = models.TextField(blank=True, help_text="Describe expected deliverables")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="draft", db_index=True)
    is_public = models.BooleanField(default=True)
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)[:180] + "-" + uuid.uuid4().hex[:6]
        super().save(*args, **kwargs)
    def __str__(self): return self.title

class CampaignApplication(TimeStamped):
    STATUS_CHOICES = [
        ("pending", "Pending"), ("shortlisted", "Shortlisted"), ("accepted", "Accepted"),
        ("rejected", "Rejected"), ("withdrawn", "Withdrawn"),
    ]
    campaign = models.ForeignKey(Campaign, on_delete=models.CASCADE, related_name="applications")
    creator = models.ForeignKey(CreatorProfile, on_delete=models.CASCADE, related_name="applications")
    pitch = models.TextField(blank=True)
    proposed_rate = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="pending", db_index=True)
    class Meta:
        constraints = [models.UniqueConstraint(fields=["campaign", "creator"], name="unique_campaign_creator_application")]
    def __str__(self): return f"{self.creator} → {self.campaign}"

class Collaboration(TimeStamped):
    STATUS_CHOICES = [
        ("active", "Active"), ("submitted", "Submitted"), ("revision", "Revision requested"),
        ("approved", "Approved"), ("completed", "Completed"), ("cancelled", "Cancelled"),
    ]
    application = models.OneToOneField(CampaignApplication, on_delete=models.CASCADE, related_name="collaboration")
    agreed_rate = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])
    due_date = models.DateField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="active", db_index=True)
    contract_notes = models.TextField(blank=True)
    def __str__(self): return f"Collaboration #{self.pk}"

class Deliverable(TimeStamped):
    STATUS_CHOICES = [
        ("pending", "Pending"), ("submitted", "Submitted"), ("revision", "Revision requested"),
        ("approved", "Approved"),
    ]
    collaboration = models.ForeignKey(Collaboration, on_delete=models.CASCADE, related_name="deliverables")
    title = models.CharField(max_length=180)
    description = models.TextField(blank=True)
    due_date = models.DateField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="pending")
    submitted_url = models.URLField(blank=True)
    brand_feedback = models.TextField(blank=True)
    def __str__(self): return self.title

class Message(TimeStamped):
    campaign = models.ForeignKey(Campaign, on_delete=models.CASCADE, related_name="messages")
    sender = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="sent_messages")
    recipient = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="received_messages")
    body = models.TextField(max_length=5000)
    read_at = models.DateTimeField(null=True, blank=True)
    class Meta: ordering = ["created_at"]

class Invoice(TimeStamped):
    STATUS_CHOICES = [("draft", "Draft"), ("issued", "Issued"), ("paid", "Paid"), ("void", "Void")]
    collaboration = models.ForeignKey(Collaboration, on_delete=models.CASCADE, related_name="invoices")
    invoice_number = models.CharField(max_length=40, unique=True, blank=True)
    amount = models.DecimalField(max_digits=12, decimal_places=2, validators=[MinValueValidator(0)])
    currency = models.CharField(max_length=3, default="INR")
    status = models.CharField(max_length=12, choices=STATUS_CHOICES, default="draft")
    due_date = models.DateField(null=True, blank=True)
    issued_at = models.DateTimeField(null=True, blank=True)
    def save(self, *args, **kwargs):
        if not self.invoice_number:
            self.invoice_number = f"CH-{uuid.uuid4().hex[:10].upper()}"
        super().save(*args, **kwargs)

class Review(TimeStamped):
    collaboration = models.ForeignKey(Collaboration, on_delete=models.CASCADE, related_name="reviews")
    reviewer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    reviewee = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="received_reviews")
    rating = models.PositiveSmallIntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)])
    comment = models.TextField(blank=True)
    class Meta:
        constraints = [models.UniqueConstraint(fields=["collaboration", "reviewer"], name="unique_review_per_collaboration_reviewer")]

class Notification(TimeStamped):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="notifications")
    title = models.CharField(max_length=180)
    body = models.CharField(max_length=500, blank=True)
    url = models.CharField(max_length=300, blank=True)
    is_read = models.BooleanField(default=False, db_index=True)
    class Meta: ordering = ["-created_at"]
