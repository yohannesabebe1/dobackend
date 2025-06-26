from django.contrib import admin
from django.urls import path, include
from . import views

urlpatterns = [
  path('reset_password/', views.resetPassword, name='reset_password') 
]
