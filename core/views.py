from decimal import Decimal
from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Q, Count, Sum
from django.http import HttpResponseForbidden, HttpResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone
from django.views.decorators.http import require_POST
from .forms import SignUpForm, CreatorProfileForm, BrandProfileForm, AgencyProfileForm, CampaignForm, ApplicationForm, SocialAccountForm, DeliverableForm, MessageForm
from .models import User, CreatorProfile, BrandProfile, AgencyProfile, Campaign, CampaignApplication, Collaboration, Deliverable, SocialAccount, Invoice, Notification, Message, Review

def home(request):
    campaigns = Campaign.objects.filter(status="open", is_public=True).select_related("brand").order_by("-created_at")[:6]
    creators = CreatorProfile.objects.filter(is_public=True).select_related("user").order_by("-created_at")[:6]
    return render(request, "core/home.html", {"campaigns": campaigns, "creators": creators})

def signup(request):
    if request.user.is_authenticated:
        return redirect("dashboard")
    form = SignUpForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        user = form.save()
        user.email = form.cleaned_data["email"].lower()
        user.display_name = form.cleaned_data["display_name"]
        user.role = form.cleaned_data["role"]
        user.save()
        if user.role == "creator":
            CreatorProfile.objects.create(user=user)
        elif user.role == "brand":
            BrandProfile.objects.create(user=user, company_name=user.display_name or user.username)
        else:
            AgencyProfile.objects.create(user=user, name=user.display_name or user.username)
        login(request, user)
        messages.success(request, "Welcome to CreatorHub. Complete your profile to get started.")
        return redirect("dashboard")
    return render(request, "registration/signup.html", {"form": form})

@login_required
def dashboard(request):
    ctx = {"unread_count": request.user.notifications.filter(is_read=False).count()}
    if request.user.role == "creator":
        profile = CreatorProfile.objects.filter(user=request.user).first()
        ctx.update(profile=profile, applications=CampaignApplication.objects.filter(creator=profile).select_related("campaign", "campaign__brand")[:8] if profile else [],
                   collaborations=Collaboration.objects.filter(application__creator=profile).select_related("application__campaign")[:8] if profile else [],
                   social_accounts=profile.social_accounts.all() if profile else [])
    elif request.user.role == "brand":
        profile = BrandProfile.objects.filter(user=request.user).first()
        ctx.update(profile=profile, campaigns=Campaign.objects.filter(brand=profile).annotate(application_count=Count("applications")).order_by("-created_at")[:8] if profile else [],
                   applications=CampaignApplication.objects.filter(campaign__brand=profile).select_related("campaign", "creator__user")[:10] if profile else [],
                   collaborations=Collaboration.objects.filter(application__campaign__brand=profile).select_related("application__creator__user", "application__campaign")[:8] if profile else [])
    else:
        profile = AgencyProfile.objects.filter(user=request.user).first()
        ctx.update(profile=profile, campaigns=Campaign.objects.filter(agency=profile).annotate(application_count=Count("applications")).order_by("-created_at")[:8] if profile else [],
                   applications=CampaignApplication.objects.filter(campaign__agency=profile).select_related("campaign", "creator__user")[:10] if profile else [],
                   collaborations=Collaboration.objects.filter(application__campaign__agency=profile).select_related("application__creator__user", "application__campaign")[:8] if profile else [])
    return render(request, "core/dashboard.html", ctx)

@login_required
def profile_edit(request):
    if request.user.role == "creator":
        profile, form_class = get_object_or_404(CreatorProfile, user=request.user), CreatorProfileForm
    elif request.user.role == "brand":
        profile, form_class = get_object_or_404(BrandProfile, user=request.user), BrandProfileForm
    else:
        profile, form_class = get_object_or_404(AgencyProfile, user=request.user), AgencyProfileForm
    form = form_class(request.POST or None, instance=profile)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Profile updated.")
        return redirect("dashboard")
    return render(request, "core/form_page.html", {"form": form, "title": "Edit profile"})

