"""
URLs de la app inventario. Se conectan en sgil/urls.py bajo /api/.

El DefaultRouter crea solo las URLs de cada ViewSet. Por ejemplo, para categorías:
    /api/categorias/        GET (listar) y POST (crear)
    /api/categorias/{id}/   GET (ver), PUT/PATCH (editar) y DELETE (borrar)
Además crea la página /api/ con la lista de endpoints (la "raíz" de la API navegable).
"""
from rest_framework.routers import DefaultRouter

from .views import (
    CategoriaViewSet,
    MovimientoViewSet,
    RecursoViewSet,
    SalaViewSet,
    TorreViewSet,
    UnidadViewSet,
)

router = DefaultRouter()
# El primer texto es el pedazo de la URL; basename no hace falta porque el ViewSet tiene queryset.
router.register('categorias', CategoriaViewSet)
router.register('torres', TorreViewSet)
router.register('salas', SalaViewSet)
router.register('recursos', RecursoViewSet)
router.register('unidades', UnidadViewSet)
router.register('movimientos', MovimientoViewSet)

urlpatterns = router.urls
