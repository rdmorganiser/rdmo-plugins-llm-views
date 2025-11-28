from django.utils.translation import gettext_lazy as _

from rest_framework import status
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet

from django_q.models import Task

from rdmo.core.permissions import HasModelPermission
from rdmo.projects.models import Project
from rdmo.projects.permissions import HasProjectPermission

from .utils import get_group


class ProjectViewSet(GenericViewSet):

    def get_queryset(self):
        return Project.objects.filter_user(self.request.user)

    @action(detail=True, methods=["POST"], permission_classes=(HasModelPermission | HasProjectPermission, ))
    def reset(self, request, pk=None):
        project = self.get_object()
        snapshot_id = request.data.get("snapshot")

        try:
            view_id = int(request.data["view"])
        except ValueError as e:
            raise ValidationError({ "view": [_("This field must be an integer value.")] }) from e
        except KeyError as e:
            raise ValidationError({ "view": [_("This field may not be blank.")] }) from e

        Task.objects.filter(group=get_group(project.id, snapshot_id, view_id)).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
