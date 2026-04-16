"""Application logic for rendering responses to HTTP requests.

View objects encapsulate logic for interpreting request data, interacting with
models or services, and generating the appropriate HTTP response(s). Views
serve as the controller layer in Django's MVC-inspired architecture, bridging
URLs to business logic.
"""

from django.http import JsonResponse
from drf_spectacular.utils import extend_schema
from rest_framework import permissions, status
from rest_framework.views import APIView

from .exceptions import *
from .serializers import *
from .shortcuts import *

__all__ = ['JobApiView']


class JobApiView(APIView):
    """API endpoints for executing and inspecting batch jobs."""

    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(
        tags=['Utils - Batch Processing'],
        summary='Execute a batch job.',
        description=(
            'Executes multiple HTTP operations atomically within a single atomic transaction. '
            'If any step returns a 4xx or 5xx status, the job halts and all changes are rolled back. '
            'Steps may reference the response body of previous steps using @ref{alias.dotpath} tokens. '
            'When `dry_run` is true, all steps execute but no database changes are persisted.'
        ),
        request=JobRequestSerializer,
        responses={
            status.HTTP_200_OK: JobResponseSerializer,
            status.HTTP_422_UNPROCESSABLE_ENTITY: JobExecutionErrorSerializer,
        },
    )
    def post(self, request) -> JsonResponse:
        """Execute all submitted steps atomically in a single transaction."""

        serializer = JobRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            results = execute_job(
                serializer.validated_data['actions'],
                user=request.user,
                server_name=request.get_host(),
                dry_run=serializer.validated_data['dry_run'],
            )

        except ReferenceResolutionError as exc:
            status_code = status.HTTP_422_UNPROCESSABLE_ENTITY
            payload = {'detail': str(exc), 'token': exc.token}

        except JobExecutionError as exc:
            status_code = status.HTTP_422_UNPROCESSABLE_ENTITY
            payload = {
                'detail': str(exc),
                'step': exc.index,
                'status': exc.status_code,
                'body': exc.body,
            }

        else:
            status_code = status.HTTP_200_OK
            payload = {'results': results}

        return JsonResponse(payload, status=status_code)
