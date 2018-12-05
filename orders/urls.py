from django.urls import path
from . import views

app.name = 'orders'

urlpatterns = [
    path('created/', views.order_create, name='order_create'),
]