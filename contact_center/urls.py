from django.urls import path
from contact_center.views import CDRListView, RecordingDownloadAPIView

urlpatterns = [
    path('', CDRListView.as_view(), name='cdr-list'),
    path('download-recording/<int:cdr_id>/', RecordingDownloadAPIView.as_view(), name='download-recording'),
]
