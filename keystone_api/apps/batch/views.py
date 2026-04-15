"""Application logic for rendering responses to HTTP requests.

View objects encapsulate logic for interpreting request data, interacting with
models or services, and generating the appropriate HTTP response(s). Views
serve as the controller layer in Django's MVC-inspired architecture, bridging
URLs to business logic.
"""

from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from .exceptions import JobExecutionError
from .models import *
from .references import ReferenceResolutionError
from .serializers import *
from .shortcuts import execute_job

__all__ = ['JobViewSet']


class JobViewSet(APIView):
    """API endpoints for executing and inspecting batch jobs."""

    permission_classes = [permissions.IsAuthenticated]
    search_fields = ['status']
    queryset = JobStatus.objects.all()

    def post(self, request) -> Response:
        """Execute all submitted steps atomically in a single transaction."""

        serializer = JobSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            job, results = execute_job(
                serializer.validated_data['actions'],
                user=request.user,
                server_name=request.get_host(),
            )

        except ReferenceResolutionError as exc:
            return Response(
                {'detail': str(exc), 'token': exc.token},
                status=status.HTTP_422_UNPROCESSABLE_ENTITY,
            )

        except JobExecutionError as exc:
            return Response(
                {
                    'detail': str(exc),
                    'failed_step': exc.index,
                    'failed_status': exc.status_code,
                    'failed_body': exc.body,
                },
                status=status.HTTP_422_UNPROCESSABLE_ENTITY,
            )

        return Response({
            'id': str(job.id),
            'status': job.status,
            'results': results,
        })