@login_required
def social_accounts(request):
    profile = get_object_or_404(CreatorProfile, user=request.user) if request.user.role == "creator" else None
    if profile is None: return HttpResponseForbidden("Creator accounts only.")
    form = SocialAccountForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        item = form.save(commit=False)
        item.creator = profile
        item.save()
        messages.success(request, "Social profile added. Metrics are self-reported until verified through an authorized integration.")
        return redirect("social_accounts")
    return render(request, "core/social_accounts.html", {"form": form, "accounts": profile.social_accounts.all()})

def creator_directory(request):
    qs = CreatorProfile.objects.filter(is_public=True).select_related("user").prefetch_related("social_accounts")
    q = request.GET.get("q", "").strip()
    niche = request.GET.get("niche", "").strip()
    location = request.GET.get("location", "").strip()
    if q:
        qs = qs.filter(Q(user__display_name__icontains=q) | Q(user__username__icontains=q) | Q(bio__icontains=q) | Q(niches__icontains=q))
    if niche: qs = qs.filter(niches__icontains=niche)
    if location: qs = qs.filter(location__icontains=location)
    page = Paginator(qs.order_by("-is_verified", "-created_at"), 12).get_page(request.GET.get("page"))
    return render(request, "core/creator_directory.html", {"page": page, "q": q, "niche": niche, "location": location})

def creator_detail(request, slug):
    profile = get_object_or_404(CreatorProfile.objects.select_related("user").prefetch_related("social_accounts"), slug=slug, is_public=True)
    return render(request, "core/creator_detail.html", {"profile": profile})

def campaign_list(request):
    qs = Campaign.objects.filter(is_public=True, status="open").select_related("brand").order_by("-created_at")
    q = request.GET.get("q", "").strip()
    niche = request.GET.get("niche", "").strip()
    if q: qs = qs.filter(Q(title__icontains=q) | Q(brief__icontains=q) | Q(brand__company_name__icontains=q))
    if niche: qs = qs.filter(niches__icontains=niche)
    page = Paginator(qs, 12).get_page(request.GET.get("page"))
    return render(request, "core/campaign_list.html", {"page": page, "q": q, "niche": niche})

@login_required
def campaign_create(request):
    if request.user.role != "brand": return HttpResponseForbidden("Only brand accounts can create campaigns.")
    brand = get_object_or_404(BrandProfile, user=request.user)
    form = CampaignForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        campaign = form.save(commit=False)
        campaign.brand = brand
        campaign.save()
        messages.success(request, "Campaign saved.")
        return redirect("campaign_detail", slug=campaign.slug)
    return render(request, "core/form_page.html", {"form": form, "title": "Create campaign"})

def campaign_detail(request, slug):
    campaign = get_object_or_404(Campaign.objects.select_related("brand", "agency"), slug=slug)
    is_owner = request.user.is_authenticated and (request.user == campaign.brand.user or (campaign.agency and request.user == campaign.agency.user) or (request.user.is_staff))
    if not campaign.is_public and not is_owner: return HttpResponseForbidden("This campaign is private.")
    application = None
    if request.user.is_authenticated and request.user.role == "creator":
        cp = CreatorProfile.objects.filter(user=request.user).first()
        if cp: application = CampaignApplication.objects.filter(campaign=campaign, creator=cp).first()
    applications = campaign.applications.select_related("creator__user").all() if is_owner else []
    return render(request, "core/campaign_detail.html", {"campaign": campaign, "is_owner": is_owner, "application": application, "applications": applications})

@login_required
def campaign_apply(request, slug):
    if request.user.role != "creator": return HttpResponseForbidden("Only creator accounts can apply.")
    campaign = get_object_or_404(Campaign, slug=slug, is_public=True, status="open")
    creator = get_object_or_404(CreatorProfile, user=request.user)
    if CampaignApplication.objects.filter(campaign=campaign, creator=creator).exists():
        messages.info(request, "You have already applied to this campaign.")
        return redirect("campaign_detail", slug=slug)
    form = ApplicationForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        app = form.save(commit=False)
        app.campaign, app.creator = campaign, creator
        app.save()
        Notification.objects.create(user=campaign.brand.user, title="New campaign application", body=f"{creator} applied to {campaign.title}", url=f"/campaigns/{campaign.slug}/")
        messages.success(request, "Application submitted.")
        return redirect("dashboard")
    return render(request, "core/form_page.html", {"form": form, "title": f"Apply: {campaign.title}"})

