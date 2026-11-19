from django.urls import path
from . import views

urlpatterns = [
    path("", views.home_view, name="home"),
    path("signup/", views.signup_view, name="signup"),
    path("login/", views.login_view, name="login"),
    path("logout/", views.logout_view, name="logout"),
    path("add-establishment/", views.add_establishment_view, name="add_establishment"),
    path("search/", views.search_view, name="search"),
    path("reserve/", views.reserve_view, name="reserve"),
    path("report-positive/", views.report_positive_view, name="report_positive"),
    path("stats/", views.stats_view, name="stats"),
    path("my-reservations/", views.my_reservations_view, name="my_reservations"),

]