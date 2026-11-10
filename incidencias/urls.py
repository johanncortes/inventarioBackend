"""
URLs de la app incidencias. Se conectan en sgil/urls.py bajo /api/.

El DefaultRouter crea solo las URLs del ViewSet:
    /api/incidencias/        GET (listar) y POST (registrar)
    /api/incidencias/{id}/   GET (ver) y PUT/PATCH (editar, avanzar el estado)

Además se agrega la vista de alertas calculadas:
    /api/alertas/            GET (panel de alertas operativas)
"""
from django.urls import path
from rest_framework.routers import DefaultRouter

from .views import AlertaListView, IncidenciaViewSet

router = DefaultRouter()
router.register('incidencias', IncidenciaViewSet)

urlpatterns = [
    path('alertas/', AlertaListView.as_view(), name='alerta-list'),
] + router.urls
