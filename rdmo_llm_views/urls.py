from django.urls import include, path

from rest_framework_extensions.routers import ExtendedDefaultRouter

from .viewsets import ProjectViewSet

app_name = 'rdmo-llm-views'

router = ExtendedDefaultRouter()
project_route = router.register(r'projects', ProjectViewSet, basename='project')

urlpatterns = [
    path('llm-views/', include(router.urls)),
]
