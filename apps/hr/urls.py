"""HR URL configuration."""
from django.urls import path

from . import views

app_name = 'hr'

urlpatterns = [
    # HR Dashboard / Root
    path('', views.HRDashboardView.as_view(), name='dashboard'),

    # Departments
    path('departments/', views.DepartmentListView.as_view(), name='department_list'),
    path('departments/add/', views.DepartmentCreateView.as_view(), name='department_create'),
    path('departments/<int:pk>/edit/', views.DepartmentUpdateView.as_view(), name='department_update'),
    path('departments/<int:pk>/delete/', views.DepartmentDeleteView.as_view(), name='department_delete'),

    # Positions
    path('positions/', views.PositionListView.as_view(), name='position_list'),
    path('positions/add/', views.PositionCreateView.as_view(), name='position_create'),
    path('positions/<int:pk>/edit/', views.PositionUpdateView.as_view(), name='position_update'),
    path('positions/<int:pk>/delete/', views.PositionDeleteView.as_view(), name='position_delete'),

    # Employees
    path('employees/', views.EmployeeListView.as_view(), name='employee_list'),
    path('employees/add/', views.EmployeeCreateView.as_view(), name='employee_create'),
    path('employees/<int:pk>/', views.EmployeeDetailView.as_view(), name='employee_detail'),
    path('employees/<int:pk>/edit/', views.EmployeeUpdateView.as_view(), name='employee_update'),
    path('employees/<int:pk>/delete/', views.EmployeeDeleteView.as_view(), name='employee_delete'),

    # Time Tracking
    path('time/', views.timesheet_view, name='timesheet'),
    path('time/clock-in/', views.clock_in_view, name='clock_in'),
    path('time/clock-out/', views.clock_out_view, name='clock_out'),

    # Shifts / Schedule
    path('schedule/', views.ShiftListView.as_view(), name='shift_list'),
    path('schedule/add/', views.ShiftCreateView.as_view(), name='shift_create'),
    path('schedule/<int:pk>/edit/', views.ShiftUpdateView.as_view(), name='shift_update'),
    path('schedule/<int:pk>/delete/', views.ShiftDeleteView.as_view(), name='shift_delete'),
]