def _can_manage_campaign(user, campaign):
    return user.is_staff or user == campaign.brand.user or bool(campaign.agency_id and user == campaign.agency.user)

@login_required
@require_POST
def application_status(request, pk, status):
    app = get_object_or_404(CampaignApplication.objects.select_related("campaign", "creator__user"), pk=pk)
    if not _can_manage_campaign(request.user, app.campaign): return HttpResponseForbidden("Not allowed.")
    if status not in {"shortlisted", "accepted", "rejected"}: return HttpResponseForbidden("Invalid status.")
    app.status = status
    app.save(update_fields=["status", "updated_at"])
    if status == "accepted":
        Collaboration.objects.get_or_create(application=app, defaults={"agreed_rate": app.proposed_rate})
        app.campaign.status = "in_progress"
        app.campaign.save(update_fields=["status", "updated_at"])
    Notification.objects.create(user=app.creator.user, title="Application updated", body=f"Your application for {app.campaign.title} is {status}.", url="/dashboard/")
    messages.success(request, f"Application marked {status}.")
    return redirect("campaign_detail", slug=app.campaign.slug)

@login_required
def collaboration_detail(request, pk):
    collab = get_object_or_404(Collaboration.objects.select_related("application__campaign__brand__user", "application__creator__user", "application__campaign__agency__user"), pk=pk)
    campaign = collab.application.campaign
    allowed = request.user == collab.application.creator.user or request.user == campaign.brand.user or (campaign.agency and request.user == campaign.agency.user) or request.user.is_staff
    if not allowed: return HttpResponseForbidden("Not allowed.")
    deliverables = collab.deliverables.all()
    form = DeliverableForm()
    if request.method == "POST":
        if request.user != collab.application.creator.user and not request.user.is_staff:
            return HttpResponseForbidden("Only the creator can submit deliverables.")
        form = DeliverableForm(request.POST)
        if form.is_valid():
            d = form.save(commit=False); d.collaboration = collab; d.status = "submitted"; d.save()
            collab.status = "submitted"; collab.save(update_fields=["status", "updated_at"])
            Notification.objects.create(user=campaign.brand.user, title="Deliverable submitted", body=f"New submission for {campaign.title}", url=f"/collaborations/{collab.pk}/")
            messages.success(request, "Deliverable submitted.")
            return redirect("collaboration_detail", pk=pk)
    return render(request, "core/collaboration_detail.html", {"collab": collab, "deliverables": deliverables, "form": form, "can_review": request.user == campaign.brand.user or request.user.is_staff})

@login_required
@require_POST
def deliverable_review(request, pk, action):
    d = get_object_or_404(Deliverable.objects.select_related("collaboration__application__campaign__brand", "collaboration__application__creator__user"), pk=pk)
    campaign = d.collaboration.application.campaign
    if request.user != campaign.brand.user and not request.user.is_staff: return HttpResponseForbidden("Not allowed.")
    if action not in {"approved", "revision"}: return HttpResponseForbidden("Invalid action.")
    d.status = action
    d.brand_feedback = request.POST.get("feedback", "")[:4000]
    d.save(update_fields=["status", "brand_feedback", "updated_at"])
    if action == "approved":
        if not d.collaboration.deliverables.exclude(status="approved").exists():
            d.collaboration.status = "completed"
            d.collaboration.save(update_fields=["status", "updated_at"])
    else:
        d.collaboration.status = "revision"
        d.collaboration.save(update_fields=["status", "updated_at"])
    Notification.objects.create(user=d.collaboration.application.creator.user, title="Deliverable reviewed", body=f"{d.title}: {action}", url=f"/collaborations/{d.collaboration_id}/")
    messages.success(request, "Deliverable review saved.")
    return redirect("collaboration_detail", pk=d.collaboration_id)

@login_required
def inbox(request):
    msgs = Message.objects.filter(Q(sender=request.user) | Q(recipient=request.user)).select_related("sender", "recipient", "campaign")
    return render(request, "core/inbox.html", {"messages_list": msgs[:100]})

