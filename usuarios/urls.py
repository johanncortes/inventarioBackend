"""
URLs de la app usuarios. Se conectan en sgil/urls.py bajo /api/.

    /api/usuarios/        GET (listar) y POST (crear)
    /api/usuarios/{id}/   GET (ver) y PUT/PATCH (cambiar rol, desactivar)
"""
from rest_framework.routers import DefaultRouter

from .views import UsuarioViewSet

router = DefaultRouter()
# basename='usuario' porque el modelo es User de Django: así las URLs se llaman
# usuario-list y usuario-detail (y no user-list).
router.register('usuarios', UsuarioViewSet, basename='usuario')

urlpatterns = router.urls
