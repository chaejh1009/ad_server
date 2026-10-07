"""
URL configuration for ad_config project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from ads import auth_views
from django.contrib.auth import views as django_auth_views

urlpatterns = [
    path('admin/', admin.site.urls),
    path("api/auth/csrf/", auth_views.csrf_token, name="csrf"),
    path("api/auth/login/", auth_views.login_view, name="login"),
    path("api/auth/logout/", auth_views.logout_view, name="logout"),
    path("accounts/login/", django_auth_views.LoginView.as_view(), name="login"),
    path("accounts/logout/", django_auth_views.LogoutView.as_view(), name="logout"),
    path("", include("ads.urls")),
    path("api/ads/", include("ads.urls")),
    path("api/media/", include("ads.media_urls")),
]
