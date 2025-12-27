"""Staff appointment URL patterns."""
from django.urls import path

from . import staff_views

app_name = 'appointments'

urlpatterns = [
    path('', staff_views.staff_list, name='staff_list'),
    path('add/', staff_views.staff_create, name='staff_create'),
    path('bulk/', staff_views.bulk_action, name='bulk_action'),
    path('<int:pk>/', staff_views.staff_detail, name='staff_detail'),
    path('<int:pk>/edit/', staff_views.staff_edit, name='staff_edit'),
    path('<int:pk>/check-in/', staff_views.check_in, name='check_in'),
    path('<int:pk>/no-show/', staff_views.mark_no_show, name='mark_no_show'),
    path('<int:pk>/complete/', staff_views.mark_complete, name='mark_complete'),
]
