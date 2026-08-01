# Build Log

## 2026-08-01 — Prevent duplicate school self-registration via Google Place ID
- **Problem:** the same physical school could register multiple times (e.g. "Adani DAV Public School" registered 3× with different coordinator emails) — `SchoolSignUpForm` only checked email uniqueness, never the school itself.
- Added `School.google_place_id` (`students/models.py`, migration `0025_school_google_place_id`, unique + nullable — existing rows have no value and multiple NULLs are allowed).
- `templates/accounts/school_sign_up.html` — the existing Google Places Autocomplete widget now also requests `place_id` and writes it into a new hidden `google_place_id` input on `place_changed`. If the user edits the school name after picking a suggestion, the hidden value is cleared (an edited name isn't guaranteed to still match that place).
- `accounts/forms.py:SchoolSignUpForm` — new hidden `google_place_id` field with `clean_google_place_id` rejecting registration if a School with that place_id already exists ("This school is already registered on IFT. Please sign in instead...").
- `accounts/views.py:school_sign_up` now saves `google_place_id` on the created School.
- Verified end-to-end via Django test client: first registration with a given place_id succeeds; second registration reusing the same place_id is blocked (200 re-render with the error, no User/School created).
- Note: this only prevents *new* duplicates going forward — the 3 existing "Adani DAV Public School" rows (and any other pre-existing dupes) are untouched; that needs a manual data-cleanup pass since merging would affect existing logins/student records.

## 2026-08-01 — Admin panel: school activate/deactivate (single + bulk)
- School model already had `is_active`/`status` (pending/inactive/active) fields, set on self-registration (`accounts/views.py:school_sign_up` creates schools as `status='pending', is_active=False`), but admins had no way to flip it — only the school itself could activate by completing its profile.
- Added `admins/views.py:toggle_school_status` (POST, per-school) and `bulk_toggle_school_status` (POST, list of IDs + `activate` flag), wired at `admins/urls.py` (`school/<id>/toggle-status/`, `schools/bulk-toggle-status/`).
- `templates/admins/user_management/schools_list.html` — added a toggle icon per row, row checkboxes + "select all", and a bulk action bar (Activate/Deactivate Selected) that appears once rows are checked. Added toast notifications (reused the `content_list.html` toast pattern) for success/failure instead of `alert()`/silent reload.
- Fix: removed the native `confirm()` on the single-row toggle — it was silently swallowing clicks with no visual feedback, which looked like the toggle "wasn't working."
- Verified: backend endpoints tested directly via Django test client (single toggle flips is_active/status correctly; bulk toggle activated then deactivated 2 schools, correct JSON + DB state each time).

## 2026-07-29 — TCE school validation working in production (Cloud Run Mumbai proxy)
- **Goal:** Real-time TCE (Tata ClassEdge) partner detection during school registration → ₹1600 (TCE) vs ₹2500. Must be fully API-driven, no manual DB edits.
- **Root cause (diagnosed):** TCE API (`ce-ift.tataclassedge.com/schoolcheck/api/v1/school/validate`) is reachable only from **Indian IPs**. Railway runs in Singapore (egress `34.21.177.21`, GCP) → ConnectTimeout. Cloudflare Worker proxy also failed: for Railway-originated requests the Worker runs at the SIN colo (proven via `request.cf.colo="SIN"` diagnostic), and Smart Placement won't relocate to India (the failing subrequest gives it no latency signal; no way to pin a colo). Note: `railway run curl` misleadingly "worked" because it executes on the local India PC, not the Railway cloud.
- **Fix:** Flask proxy on **Google Cloud Run, asia-south1 (Mumbai)** — India egress reaches TCE in ~1s. Confirmed India *datacenter* IPs are allowed (not residential-only).
  - Proxy source: `C:\Users\kunal\Desktop\tce-proxy-gcp\` (`main.py` Flask + `Dockerfile` + `requirements.txt`).
  - Deployed to GCP project `ift-platform-499910` (account `enpowerlab.ai@gmail.com`, billing linked `0110FF-5060A4-87B695`). Enabled run/cloudbuild/artifactregistry APIs. URL: `https://tce-proxy-222521293721.asia-south1.run.app`. Auth header `X-Proxy-Secret`.
  - `accounts/views.py:school_sign_up` — rewrote TCE block to POST to the proxy (`TCE_PROXY_URL`) with `X-Proxy-Secret`, 20s timeout; dropped the always-failing direct attempt. Sets `School.is_tata_classedge` from `is_tce_school`.
  - `Procfile` — gunicorn `--timeout 60`.
  - Railway env var `TCE_PROXY_URL` set to the Cloud Run URL (`TCE_PROXY_SECRET`/`TCE_API_*` already present).
- **Verified end-to-end:** production registration of a TCE partner school → log `Proxy: status=200 is_tce_school:true`, DB `is_tata_classedge=t`, ~3.7s response.
- **Cleanup:** deleted 5 debug test schools + their users/notifications from prod DB; deleted the obsolete Cloudflare Worker `tce-proxy` (its every-minute cron was needlessly pinging TCE).
- Commits pushed to `techinfinity/main`: `5be3494` (Mumbai proxy), plus timeout/diagnostic commits `81772fb`, `5ad1c6c`, `abbc105`.

## 2026-07-29 — Learning videos made OPTIONAL + notification badge fix
- **Videos no longer mandatory** for students (leader or members). Removed the blocking "Complete Mandatory Videos" popup from `templates/students/submit_idea_v2.html` (the whole `{% if not all_videos_done %}` overlay block). Idea submission was never blocked server-side, so only the UI gate existed.
- `students/views.py`: `_learning_progress()` and `video_completion_status()` no longer filter on `is_mandatory` — they count all active videos and are now purely informational.
- `templates/students/dashboard_v2.html`: removed the "Complete all mandatory videos before submitting your idea" warning banner, renamed the section to "Learning Videos", and the per-video badge now reads "Optional".
- `LearningVideo.is_mandatory` field left in place (default True) but is no longer used for any gating — legacy/cosmetic only. No migration needed.
- Verified (seeded 8 videos, student with 0 watched): submit page 200 with no popup and a usable form; dashboard shows videos with "Optional" label and no nag banner.
- **Notification bell badge**: "Mark all as read" cleared the DB but the server-rendered header badge (`.notif-badge-dot`, pulsing) stayed until a page reload. Added `clearHeaderBadge()` / `decrementHeaderBadge()` in `templates/students/notifications.html` and wired them into the mark-all and per-notification handlers. Backend was already correct (marks notifications read + sets `announcements_read_at`). Verified in-browser: badge 3 → removed instantly without reload, and stays gone after refresh.

## 2026-07-28 — Branded HTML password reset email
- Split `templates/accounts/password_reset_email.html` into a plain-text fallback (`password_reset_email.txt`) and a new branded HTML version (`password_reset_email_html.html`, same purple/gold header + logo + CTA button style as the onboarding emails).
- `accounts/views.py:ForgotPasswordView` now sets `html_email_template_name` (Django's `PasswordResetForm` sends both parts as multipart automatically) and injects `logo_url` via `extra_email_context`/`get_extra_email_context` + `form_valid` override.
- Verified: test-client POST to `/accounts/forgot-password/` produced correct multipart output (plain + HTML) on console backend; HTML rendering visually confirmed in-browser via temporary preview route (added and removed same session). Test user cleaned up after.

## 2026-07-28 — All outgoing mail redirected to hemant@techinfinity.io (dev safety net)
- Added `accounts/email_backend.py:RedirectEmailBackend` — wraps whichever real backend is configured (`EMAIL_BACKEND_REAL`, console locally / ZeptoMail in prod) and rewrites every message's to/cc/bcc to `settings.EMAIL_REDIRECT_TO` before delegating, prefixing the subject with the original intended recipient(s) for traceability. Covers every send path project-wide (onboarding, certificates, password reset, landing inquiries) without touching individual call sites.
- `ift_platform/settings.py` — `EMAIL_BACKEND` now resolves to `RedirectEmailBackend` only when `EMAIL_REDIRECT_TO` is set in env; otherwise falls back to the real backend unchanged.
- `.env` — set `EMAIL_REDIRECT_TO=hemant@techinfinity.io`.
- Verified via shell: `send_mail` to `someoneelse@example.com` arrived addressed to `hemant@techinfinity.io` with subject prefixed `[to: someoneelse@example.com] ...`. Restarted dev server to pick up the setting.
- To turn off: remove/blank `EMAIL_REDIRECT_TO` in `.env`.

## 2026-07-28 — Onboarding emails: HTML templates + student onboarding wired
- Audited every event in the platform for existing/missing transactional emails (accounts, students, admins, ai_assistant, re_evaluation) — see chat history for full table; biggest gaps found: re_evaluation has zero applicant-facing email at any stage, and top 400/100/school-champion designation fires no notification.
- Wired the first gap: `admins/views.py:onboard_student` now sends a credentials email on student onboarding (previously silent), reusing `accounts/emails.py:send_onboard_credentials` (same helper already used for school/evaluator onboarding).
- Replaced the single generic plain-text onboarding template with branded HTML templates per role: `templates/accounts/email_onboard_{student,school,evaluator}.html`, all extending a shared `email_onboard_base.html` (purple/gold IFT branding, credentials box, CTA button). Plain-text `.txt` counterparts kept as the multipart fallback; old generic `email_onboard_credentials.txt` kept as last-resort fallback only.
- `send_onboard_credentials` now sends `EmailMultiAlternatives` (text + HTML) instead of plain `send_mail`; role-specific template resolution via `email_onboard_{role.lower()}.{html,txt}`.
- Verified: Django `check` clean; test-client onboarding POST renders correct subject/template/recipient on console backend; HTML rendering visually confirmed in-browser via a temporary preview route (added and removed same session) for student and evaluator variants.
- Note: `admins/views.py:onboard_school` still creates no `User` account (School record only) — no credentials to email there; separate gap if needed later.
- Added actual IFT crest logo to the email header (was text "ift" before). New asset `static/images/email_logo.png` (320x320, transparent bg, white-ribbon variant — legible on the dark purple header, sourced/resized from `static/landing/IFT Logo_revised-White.png`). `send_onboard_credentials` now passes an absolute `logo_url` (via `SITE_URL` + `staticfiles_storage.url(...)`) since email images must be absolute URLs, not relative static paths. Verified visually in-browser (temporary preview route, removed after).

## 2026-07-28 — Fresh clone: local dev environment setup
- Cloned repo to `/Users/hemantshah/Desktop/AI/Claude/IFT` (preserved pre-existing local `.claude/` dir).
- Created `venv` with Python 3.12.7 (matching `runtime.txt`; system default was 3.14.4) and installed `requirements.txt`.
- Created `.env` from provided project credentials (SECRET_KEY, OPENROUTER_API_KEY, Razorpay test keys, SQLite DB).
- Ran `python manage.py migrate` — all 5 apps' migrations applied cleanly to a fresh SQLite DB.
- Added `.claude/launch.json` (`ift-django` config, port 8000) and started the dev server via the browser preview tool; verified landing page renders correctly (200s on all static assets, screenshot confirmed).

## 2026-07-21 — Certificates: manual per-recipient send with name autocomplete
- Removed the **"Send to all pending"** bulk button from all 4 cards (client sends individually).
- Each card now has **"Send to a student/school"**: a name autocomplete input — type a partial name (e.g. "aar") → dropdown of eligible recipients (name + email, "Sent" tag if already sent) → select → **Send** (real, tracked). Preview kept.
- New views `admins/views.py`: `certificate_suggestions(cert_type)` (JSON, filters `_certificate_recipients` by name/email `?q=`, unsent-first) and `send_single_certificate` (POST cert_type+kind+entity_id → real `_send_certificate`, is_test=False). URLs `certificates/suggest/<cert_type>/` and `certificates/send-one/`. `send_certificates_batch` view left in place but no longer linked from UI.
- Also added a **"View"** action per Recent-activity row → opens that row's certificate PDF (`preview_certificate` with the row's name+type).
- Verified locally (console forced): suggest 'mee'→Meera(unsent)/'aar'→Aarav(sent); send-one creates 1 real row + sent-flag flips; invalid id guarded. Browser: autocomplete dropdown + select + Send-enable confirmed (screenshot).

## 2026-07-21 — Participation certificate: auto-send on submit
- **Participation** now emails **automatically** when a student publishes their idea (`students/views.py:publish_idea`). Other 3 types stay **manual** (per client: rankings vary, send on click).
- New helper `admins/views.py:send_participation_certificate(student, sent_by)` — background daemon thread, dedupes via CertificateIssue (one per student), swallows all errors so it never affects the submission. Reuses `_send_certificate`.
- Verified locally (console backend forced): 1st publish → 1 cert row (full name), 2nd call → 0 (dedupe). Note: on live (ZeptoMail env) this sends a REAL email on every new publish. Pre-existing submitted ideas won't auto-send (hook fires only on new publish) — use the manual batch button for those.

## 2026-07-21 — Certificate emailing feature (admin-triggered)

**Goal:** Email PDF certificates with each student's proper name (Dancing Script, black), triggered manually by super-admin.

**Delivered — all 4 flows:**
- Participation → student (submitted an idea)
- Top 400 → student (`AIEvaluation.is_top_400`)
- Top 100 → student (`rank <= 100`) **and** their school
- School Champion → school (one per school, school name; eligible = schools with a Top-100 student). Confirmed logic: Top 100 issues to student + school.

**Changes:**
- `admins/certificates.py` (new) — Pillow name overlay; CMYK→sRGB via ICC (colour-accurate); returns PDF bytes.
- `static/fonts/DancingScript.ttf` (new) — bundled font.
- `static/certificates/*.jpg` — 4 templates (participation, top100, top400, school-champion).
- `accounts/email_backend.py` — ZeptoMail attachment support (base64).
- `admins/models.py` + migration `0010` — `CertificateIssue` audit model.
- `admins/views.py` — `certificates_view`, `preview_certificate`, `send_test_certificate`, `send_certificates_batch`.
- `admins/urls.py` — 4 routes under `/super-admin/certificates/`.
- `templates/admins/certificates.html` (new) + "Certificates" nav link added to 21 admin sidebars.

**Verified (local, Django test client + console email backend):**
- Page renders 200; correct eligible/pending counts (participation 4, top100 1, top400 2, school_champion 1 on seed).
- All 4 preview endpoints return valid PDFs; ZeptoMail attachment payload base64-correct.
- school-champion PDF capped to ~0.46 MB (from 6.5 MB) via width cap; school name placement correct.
- Batch send emails all eligible + records CertificateIssue (student or school); re-run skips already-sent (dedupe by student/school).
- Admin UI screenshot confirmed (all 4 cards).

**Notes:** `top400.jpg` body text still says "School Champion" (client to confirm); nothing committed yet; LearningVideo/VideoProgress migration still out of scope.
