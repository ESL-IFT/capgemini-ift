# Build Log

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
