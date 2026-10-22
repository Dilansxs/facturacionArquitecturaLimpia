from abc import ABC, abstractmethod
from decimal import Decimal, InvalidOperation
from modelo.modelo import Factura, LineaFactura, ControlFraude, PoliticaFiscal
from modelo.iRepositorios import RepositorioFacturas


class CrearFactura(ABC):
    """
    Puerto de entrada (Contrato de la capa de aplicación).
    Tanto el adaptador REST como el Broker AMQP invocan este contrato.
    """

    @abstractmethod
    def ejecutar(self, solicitud: dict) -> dict:
        pass


class CrearFacturaUseCase(CrearFactura):
    """
    Caso de uso único para la creación de facturas.
    No conoce si los datos vienen por HTTP o RabbitMQ, ni en qué BD se guardan.
    """

    def __init__(
        self,
        repositorio: RepositorioFacturas,
        control_fraude: ControlFraude,
        politica_fiscal: PoliticaFiscal
    ):
        self._repositorio = repositorio
        self._controlFraude = control_fraude
        self._politicaFiscal = politica_fiscal

    def ejecutar(self, solicitud: dict) -> dict:
        if not isinstance(solicitud, dict):
            raise ValueError("La solicitud debe ser un objeto.")

        cliente_id = solicitud.get("cliente_id")
        if not isinstance(cliente_id, str) or not cliente_id.strip():
            raise ValueError("El identificador del cliente es obligatorio.")

        lineas_datos = solicitud.get("lineas", [])
        if not isinstance(lineas_datos, list):
            raise ValueError("Las líneas de la factura deben enviarse en una lista.")

        lineas = []
        for indice, item in enumerate(lineas_datos, start=1):
            if not isinstance(item, dict):
                raise ValueError(f"La línea {indice} debe ser un objeto.")

            campos_requeridos = ("descripcion", "cantidad", "precio_unitario")
            campos_faltantes = [campo for campo in campos_requeridos if campo not in item]
            if campos_faltantes:
                raise ValueError(
                    f"Faltan campos en la línea {indice}: {', '.join(campos_faltantes)}."
                )

            descripcion = item["descripcion"]
            if not isinstance(descripcion, str):
                raise ValueError(f"La descripción de la línea {indice} debe ser texto.")

            cantidad_dato = item["cantidad"]
            if isinstance(cantidad_dato, bool) or not isinstance(cantidad_dato, (int, str)):
                raise ValueError(f"La cantidad de la línea {indice} debe ser un entero.")
            try:
                cantidad = int(cantidad_dato)
            except ValueError as error:
                raise ValueError(
                    f"La cantidad de la línea {indice} debe ser un entero."
                ) from error

            precio_dato = item["precio_unitario"]
            if isinstance(precio_dato, bool) or not isinstance(
                precio_dato, (str, int, float, Decimal)
            ):
                raise ValueError(f"El precio de la línea {indice} debe ser numérico.")
            try:
                precio_unitario = Decimal(str(precio_dato))
            except InvalidOperation as error:
                raise ValueError(
                    f"El precio de la línea {indice} debe ser numérico."
                ) from error

            lineas.append(
                LineaFactura(
                    descripcion=descripcion,
                    cantidad=cantidad,
                    precio_unitario=precio_unitario
                )
            )

        # 2. Calcular subtotal preliminar y validar reglas de Control de Fraude
        subtotal_preliminar = sum((linea.subtotal for linea in lineas), Decimal("0.00"))
        self._controlFraude.validar(cliente_id, subtotal_preliminar)

        # 3. Obtener la tasa de impuesto según las Políticas Fiscales del dominio
        tasa = self._politicaFiscal.tasa_aplicable(cliente_id)

        # 4. Crear la entidad Factura en el dominio
        factura = Factura.crear(cliente_id, lineas, tasa)

        # 5. Guardar usando el contrato genérico de persistencia
        self._repositorio.guardar(factura)

        # 6. Retornar respuesta neutra (diccionario)
        return {
            "id": factura.id,
            "cliente_id": factura.cliente_id,
            "subtotal": str(factura.subtotal),
            "impuesto": str(factura.impuesto),
            "total": str(factura.total)
        }