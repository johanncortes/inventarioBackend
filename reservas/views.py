"""
Vistas de la app reservas.

- ReservaViewSet: CRUD de reservas con filtros, permisos por rol y cancelación
  (HU-03, HU-07, HU-08, M4, M5, M10, M11, M12).
- DisponibilidadView: vista calculada que responde cuántas unidades libres hay
  y qué salas están disponibles en un horario (M13, CA-03.2).

Permisos (tabla del plan, sección 3):
  - Docente: crea reservas y solo ve/edita las suyas.
  - Departamento: lee todas las reservas, no puede crear.
  - Encargado: lee todas y puede cancelar cualquiera.
"""
from rest_framework import status, viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from inventario.models import Recurso, Sala
from usuarios.models import Perfil
from usuarios.permisos import EsEncargadoOSoloLectura, obtener_rol

from .disponibilidad import sala_esta_ocupada, unidades_disponibles
from .models import Reserva
from .permisos import EsDuenoOEncargado
from .serializers import ReservaSerializer


class ReservaViewSet(viewsets.ModelViewSet):
    """CRUD de reservas: listar, ver, crear, editar y cancelar (HU-03).

    La eliminación (DELETE) no está permitida para conservar el historial (RNF-06).
    Para "cancelar" se usa PATCH con {\"cancelada\": true}.
    """

    serializer_class = ReservaSerializer
    # EsDuenoOEncargado se revisa a nivel de objeto (has_object_permission).
    # IsAuthenticated asegura que haya sesión (ya es el default global, pero
    # lo ponemos explícito para que quede claro).
    permission_classes = [IsAuthenticated, EsDuenoOEncargado]

    # Sin DELETE: las reservas no se borran, solo se cancelan (RNF-06).
    http_method_names = ['get', 'post', 'put', 'patch', 'head', 'options']

    # Filtros del listado (M12): fecha, recurso, sala y estado de cancelación.
    filterset_fields = ['fecha', 'recurso', 'sala', 'cancelada']

    # Búsqueda por nombre de asignatura o motivo (?search=Química) (M12).
    search_fields = ['asignatura', 'motivo', 'recurso__nombre']

    # Orden por defecto: las más próximas primero.
    ordering = ['fecha', 'hora_inicio']
    ordering_fields = ['fecha', 'hora_inicio', 'creada_en']

    def get_queryset(self):
        """Filtra las reservas según el rol del usuario (RNF-08).

        - Docente: solo ve SUS reservas.
        - Departamento y Encargado: ven todas.

        get_queryset se ejecuta antes de cada acción (list, retrieve, update...).
        """
        rol = obtener_rol(self.request.user)

        # El docente solo ve sus propias reservas ("Mis reservas").
        if rol == Perfil.DOCENTE:
            return (
                Reserva.objects
                .filter(docente=self.request.user)
                .select_related('recurso', 'sala', 'docente')
            )

        # El departamento y el encargado ven todas.
        return Reserva.objects.select_related('recurso', 'sala', 'docente').all()

    def get_permissions(self):
        """El departamento solo puede leer (GET); el docente puede crear y editar las suyas.

        Se llama antes de has_permission, así que el usuario puede no estar
        autenticado todavía: obtener_rol() devuelve None en ese caso y
        se cae al return por defecto (IsAuthenticated bloquea al anónimo).
        """
        rol = obtener_rol(self.request.user)

        # Solo lectura para el departamento.
        if rol == Perfil.DEPARTAMENTO:
            return [EsEncargadoOSoloLectura()]

        return [IsAuthenticated(), EsDuenoOEncargado()]

    def perform_create(self, serializer):
        """Guarda el docente conectado como dueño de la reserva (M5).

        perform_create se ejecuta justo antes de guardar. Así el docente
        no puede crear una reserva a nombre de otro.
        """
        serializer.save(docente=self.request.user)


class DisponibilidadView(APIView):
    """Calcula unidades disponibles y salas libres para un recurso en un horario (M13).

    Endpoint: GET /api/disponibilidad/?recurso=<id>&fecha=<YYYY-MM-DD>&hora_inicio=<HH:MM>&hora_fin=<HH:MM>

    Responde:
    {
        "recurso": "Termómetro digital",
        "fecha": "2024-10-09",
        "hora_inicio": "08:30",
        "hora_fin": "10:00",
        "unidades_disponibles": 3,
        "salas_libres": ["B307", "B308"]
    }
    """

    # name para que raiz.py lo pueda referenciar con reverse('disponibilidad').
    # El encargado y el docente pueden consultar disponibilidad (RF-03).
    permission_classes = [IsAuthenticated]

    def get(self, request, format=None):
        """Lee los parámetros, calcula disponibilidad y devuelve el resultado."""
        # Leer los parámetros de la URL (?recurso=1&fecha=...&hora_inicio=...&hora_fin=...).
        recurso_id = request.query_params.get('recurso')
        fecha_str = request.query_params.get('fecha')
        inicio_str = request.query_params.get('hora_inicio')
        fin_str = request.query_params.get('hora_fin')

        # Validar que estén todos los parámetros.
        errores = {}
        if not recurso_id:
            errores['recurso'] = 'Este parámetro es obligatorio.'
        if not fecha_str:
            errores['fecha'] = 'Este parámetro es obligatorio.'
        if not inicio_str:
            errores['hora_inicio'] = 'Este parámetro es obligatorio.'
        if not fin_str:
            errores['hora_fin'] = 'Este parámetro es obligatorio.'
        if errores:
            return Response(errores, status=status.HTTP_400_BAD_REQUEST)

        # Convertir los strings a los tipos correctos con manejo de errores.
        try:
            from datetime import date, time
            recurso = Recurso.objects.get(pk=recurso_id)
            fecha = date.fromisoformat(fecha_str)
            hora_inicio = time.fromisoformat(inicio_str)
            hora_fin = time.fromisoformat(fin_str)
        except Recurso.DoesNotExist:
            return Response({'recurso': 'Recurso no encontrado.'}, status=status.HTTP_404_NOT_FOUND)
        except ValueError as e:
            return Response({'detalle': f'Formato de fecha u hora inválido: {e}'}, status=status.HTTP_400_BAD_REQUEST)

        # El horario tiene que tener sentido (misma regla que al crear una reserva).
        if hora_fin <= hora_inicio:
            return Response(
                {'hora_fin': 'La hora de fin debe ser posterior a la de inicio.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Calcular unidades disponibles usando la función de disponibilidad.py.
        disponibles = unidades_disponibles(recurso, fecha, hora_inicio, hora_fin)

        # Calcular las salas libres en ese horario.
        # Una sala está libre si no tiene reservas activas que se crucen con el horario.
        salas_libres = []
        for sala in Sala.objects.all():
            if not sala_esta_ocupada(sala, fecha, hora_inicio, hora_fin):
                salas_libres.append(sala.codigo)

        return Response({
            'recurso': recurso.nombre,
            'fecha': fecha_str,
            'hora_inicio': inicio_str,
            'hora_fin': fin_str,
            'unidades_disponibles': max(disponibles, 0),  # nunca negativo en la respuesta
            'salas_libres': salas_libres,
        })

