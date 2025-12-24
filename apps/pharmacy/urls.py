from django.urls import path

from . import views

app_name = 'pharmacy'

urlpatterns = [
    # Prescriptions
    path('prescriptions/', views.PrescriptionListView.as_view(), name='prescription_list'),
    path('prescriptions/<int:pk>/', views.PrescriptionDetailView.as_view(), name='prescription_detail'),

    # Refills
    path('refills/', views.RefillListView.as_view(), name='refill_list'),
    path('refills/<int:pk>/', views.RefillDetailView.as_view(), name='refill_detail'),
    path(
        'prescriptions/<int:prescription_id>/refill/',
        views.RefillRequestCreateView.as_view(),
        name='request_refill'
    ),
]
