# urls.py
from django.urls import path
from . import views

urlpatterns = [
    path('payment/start/', views.start_payment, name='start_payment'),
    path('payment/callback/', views.payment_callback, name='payment_callback'),
]
