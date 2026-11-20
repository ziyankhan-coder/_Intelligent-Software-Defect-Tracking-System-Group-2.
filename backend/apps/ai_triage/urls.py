from django.urls import path
from .views import AnalyzeDraftView

urlpatterns = [
    path(
        "analyze-draft/",
        AnalyzeDraftView.as_view(),
        name="analyze-draft"
    ),
]