import random
from django.shortcuts import render, redirect
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.models import User
from .forms import SignupForm, EstablishmentForm, ReservationForm
from django.contrib.auth.decorators import login_required
from .models import Establishment, PositiveReport, Reservation, Profile
from .forms import ReservationForm, PositiveReportForm
from django.db.models import Sum
from datetime import timedelta
from django.utils import timezone
# Pool of words for the CAPTCHA challenge.
CAPTCHA_WORDS = ["covid", "tracing", "brussels", "django", "horeca", "python"]


def signup_view(request):
    if request.method == "POST":
        form = SignupForm(request.POST)
        # We stored the shown word in the session when the page was first loaded.
        expected = request.session.get("captcha_word", "")
        if form.is_valid():
            typed = form.cleaned_data["captcha"]
            # Check the user typed the word reversed. [::-1] reverses a string.
            if typed != expected[::-1]:
                form.add_error("captcha", "Wrong CAPTCHA. Type the word backwards.")
            else:
                # Create the user. We use the email as the username
                # create_user() hashes the password 
                user = User.objects.create_user(
                    username=form.cleaned_data["email"],
                    email=form.cleaned_data["email"],
                    password=form.cleaned_data["password"],
                    first_name=form.cleaned_data["first_name"],
                    last_name=form.cleaned_data["last_name"],
                )
                login(request, user)  # log them in straight away
                # Store the manager flag in the linked profile.
                Profile.objects.create(
                    user=user,
                    is_manager=form.cleaned_data["is_manager"],
                )
                return redirect("home")
    else:
        form = SignupForm()

    word = random.choice(CAPTCHA_WORDS)
    request.session["captcha_word"] = word
    return render(request, "signup.html", {"form": form, "captcha_word": word})


def login_view(request):
    error = None
    if request.method == "POST":
        email = request.POST.get("email")
        password = request.POST.get("password")
        # checks the email/password against the database
        user = authenticate(request, username=email, password=password)
        if user is not None:
            login(request, user)
            return redirect("home")
        error = "Invalid email or password."
    return render(request, "login.html", {"error": error})


def logout_view(request):
    logout(request)
    return redirect("login")

@login_required
def home_view(request):
    contacts = get_my_contacts(request.user)
    return render(request, "home.html", {"contacts": contacts})

@login_required
def add_establishment_view(request):
    if not request.user.profile.is_manager:
        return render(request, "not_manager.html")
    if request.method == "POST":
        form = EstablishmentForm(request.POST)
        if form.is_valid():
            establishment = form.save(commit=False)
            establishment.manager = request.user  # the logged-in user owns it
            establishment.save()
            return redirect("home")
    else:
        form = EstablishmentForm()
    return render(request, "add_establishment.html", {"form": form})

from .models import Establishment  # add Establishment to your existing imports if not already there

@login_required
def search_view(request):
    # Read the search inputs 
    name_query = request.GET.get("name", "")
    compliance = request.GET.get("compliance", "")

    # Start with ALL establishments, then narrow down.
    results = Establishment.objects.all()

    # If a name was typed, keep only those whose name contains it (case-insensitive).
    if name_query:
        results = results.filter(name__icontains=name_query)

    # If a compliance filter was chosen, keep only matching ones.
    if compliance == "compliant":
        results = results.filter(is_compliant=True)
    elif compliance == "noncompliant":
        results = results.filter(is_compliant=False)

    return render(request, "search.html", {"results": results})

@login_required
def reserve_view(request):
    if request.method == "POST":
        form = ReservationForm(request.POST)
        if form.is_valid():
            reservation = form.save(commit=False)
            reservation.client = request.user  # the logged-in user books it
            establishment = reservation.establishment

            #  CAPACITY CHECK 
            # Sum all people already booked at this establishment on this date.
            already_booked = Reservation.objects.filter(establishment=establishment,date=reservation.date,).aggregate(total=Sum("nb_people"))["total"] or 0

            # Is there place for this new booking?
            if already_booked + reservation.nb_people > establishment.capacity:
                remaining = establishment.capacity - already_booked
                form.add_error("nb_people",
                    f"Not enough seats. Only {remaining} left on that date.")
            else:
                reservation.save()
                return redirect("home")
    else:
        form = ReservationForm()
    return render(request, "reserve.html", {"form": form})

@login_required
def report_positive_view(request):
    if request.method == "POST":
        form = PositiveReportForm(request.POST)
        if form.is_valid():
            report = form.save(commit=False)
            report.client = request.user   # the logged-in user is the positive case
            report.save()
            return redirect("home")
    else:
        form = PositiveReportForm()
    return render(request, "report_positive.html", {"form": form})

@login_required
def my_reservations_view(request):
    # All reservations at establishments owned by the logged-in manager.
    reservations = Reservation.objects.filter(
        establishment__manager=request.user
    ).order_by("date")
    return render(request, "my_reservations.html", {"reservations": reservations})

def get_my_contacts(user):

    warnings = []

    # 1. Every declared positive case.
    positives = PositiveReport.objects.all()

    for report in positives:
        # Don't warn someone about their own positive report.
        if report.client == user:
            continue

        # 2. Where did the positive person book ON their test date?
        positive_places = Reservation.objects.filter(client=report.client,date=report.test_date,).values_list("establishment", flat=True)#  a flat list of establishment IDs,

        # 3. Did `user` book any of those same places on that same date?
        my_overlaps = Reservation.objects.filter(client=user, date=report.test_date,establishment__in=positive_places,)  # establishment is one of those IDs
        

        # 4. Each overlap is a warning.
        for r in my_overlaps:
            warnings.append((report.test_date, r.establishment.name))

    return warnings

def stats_view(request):
    # 30-day window
    today = timezone.now().date()
    start = today - timedelta(days=30)

    # reports whose test date falls in the window.
    recent_positives = PositiveReport.objects.filter(
        test_date__gte=start,   
        test_date__lte=today,   
    )
    nb_positive = recent_positives.count()

    # People contacted: reuse the tracing logic per positive case,
    # collecting the distinct users who overlapped with a positive one.
    contacted_users = set()
    for report in recent_positives:
        # Who else booked the same place on the test date?
        overlaps = Reservation.objects.filter(date=report.test_date,establishment__in=Reservation.objects.filter(client=report.client,date=report.test_date,
            ).values_list("establishment", flat=True),).exclude(client=report.client)  # exclude the positive person themselves

        for r in overlaps:
            contacted_users.add(r.client.id)  # a set auto-deduplicates
    nb_contacted = len(contacted_users)
    return render(request, "stats.html", {
        "nb_positive": nb_positive,
        "nb_contacted": nb_contacted,
    })