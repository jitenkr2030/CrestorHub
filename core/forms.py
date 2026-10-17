from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import User, CreatorProfile, BrandProfile, AgencyProfile, Campaign, CampaignApplication, SocialAccount, Deliverable, Message

class SignUpForm(UserCreationForm):
    email = forms.EmailField()
    display_name = forms.CharField(max_length=140)
    role = forms.ChoiceField(choices=User.ROLE_CHOICES)
    class Meta:
        model = User
        fields = ("username", "display_name", "email", "role", "password1", "password2")
    def clean_email(self):
        email = self.cleaned_data["email"].lower()
        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError("An account with this email already exists.")
        return email

class CreatorProfileForm(forms.ModelForm):
    class Meta:
        model = CreatorProfile
        fields = ["bio", "location", "languages", "niches", "website", "rate_from", "is_public"]
        widgets = {"bio": forms.Textarea(attrs={"rows": 4})}

class BrandProfileForm(forms.ModelForm):
    class Meta:
        model = BrandProfile
        fields = ["company_name", "website", "industry", "description", "location"]
        widgets = {"description": forms.Textarea(attrs={"rows": 4})}

class AgencyProfileForm(forms.ModelForm):
    class Meta:
        model = AgencyProfile
        fields = ["name", "website", "description"]
        widgets = {"description": forms.Textarea(attrs={"rows": 4})}

class SocialAccountForm(forms.ModelForm):
    class Meta:
        model = SocialAccount
        fields = ["platform", "handle", "profile_url", "followers", "average_views", "engagement_rate"]

class CampaignForm(forms.ModelForm):
    class Meta:
        model = Campaign
        fields = ["title", "brief", "objectives", "niches", "target_location", "budget", "start_date", "end_date", "deliverables", "status", "is_public"]
        widgets = {
            "brief": forms.Textarea(attrs={"rows": 5}),
            "deliverables": forms.Textarea(attrs={"rows": 3}),
            "start_date": forms.DateInput(attrs={"type": "date"}),
            "end_date": forms.DateInput(attrs={"type": "date"}),
        }
    def clean(self):
        cleaned = super().clean()
        start, end = cleaned.get("start_date"), cleaned.get("end_date")
        if start and end and end < start:
            self.add_error("end_date", "End date must be on or after the start date.")
        return cleaned

class ApplicationForm(forms.ModelForm):
    class Meta:
        model = CampaignApplication
        fields = ["pitch", "proposed_rate"]
        widgets = {"pitch": forms.Textarea(attrs={"rows": 4})}

class DeliverableForm(forms.ModelForm):
    class Meta:
        model = Deliverable
        fields = ["title", "description", "due_date", "submitted_url"]
        widgets = {"due_date": forms.DateInput(attrs={"type": "date"}), "description": forms.Textarea(attrs={"rows": 3})}

class MessageForm(forms.ModelForm):
    class Meta:
        model = Message
        fields = ["body"]
        widgets = {"body": forms.Textarea(attrs={"rows": 3, "placeholder": "Write a campaign message..."})}
