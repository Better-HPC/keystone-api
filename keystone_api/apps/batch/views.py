"""Application logic for rendering responses to HTTP requests.

View objects encapsulate logic for interpreting request data, interacting with
models or services, and generating the appropriate HTTP response(s). Views
serve as the controller layer in Django's MVC-inspired architecture, bridging
URLs to business logic.
"""

import json

from django.http import JsonResponse
from drf_spectacular.utils import extend_schema
from rest_framework import parsers, permissions, status
from rest_framework.request import Request
from rest_framework.views import APIView

from .exceptions import *
from .serializers import *
from .shortcuts import *

__all__ = ['JobApiView']


class JobApiView(APIView):
    """API endpoints for executing and inspecting batch jobs."""

    permission_classes = [permissions.IsAuthenticated]
    parser_classes = [parsers.MultiPartParser, parsers.JSONParser]

    @extend_schema(
        tags=['Utils - Batch Processing'],
        summary='Execute a batch job.',
        description=(
            'Executes multiple HTTP operations atomically within a single atomic transaction. '
            'If any step returns a 4xx or 5xx status, the job halts and all changes are rolled back. '
            'Steps may reference the response body of previous steps using @ref{alias.dotpath} tokens. '
            'File parts uploaded alongside the job definition may be referenced in step payloads '
            'using @file{name} tokens, where `name` is the multipart field name. '
            'When `dry_run` is true, all steps execute but no database changes are persisted.'
        ),
        request=JobRequestSerializer,
        responses={
            status.HTTP_200_OK: JobResultSerializer,
            status.HTTP_422_UNPROCESSABLE_ENTITY: JobExecutionErrorSerializer,
        },
    )
    def post(self, request: Request) -> JsonResponse:
        """Execute all submitted steps atomically in a single transaction."""

        # Resolve the request content type and parse content payload
        try:
            data, files = self._parse_request(request)

        except json.JSONDecodeError:
            return JsonResponse({
                'detail': 'The `job` field is not valid JSON.'
            }, status=status.HTTP_400_BAD_REQUEST)

        # Validate payload schema
        serializer = JobSerializer(data=data)
        serializer.is_valid(raise_exception=True)

        # Execute the batch job
        try:
            results = execute_job(
                serializer.validated_data['actions'],
                user=request.user,
                server_name=request.get_host(),
                dry_run=serializer.validated_data['dry_run'],
                files=files,
            )

        except ReferenceResolutionError as exc:
            return JsonResponse({
                'detail': f'Cannot resolve reference "{exc.token}": {exc.reason}',
                'token': exc.token
            }, status=status.HTTP_422_UNPROCESSABLE_ENTITY)

        except JobExecutionError as exc:
            return JsonResponse({
                'detail': f'Step #{exc.index} ({exc.method} {exc.path}) failed with status {exc.status_code}',
                'step': exc.index,
                'status': exc.status_code,
                'body': exc.body,
            }, status=status.HTTP_422_UNPROCESSABLE_ENTITY)

        return JsonResponse({'results': results}, status=status.HTTP_200_OK)

    def _parse_request(self, request: Request) -> tuple[dict, dict | None]:
        """Return the JSON payload and file attachments from an incoming HTTP request.

        Supports `application/json` and `multipart/form-data` request formats,
        allowing users to submit standalone JSON or JSON with file attachments.

        Args:
            request: The HTTP request object to parse.

        Returns:
            The parsed JSON payload and file attachments.
        """

        data = request.data.get('job')
        if isinstance(data, str):
            data = json.loads(data)

        files = dict(request.FILES) if request.FILES else None
        return data, files
