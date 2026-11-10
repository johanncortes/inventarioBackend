"""
URLs de la app incidencias. Se conectan en sgil/urls.py bajo /api/.

El DefaultRouter crea solo las URLs del ViewSet:
    /api/incidencias/        GET (listar) y POST (registrar)
    /api/incidencias/{id}/   GET (ver) y PUT/PATCH (editar, avanzar el estado)
"""
from rest_framework.routers import DefaultRouter

from .views import IncidenciaViewSet

router = DefaultRouter()
# basename no hace falta porque el ViewSet tiene queryset: las rutas se llaman incidencia-list, incidencia-detail.
router.register('incidencias', IncidenciaViewSet)

urlpatterns = router.urls

