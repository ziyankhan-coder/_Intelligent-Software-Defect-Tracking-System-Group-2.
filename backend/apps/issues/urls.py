from django.urls import path
from .views import IssueListCreateView, IssueDetailView, IssueSummaryView

app_name = 'issues'

urlpatterns = [
    path('summary/', IssueSummaryView.as_view(), name='issue_summary'),
    path('', IssueListCreateView.as_view(), name='issue_list_create'),
    path('<int:pk>/', IssueDetailView.as_view(), name='issue_detail'),
]
