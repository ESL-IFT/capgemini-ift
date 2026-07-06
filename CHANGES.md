# CHANGES — School Dashboard Enhancements

Date: 2026-07-06
Scope: School dashboard widgets + school profile "Designated Teacher" fields. All changes are additive; no existing view/logic was modified or removed (except one pre-existing crash bug fix in `students/admin.py`).

---

## Files Changed

### 1. `students/models.py` — School model
Added 2 fields after `principal_email`:
```python
designated_teacher_name = models.CharField(max_length=150, blank=True)
designated_teacher_mobile = models.CharField(max_length=15, blank=True)
```

### 2. `students/migrations/0016_learningvideo_school_designated_teacher_mobile_and_more.py` (NEW)
Migration for the 2 new School fields (plus auto-detected pending alterations for LearningVideo/VideoProgress/choices that were already un-migrated in the repo).

### 3. `students/admin.py` — pre-existing bug fix
Line ~88, `IdeaSuggestionAdmin.list_display` referenced `'field_name'`, which does not exist on the `IdeaSuggestion` model (it uses a `changes` JSONField). This caused `admin.E108` and Django refused to start (`migrate`/`runserver` both blocked). Removed the invalid entry:
```python
# before
list_display = ('submission', 'suggested_by', 'field_name', 'status', 'created_at')
# after
list_display = ('submission', 'suggested_by', 'status', 'created_at')
```

### 4. `students/views.py`
- `school_dashboard` view: **added context only** (existing calculations untouched):
  - `grade_data` — submissions grouped by student grade
  - `paid_count`, `unpaid_count` — payment status (payment not built yet → paid = 0)
  - `funnel` — Registered / Payment / Team Formation / Idea Submission (this school)
  - `team_pie` — Total Registration / Paid / Working on Ideas / Ideas Submitted (this school)
  - `platform_schools`, `platform_students`, `platform_teams`, `platform_ideas` — platform-wide
  - `days_left`, `submission_deadline` — from `admins.Phase` (name contains "submission"), fallback 2026-10-15
- 2 NEW views:
  - `school_payments` — student-wise payment + submission status table (for follow-ups)
  - `platform_live_stats` — JSON endpoint feeding the live ticker

### 5. `students/urls.py` — 2 NEW routes
```python
path('school/payments/', views.school_payments, name='school_payments'),
path('school/live-stats/', views.platform_live_stats, name='platform_live_stats'),
```

### 6. `templates/students/school_dashboard.html`
- Added Chart.js CDN (`chart.js@4.4.1`) in `<head>`.
- **Live ticker** (top): days left for submission, schools participating, students participating, deadline. Auto-refreshes daily via `students:platform_live_stats`.
- **Platform-wide KPI row**: Schools Participated / Students / Teams / Ideas Registered (across platform).
- **Registration & Payment widget** + "View more" link to `students:school_payments`.
- **Grade-wise Submissions** bar chart (`gradeChart`).
- **Live Status** doughnut (`funnelChart`): Registered / Payment / Team Formation / Idea Submission.
- **Team Formation Status**: replaced old SVG donut with a **pie chart** (`teamPieChart`) + a 2×2 stat grid — Total Registration, Students Paid, Working on Ideas, Ideas Submitted.
- Profile completion form: new **"D. Designated Teacher"** section — `designated_teacher_name` + `designated_teacher_mobile` (both required to activate the school).
- Header text: "IFT Competition Overview" → "IFT **Program** Overview".
- Removed the top-right active-phase badge from the page header.
- Added CSS for ticker, chart boxes, payment legend, and team-formation stat cards.

### 7. `templates/students/school_payments.html` (NEW)
Standalone payment follow-up page: paid vs pending summary + per-student table (name, email, grade, phone, payment status, submission status).

---

## Behavioral / Data Notes

- **Payment gateway is NOT implemented.** `paid_count` is hardcoded to `0`; all students show "Payment Pending". When a real payment flow is added:
  1. Add a per-student paid flag (e.g. `Student.is_paid`).
  2. Compute `paid_count` / `unpaid_count` from it in `school_dashboard` and `school_payments`.
  3. All existing widgets (payment card, funnel, team pie, detail page) will then reflect real data with no further template changes.

- **Submission deadline** is read from `admins.Phase` whose name contains "submission" (`end_date` / `days_remaining`), fallback `2026-10-15`. Editable from the super-admin Schedule page. A "Idea Submission" phase ending 2026-10-15 was seeded locally.

- **Dummy/demo data** (demo school, ~30 students, 23 submissions across all 17 SDG tracks, 8 teams, the seed Phase) exists **only in the local SQLite DB**, which is gitignored — it will not be pushed to the server.

- **Local login for testing** (local only): school `demoschool@ift.local` / `school@123`.

---

## Deployment Fixes (Railway)

### 8. `students/migrations/0016_...py` — trimmed before push
The auto-generated `0016` also contained `CreateModel(LearningVideo)`, `CreateModel(VideoProgress)` and several `AlterField` choices ops (pre-existing un-migrated models in the repo). To keep the deploy purely additive and avoid touching existing server tables, `0016` was **trimmed to only the two School `AddField` operations**. (These models remain un-migrated, same as before — a pre-existing repo condition.)

### 9. `Procfile`
`web` command changed to run migrate before gunicorn:
```
web: python manage.py migrate --noinput && gunicorn ift_platform.wsgi --bind 0.0.0.0:$PORT
```
(Note: Railway builds from the Dockerfile, so Procfile is effectively ignored — see #10. Kept for parity.)

### 10. `Dockerfile` — the actual deploy fix
Railway deploys from the Dockerfile, whose `CMD` was gunicorn-only, so migrations never ran on deploy (caused `column students_school.designated_teacher_name does not exist` on prod). Fixed:
```dockerfile
CMD ["sh", "-c", "python manage.py migrate --noinput && gunicorn ift_platform.wsgi --bind 0.0.0.0:8000"]
```
Now every container start applies pending migrations.

---

## Push History (branch: main → github.com/techinfinitydevelopers/IFT)
- `17e1975` — feat: school dashboard widgets, charts, payment tracking, teacher fields + admin.E108 fix
- `9389532` — fix(deploy): run migrate on web startup (Procfile)
- `2f86594` — fix(deploy): run migrate in Dockerfile CMD (real fix, Procfile was ignored)

Pushed via a Personal Access Token supplied in chat — **that token must be rotated/revoked** (it was exposed).

---

## Setup notes (local)
- `.env` created from `.env.example` (gitignored).
- `db.sqlite3` and `.env` are gitignored — local users/data do not reach the server (Railway uses PostgreSQL).
- Local dev DB (SQLite) already has the full `0016` (incl. LearningVideo/VideoProgress); the server only gets the trimmed School fields.
