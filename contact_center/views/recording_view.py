from django.http import StreamingHttpResponse
from django.shortcuts import get_object_or_404
from drf_spectacular.utils import extend_schema
from rest_framework import permissions
from rest_framework.response import Response
from rest_framework.views import APIView

from contact_center.models import CallRecord
from contact_center.services import IssabelService


@extend_schema(tags=['CDR'], summary='Recording download')
class RecordingDownloadAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, cdr_id: int):
        cdr = get_object_or_404(CallRecord, id=cdr_id)

        if not cdr.recordingfile:
            return Response({'detail': 'Recording not found'}, status=404)

        service = IssabelService()
        upstream = service.stream_recording(cdr.recordingfile)

        response = StreamingHttpResponse(
            upstream.iter_content(chunk_size=8192),
            content_type='audio/wav',
        )
        response['Content-Disposition'] = f'attachment; filename="{cdr.recordingfile}"'
        return response
