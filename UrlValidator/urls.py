from django.contrib import admin
from django.urls import path

from UrlValidator import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.index),
    path('check/', views.get_scrape),
]
