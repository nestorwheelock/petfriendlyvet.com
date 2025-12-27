"""URL patterns for the parties app."""
from django.urls import path

from . import views

app_name = 'parties'

urlpatterns = [
    path('', views.PartiesDashboardView.as_view(), name='dashboard'),

    # People CRUD
    path('people/', views.PeopleListView.as_view(), name='people_list'),
    path('people/add/', views.PersonCreateView.as_view(), name='person_create'),
    path('people/<int:pk>/', views.PersonDetailView.as_view(), name='person_detail'),
    path('people/<int:pk>/edit/', views.PersonUpdateView.as_view(), name='person_edit'),
    path('people/<int:pk>/delete/', views.PersonDeleteView.as_view(), name='person_delete'),
    path('people/<int:pk>/pets/add/', views.PersonAddPetView.as_view(), name='person_add_pet'),
    path('people/<int:pk>/pets/search/', views.PersonSearchPetsView.as_view(), name='person_search_pets'),
    path('people/<int:pk>/pets/<int:pet_pk>/unlink/', views.PersonUnlinkPetView.as_view(), name='person_unlink_pet'),

    # Organizations CRUD
    path('organizations/', views.OrganizationsListView.as_view(), name='organizations_list'),
    path('organizations/add/', views.OrganizationCreateView.as_view(), name='organization_create'),
    path('organizations/<int:pk>/', views.OrganizationDetailView.as_view(), name='organization_detail'),
    path('organizations/<int:pk>/edit/', views.OrganizationUpdateView.as_view(), name='organization_edit'),
    path('organizations/<int:pk>/delete/', views.OrganizationDeleteView.as_view(), name='organization_delete'),

    # Groups CRUD
    path('groups/', views.GroupsListView.as_view(), name='groups_list'),
    path('groups/add/', views.GroupCreateView.as_view(), name='group_create'),
    path('groups/<int:pk>/', views.GroupDetailView.as_view(), name='group_detail'),
    path('groups/<int:pk>/edit/', views.GroupUpdateView.as_view(), name='group_edit'),
    path('groups/<int:pk>/delete/', views.GroupDeleteView.as_view(), name='group_delete'),

    # Relationships CRUD
    path('relationships/', views.RelationshipsListView.as_view(), name='relationships_list'),
    path('relationships/add/', views.RelationshipCreateView.as_view(), name='relationship_create'),
    path('relationships/<int:pk>/edit/', views.RelationshipUpdateView.as_view(), name='relationship_edit'),
    path('relationships/<int:pk>/delete/', views.RelationshipDeleteView.as_view(), name='relationship_delete'),
]
