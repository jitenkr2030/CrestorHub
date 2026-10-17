# CreatorHub — Influencer Marketplace, Management & Agency SaaS

A Django full-stack starter for an all-in-one influencer collaboration platform. Includes public creator discovery, brand campaigns, creator applications, collaboration workflows, deliverable approvals, agency assignment, messaging, notifications, invoice records, workflow analytics, Django admin, and responsive templates.

> **Production note:** This is a substantial runnable MVP starter, not a fully audited production marketplace. Before taking real payments or handling sensitive client data, complete the launch checklist below. Payment processing/escrow, OAuth social integrations, live platform analytics, electronic signatures, automated tax invoices, and full agency team permissions are not implemented.

## Requirements
- Python 3.11–3.13 recommended
- pip and venv
- SQLite for local development; PostgreSQL recommended for production

## Local setup (Linux, Ubuntu, Termux Ubuntu/proot)
```bash
unzip creatorhub.zip
cd creatorhub
python -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt
cp .env.example .env
python manage.py makemigrations core
python manage.py migrate
python manage.py createsuperuser
python manage.py seed_demo
python manage.py check
python manage.py runserver 0.0.0.0:8000
```
Open `http://127.0.0.1:8000`.

Demo users created by `seed_demo`:
- `demo_creator` / `DemoPass123!`
- `demo_brand` / `DemoPass123!`

Demo credentials are only for local testing. Do not deploy demo accounts publicly.

## Main routes
- `/` — marketing landing page
- `/signup/`, `/login/`, `/logout/`
- `/dashboard/` — role-specific dashboard
- `/creators/` — searchable creator directory
- `/campaigns/` — public campaign directory
- `/campaigns/new/` — brand campaign creation
- `/social-accounts/` — creator profile metrics (self-reported)
- `/analytics/` — recorded workflow counts
- `/inbox/`, `/notifications/`, `/invoices/`
- `/admin/` — Django administration
- `/health/` — simple health check

## Role model
- Creator / Influencer: creator profile, social account listing, campaign applications, collaboration deliverables.
- Brand: brand profile, campaign creation, application decisions, deliverable review.
- Agency: agency profile and campaign association model; agencies can manage campaigns assigned to them by an administrator. Full tenant/team permission management should be added before offering agency workspaces commercially.
- Staff/superuser: administrative oversight.

## Production configuration
Set environment variables in the host's secret configuration; do not commit `.env`.
```env
DJANGO_SECRET_KEY=<long-random-secret>
DJANGO_DEBUG=False
DJANGO_ALLOWED_HOSTS=your-domain.example
CSRF_TRUSTED_ORIGINS=https://your-domain.example
DATABASE_URL=postgresql://USER:PASSWORD@HOST:5432/DBNAME
SECURE_SSL_REDIRECT=True
SESSION_COOKIE_SECURE=True
CSRF_COOKIE_SECURE=True
```
Use a managed PostgreSQL database and persistent object storage for user uploads. This starter does not yet configure cloud media storage. Add a suitable email provider by configuring `EMAIL_BACKEND` and `DEFAULT_FROM_EMAIL`.

Build and run:
```bash
pip install -r requirements.txt
python manage.py check --deploy
python manage.py makemigrations core
python manage.py migrate
python manage.py collectstatic --noinput
gunicorn config.wsgi:application --bind 0.0.0.0:8000 --workers 3 --timeout 120
```
Use your host's release/pre-deploy command for migrations; avoid concurrent migration execution from every worker.

## Before public production launch
1. Set a strong random secret, DEBUG=False, allowed hosts and HTTPS settings.
2. Replace console email backend with a real transactional email provider; add email verification and password reset UX.
3. Add automated tests for access control, all role workflows, forms and concurrent application decisions.
4. Add rate limiting, abuse reporting, audit logging, secure account recovery, and spam controls.
5. Add proper agency tenancy: membership invitations, organization-scoped roles, and explicit permissions. Current agency assignment is deliberately basic.
6. Integrate social platform APIs through their official OAuth/API programs; do not treat manually entered metrics as verified.
7. Use a compliant payment provider for checkout/payouts. Do not store card details or claim escrow support until implemented and reviewed.
8. Add signed contracts, dispute policy, refund/cancellation logic, tax and invoice review with qualified professionals.
9. Add object storage, upload validation/scanning, backups, restore drills, monitoring and error tracking.
10. Review privacy policy, terms, data retention/deletion, consent, DPDP Act obligations where applicable, and third-party platform rules.
11. Load-test and conduct an independent security review before handling production users.

## Current MVP limitations
- Creator social numbers are user-entered and not automatically synchronized.
- Invoice records are workflow records only; they do not trigger payments or generate compliant tax invoices.
- Email notifications currently use Django's console backend by default.
- No built-in OAuth social connections, real-time analytics ingestion, escrow, payment gateway, contract e-signature, or mobile application.
- Admin can associate an agency with a campaign; a dedicated agency team/member invitation and client-isolation module remains future work.

## Suggested next development increments
1. Automated tests and API endpoints (Django REST Framework).
2. Agency tenant isolation, team invitations and client workspaces.
3. Official social OAuth integrations and analytics synchronization.
4. Razorpay/Stripe checkout plus webhook-verified payment ledger.
5. Invoice PDF generation, contract templates and audit trail.