@login_required
def message_send(request, campaign_id):
    campaign = get_object_or_404(Campaign, pk=campaign_id)
    # Only users attached to this campaign can message one another.
    participants = {campaign.brand.user_id}
    if campaign.agency_id: participants.add(campaign.agency.user_id)
    participants.update(campaign.applications.values_list("creator__user_id", flat=True))
    if request.user.pk not in participants: return HttpResponseForbidden("Not allowed.")
    form = MessageForm(request.POST or None)
    recipient_id = request.POST.get("recipient")
    if request.method == "POST" and form.is_valid():
        try: recipient = User.objects.get(pk=int(recipient_id), pk__in=participants)
        except (User.DoesNotExist, ValueError, TypeError):
            messages.error(request, "Choose a valid campaign participant.")
            return redirect("campaign_detail", slug=campaign.slug)
        if recipient == request.user:
            messages.error(request, "You cannot message yourself.")
            return redirect("campaign_detail", slug=campaign.slug)
        msg = form.save(commit=False); msg.campaign = campaign; msg.sender = request.user; msg.recipient = recipient; msg.save()
        Notification.objects.create(user=recipient, title="New campaign message", body=f"Message about {campaign.title}", url="/inbox/")
        messages.success(request, "Message sent.")
        return redirect("inbox")
    return render(request, "core/message_send.html", {"form": form, "campaign": campaign, "participants": User.objects.filter(pk__in=participants).exclude(pk=request.user.pk)})

@login_required
def notifications(request):
    items = request.user.notifications.all()[:100]
    request.user.notifications.filter(is_read=False).update(is_read=True)
    return render(request, "core/notifications.html", {"items": items})

@login_required
def invoice_list(request):
    qs = Invoice.objects.select_related("collaboration__application__campaign", "collaboration__application__creator__user", "collaboration__application__campaign__brand__user")
    if request.user.role == "creator":
        qs = qs.filter(collaboration__application__creator__user=request.user)
    elif request.user.role == "brand":
        qs = qs.filter(collaboration__application__campaign__brand__user=request.user)
    elif request.user.role == "agency":
        qs = qs.filter(collaboration__application__campaign__agency__user=request.user)
    else:
        if not request.user.is_staff: return HttpResponseForbidden()
    return render(request, "core/invoices.html", {"invoices": qs.order_by("-created_at")[:100]})

@login_required
def analytics(request):
    if request.user.role == "creator":
        profile = get_object_or_404(CreatorProfile, user=request.user)
        apps = CampaignApplication.objects.filter(creator=profile)
        collabs = Collaboration.objects.filter(application__creator=profile)
        context = {"applications_count": apps.count(), "accepted_count": apps.filter(status="accepted").count(),
                   "active_count": collabs.exclude(status__in=["completed", "cancelled"]).count(),
                   "completed_count": collabs.filter(status="completed").count(),
                   "earnings": collabs.filter(status__in=["approved", "completed"]).aggregate(total=Sum("agreed_rate"))["total"] or Decimal("0")}
    elif request.user.role == "brand":
        brand = get_object_or_404(BrandProfile, user=request.user)
        campaigns = Campaign.objects.filter(brand=brand)
        collabs = Collaboration.objects.filter(application__campaign__brand=brand)
        context = {"campaigns_count": campaigns.count(), "applications_count": CampaignApplication.objects.filter(campaign__brand=brand).count(),
                   "active_count": collabs.exclude(status__in=["completed", "cancelled"]).count(),
                   "completed_count": collabs.filter(status="completed").count(),
                   "budget_total": campaigns.aggregate(total=Sum("budget"))["total"] or Decimal("0")}
    else:
        agency = get_object_or_404(AgencyProfile, user=request.user)
        campaigns = Campaign.objects.filter(agency=agency)
        context = {"campaigns_count": campaigns.count(), "applications_count": CampaignApplication.objects.filter(campaign__agency=agency).count(),
                   "active_count": Collaboration.objects.filter(application__campaign__agency=agency).exclude(status__in=["completed", "cancelled"]).count(),
                   "completed_count": Collaboration.objects.filter(application__campaign__agency=agency, status="completed").count()}
    return render(request, "core/analytics.html", {"stats": context})

def health(request):
    return HttpResponse("ok", content_type="text/plain")
