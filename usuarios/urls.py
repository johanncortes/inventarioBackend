"""
URLs de la app usuarios. Se conectan en sgil/urls.py bajo /api/.

    /api/usuarios/yo/     GET: el usuario conectado (cualquier rol)
    /api/usuarios/        GET (listar) y POST (crear) — solo encargado
    /api/usuarios/{id}/   GET (ver) y PUT/PATCH (cambiar rol, desactivar) — solo encargado
"""
from django.urls import path
from rest_framework.routers import DefaultRouter

from .views import UsuarioViewSet, YoView

router = DefaultRouter()
# basename='usuario' porque el modelo es User de Django: así las URLs se llaman
# usuario-list y usuario-detail (y no user-list).
router.register('usuarios', UsuarioViewSet, basename='usuario')

# 'usuarios/yo/' va ANTES que las URLs del router: Django revisa las rutas en
# orden, y el router tomaría "yo" como si fuera el id de un usuario (/usuarios/{id}/).
urlpatterns = [
    path('usuarios/yo/', YoView.as_view(), name='usuario-yo'),
] + router.urls
