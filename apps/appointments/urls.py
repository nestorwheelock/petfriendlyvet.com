"""Appointment URL configuration."""
from django.urls import path

from . import views

app_name = 'appointments'

urlpatterns = [
    path('services/', views.ServiceListView.as_view(), name='services'),
    path('book/', views.BookAppointmentView.as_view(), name='book'),
    path('my-appointments/', views.MyAppointmentsView.as_view(), name='my_appointments'),
    path('<int:pk>/', views.AppointmentDetailView.as_view(), name='detail'),
    path('<int:pk>/cancel/', views.CancelAppointmentView.as_view(), name='cancel'),
    path('available-slots/', views.AvailableSlotsView.as_view(), name='available_slots'),
]
