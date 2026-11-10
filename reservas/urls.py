"""
URLs de la app reservas.

DefaultRouter genera automáticamente las rutas del CRUD:
  GET  /api/reservas/          → listar (ReservaViewSet.list)
  POST /api/reservas/          → crear  (ReservaViewSet.create)
  GET  /api/reservas/{id}/     → ver    (ReservaViewSet.retrieve)
  PUT  /api/reservas/{id}/     → editar completo
  PATCH /api/reservas/{id}/    → editar parcial (cancelar: {\"cancelada\": true})

La vista calculada /api/disponibilidad/ se agrega con path() porque no es un
ViewSet (es un APIView, M13). Se le da name='disponibilidad' para que raiz.py
la liste con reverse().
"""
from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import DisponibilidadView, ReservaViewSet

# El router crea las URLs del CRUD de forma automática.
router = DefaultRouter()
router.register('reservas', ReservaViewSet, basename='reserva')

urlpatterns = [
    # Todas las rutas del router (/api/reservas/ y /api/reservas/{id}/).
    path('', include(router.urls)),

    # Vista calculada de disponibilidad (no es un ViewSet, va aparte).
    # name='disponibilidad' permite que raiz.py la liste con reverse('disponibilidad').
    path('disponibilidad/', DisponibilidadView.as_view(), name='disponibilidad'),
]

