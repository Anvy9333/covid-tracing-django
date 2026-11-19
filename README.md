# COVID Tracing — Django Project (INFO-S2001)

A contact-tracing web application for HORECA establishments (bars, cafés, restaurants, hotels).
Clients book spots at establishments; when a client declares a positive COVID test, everyone who
was at the same establishment on the same day is warned.

Built with Django 6.1 and SQLite. No external services required.

## Setup

```bash
# 1. Create and activate a virtual environment
python -m venv venv
venv\Scripts\activate          # Windows
# source venv/bin/activate     # Linux / macOS

# 2. Install dependencies
pip install -r requirements.txt

# 3. Set up the database
python manage.py migrate

# 4. (Optional) Create an admin account to inspect the data
python manage.py createsuperuser

# 5. Run the development server
python manage.py runserver
```

Then open http://127.0.0.1:8000

## Project structure

- `tracing/` — project configuration (settings, root URL routing)
- `core/` — the application: models, views, forms, templates, URLs
  - `models.py` — database schema
  - `views.py` — one function per page
  - `forms.py` — signup, establishment, reservation, positive-report forms
  - `templates/` — HTML pages
  - `urls.py` — URL-to-view mapping

## Data model

- **User** (Django built-in) — reused for name, email, password (hashed). Extended by:
- **Profile** — one-to-one link to User, holds the `is_manager` flag.
- **Establishment** — name, capacity, `is_compliant` (hygiene norms), owned by a manager.
- **Reservation** — a client books an establishment for a given date and headcount.
- **PositiveReport** — a client declares a positive test on a given date.

"Contact" is **not stored** — it is computed on demand: two people are in contact if they have a
reservation at the same establishment on the same day.

## Features (all 7 required + 1 bonus)

| # | Feature | Where |
|---|---------|-------|
| 1 | Signup / login / logout, reversed-word CAPTCHA, manager flag | `signup_view`, `login_view` |
| 2 | Manager adds an establishment (gated on `is_manager`) | `add_establishment_view` |
| 3 | Search establishments by name + compliance | `search_view` |
| 4 | Reserve for N people, with per-day capacity check | `reserve_view` |
| 5 | Report a positive test with its date | `report_positive_view` |
| 6 | Contact warning on login (same place, same day as a positive test) | `get_my_contacts`, `home_view` |
| 7 | Public 30-day statistics page | `stats_view` |
| + | Bonus: manager views their establishments' reservations | `my_reservations_view` |

## Key implementation notes

- **Passwords** are hashed by Django's `create_user()` — never stored in clear.
- **CAPTCHA**: a random word is stored server-side in the session; the user must retype it reversed.
  This matches the project statement; it is not real bot protection.
- **Capacity check**: before accepting a booking, the app sums people already booked at that
  establishment on that date and rejects the booking if the total would exceed capacity.
- **Contact tracing**: for each positive report, find the establishments that person booked on
  their test date, then check whether the current user booked any of the same places on the same
  date. Computed live, not stored.
- **Manager role**: enforced server-side in the view, not only by hiding navigation links.
- **Reservations** cannot be made for past dates (validated in `ReservationForm.clean_date`).

## Known limitations (deliberate, for a "succinct" implementation)

- No password-strength validation.
- Capacity check is not wrapped in a database transaction (two simultaneous bookings could
  theoretically overbook).
- The CAPTCHA is plaintext — spec-compliant but trivially bypassable.