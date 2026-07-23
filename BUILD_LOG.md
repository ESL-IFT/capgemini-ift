# Build Log

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
