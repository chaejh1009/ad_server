from django.urls import path

from . import views, web_views

app_name = "ads"
urlpatterns = [
    path("advertiser/campaigns/", web_views.campaign_view, name="web-campaigns"),
    path("advertiser/bids/", web_views.bid_view, name="web-bids"),
    path("campaigns/", views.campaigns, name="campaigns"),
    path("bids/", views.bids, name="bids"),
]