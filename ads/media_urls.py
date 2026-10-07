from django.urls import path
from . import views

app_name = "media_ads"
urlpatterns = [
        path("decision/", views.decision, name="decision"),
        path("events/", views.event, name="events"),
    ]