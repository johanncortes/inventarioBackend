"""
Vistas de la app incidencias (Diego).

- IncidenciaViewSet: registrar y consultar incidencias (HU-04, HU-10).
- AlertaListView: panel de alertas operativas calculadas del inventario (HU-05, HU-09).

Un ModelViewSet arma en una sola clase las acciones del CRUD:
listar y crear (GET y POST a /api/incidencias/), y ver y editar
(GET y PUT/PATCH a /api/incidencias/{id}/). El router las conecta a las URLs
(incidencias/urls.py).

AlertaListView es una APIView porque no proviene de una tabla estática en la base de datos,
sino que se calcula dinámicamente desde Recurso y Unidad (alertas.py).
"""
from rest_framework import status, viewsets
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response
from rest_framework.views import APIView

from usuarios.permisos import EsEncargadoODepartamento

from .alertas import calcular_alertas
from .models import Incidencia
from .permisos import PermisoIncidencias
from .serializers import IncidenciaSerializer


class IncidenciaViewSet(viewsets.ModelViewSet):
    """CRUD de incidencias (HU-04, HU-10).

    Permisos (RNF-03, D7):
    - Encargado: registra y avanza estados.
    - Departamento: solo lectura.
    - Docente: 403 Forbidden.

    Métodos HTTP permitidos (RNF-06, D8):
    - No se permite borrar incidencias (sin 'delete'). Un DELETE responderá 405 Method Not Allowed.
    """

    # select_related trae el recurso, la unidad y los dos usuarios en la MISMA
    # consulta (son FK). Sin esto, la página haría varias consultas por incidencia.
    queryset = Incidencia.objects.select_related('recurso', 'unidad', 'docente_presente', 'registrada_por')
    serializer_class = IncidenciaSerializer
    permission_classes = [PermisoIncidencias]

    # Sin 'delete': las incidencias registradas forman parte de la auditoría y no se borran (RNF-06)
    http_method_names = ['get', 'post', 'put', 'patch', 'head', 'options']

    # Filtros, búsqueda y orden (D9, HU-04, HU-10)
    filterset_fields = ['estado', 'recurso', 'unidad']
    search_fields = ['descripcion', 'recurso__nombre', 'unidad__numero', 'detalle_afectados']
    ordering_fields = ['fecha', 'estado']
    ordering = ['-fecha']  # la más nueva primero por defecto

    def perform_create(self, serializer):
        """Guarda quién registró la incidencia: el usuario conectado (HU-10).

        perform_create se ejecuta justo antes de guardar en un POST. Así el
        encargado no puede registrar una incidencia a nombre de otra persona.
        El estado nace en 'pendiente' y la fecha se pone sola (auto_now_add).
        """
        serializer.save(registrada_por=self.request.user)


class AlertaListView(APIView):
    """GET /api/alertas/: Listado de alertas calculadas con filtro y paginación (HU-05, HU-09, D12).

    Filtro por tipo: ?tipo=reparacion | mantencion | reposicion
    Paginación: Usa PageNumberPagination de 9 por página; entrega 'count' (contador total de alertas).

    Permisos:
    - Encargado y Departamento: lectura permitida.
    - Docente / Sin sesión: 403 Forbidden.
    """

    permission_classes = [EsEncargadoODepartamento]

    def get(self, request):
        alertas = calcular_alertas()

        # Filtrar por tipo si viene en query_params (CA-05.2)
        tipo = request.query_params.get('tipo')
        if tipo:
            # Un tipo mal escrito (ej: ?tipo=reposision) responde 400 con los tipos
            # válidos, en vez de una lista vacía que parece "no hay alertas".
            tipos_validos = ['reparacion', 'mantencion', 'reposicion']
            if tipo not in tipos_validos:
                return Response(
                    {'tipo': f'Tipo no válido. Usa uno de: {", ".join(tipos_validos)}.'},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            alertas = [a for a in alertas if a['tipo'] == tipo]

        # Paginación estándar de DRF de 9 por página (CA-05.1)
        paginador = PageNumberPagination()
        alertas_paginadas = paginador.paginate_queryset(alertas, request, view=self)

        return paginador.get_paginated_response(alertas_paginadas)
