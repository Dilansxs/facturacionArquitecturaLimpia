from dataclasses import dataclass
from decimal import Decimal, DecimalException
from typing import List
import uuid


@dataclass
class LineaFactura:
    descripcion: str
    cantidad: int
    precio_unitario: Decimal
    subtotal: Decimal = Decimal("0.00")

    def __post_init__(self):
        if not isinstance(self.descripcion, str) or not self.descripcion.strip():
            raise ValueError("La descripción del producto o servicio es obligatoria.")
        if isinstance(self.cantidad, bool) or not isinstance(self.cantidad, int):
            raise ValueError("La cantidad debe ser un número entero.")
        if self.cantidad <= 0:
            raise ValueError("La cantidad debe ser mayor a cero.")
        if not isinstance(self.precio_unitario, Decimal) or not self.precio_unitario.is_finite():
            raise ValueError("El precio unitario debe ser un número válido.")
        if self.precio_unitario <= Decimal("0.00"):
            raise ValueError("El precio unitario debe ser mayor a cero.")
        try:
            self.subtotal = (
                self.precio_unitario * Decimal(self.cantidad)
            ).quantize(Decimal("0.01"))
        except DecimalException as error:
            raise ValueError("El subtotal de la línea está fuera del rango permitido.") from error


@dataclass
class Factura:
    id: str
    cliente_id: str
    lineas: List[LineaFactura]
    subtotal: Decimal
    impuesto: Decimal
    total: Decimal

    @staticmethod
    def crear(cliente_id: str, lineas: List[LineaFactura], tasa: Decimal) -> "Factura":
        if not isinstance(cliente_id, str) or not cliente_id.strip():
            raise ValueError("El identificador del cliente es obligatorio.")
        if not isinstance(lineas, list):
            raise ValueError("Las líneas de la factura deben enviarse en una lista.")
        if not lineas:
            raise ValueError("La factura debe tener al menos una línea de detalle.")
        if any(not isinstance(linea, LineaFactura) for linea in lineas):
            raise ValueError("Todas las líneas deben ser detalles de factura válidos.")
        if not isinstance(tasa, Decimal) or not tasa.is_finite() or tasa < Decimal("0.00"):
            raise ValueError("La tasa fiscal debe ser un número válido no negativo.")

        try:
            subtotal = sum(
                (linea.subtotal for linea in lineas), Decimal("0.00")
            ).quantize(Decimal("0.01"))
            impuesto = (subtotal * tasa).quantize(Decimal("0.01"))
            total = (subtotal + impuesto).quantize(Decimal("0.01"))
        except DecimalException as error:
            raise ValueError("Los importes de la factura están fuera del rango permitido.") from error
        nuevo_id = f"FAC-{str(uuid.uuid4())[:8].upper()}"

        return Factura(
            id=nuevo_id,
            cliente_id=cliente_id,
            lineas=lineas,
            subtotal=subtotal,
            impuesto=impuesto,
            total=total
        )


class ControlFraude:
    """Regla crítica del dominio: verifica límites de monto y clientes bloqueados."""

    def __init__(self, limite: Decimal = Decimal("10000.00")):
        self._limite = limite
        self._clientes_bloqueados = {"CLI-FRAUDE", "CLI-BLOQUEADO"}

    def validar(self, cliente_id: str, subtotal: Decimal) -> None:
        if cliente_id in self._clientes_bloqueados:
            raise ValueError(f"Fraude detectado: el cliente '{cliente_id}' se encuentra bloqueado.")
        if subtotal > self._limite:
            raise ValueError(
                f"Fraude detectado: el subtotal (${subtotal}) supera el límite permitido (${self._limite})."
            )


class PoliticaFiscal:
    """Regla crítica del dominio: determina el porcentaje de impuesto aplicable."""

    def __init__(self, tasa_defecto: Decimal = Decimal("0.15")):
        self._tasa_defecto = tasa_defecto

    def tasa_aplicable(self, cliente_id: str) -> Decimal:
        # Si es cliente de exportación (prefijo EXP-), aplica 0% de IVA; caso contrario 15%
        if cliente_id.startswith("EXP-"):
            return Decimal("0.00")
        return self._tasa_defecto