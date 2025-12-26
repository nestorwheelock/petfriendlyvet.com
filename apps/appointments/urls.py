"""Appointment URL configuration."""
from django.urls import path
from django.views.generic import RedirectView

from . import views

app_name = 'appointments'

urlpatterns = [
    path('', RedirectView.as_view(pattern_name='appointments:my_appointments'), name='index'),
    path('services/', views.ServiceListView.as_view(), name='services'),
    path('book/', views.BookAppointmentView.as_view(), name='book'),
    path('my-appointments/', views.MyAppointmentsView.as_view(), name='my_appointments'),
    path('<int:pk>/', views.AppointmentDetailView.as_view(), name='detail'),
    path('<int:pk>/cancel/', views.CancelAppointmentView.as_view(), name='cancel'),
    path('<int:pk>/reschedule/', views.RescheduleAppointmentView.as_view(), name='reschedule'),
    path('available-slots/', views.AvailableSlotsView.as_view(), name='available_slots'),
]
