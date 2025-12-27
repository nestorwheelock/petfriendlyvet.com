from django.urls import path

from . import views

app_name = 'crm'

urlpatterns = [
    path('', views.CRMDashboardView.as_view(), name='dashboard'),
    path('customers/', views.CustomerListView.as_view(), name='customer_list'),
    path('customers/<int:pk>/', views.CustomerDetailView.as_view(), name='customer_detail'),
    # Lookup by user ID (used from encounter cards where we have user.id not profile.id)
    path('customers/by-user/<int:user_id>/', views.customer_by_user, name='customer_by_user'),
]
