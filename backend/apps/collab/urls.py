from django.urls import path
from .views import ProjectListCreateView, ProjectDetailView, ProjectMemberAssignView

app_name = 'collab'

urlpatterns = [
    path('', ProjectListCreateView.as_view(), name='project_list_create'),
    path('<int:pk>/', ProjectDetailView.as_view(), name='project_detail'),
    path('<int:pk>/members/', ProjectMemberAssignView.as_view(), name='project_members_assign'),
    path('<int:pk>/members/<int:user_id>/', ProjectMemberAssignView.as_view(), name='project_members_remove'),
]
