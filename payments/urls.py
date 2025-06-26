# payments/urls.py
from django.urls import path
from . import views

urlpatterns = [
    path('create-paypal-payment/', views.create_paypal_payment, name='create-paypal-payment'),
    path('create-chapa-payment/', views.create_chapa_payment, name='create-chapa-payment'),
    path('<int:pk>/', views.payment_detail, name='payment-detail'),  # Moved up
    path('paypal-ipn/', views.paypal_ipn, name='paypal-ipn'),
    path('chapa-ipn/', views.chapa_ipn, name='chapa-ipn'),
    path('verify-chapa/', views.verify_chapa_payment, name='verify-chapa'),
]