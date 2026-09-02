from django.urls import path
from .views import verification_view

urlpatterns = [path("verification", verification_view)]
