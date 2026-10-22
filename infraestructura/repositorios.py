from typing import Dict, Union
from modelo.modelo import Factura
from modelo.iRepositorios import RepositorioFacturas


def seleccionar_repositorio(proveedor: str) -> RepositorioFacturas:
    """Selecciona el adaptador de persistencia desde la capa de infraestructura."""
    if not isinstance(proveedor, str):
        raise ValueError("El proveedor de base de datos debe ser texto.")

    proveedor = proveedor.strip().lower()
    if proveedor == "memoria":
        return RepositorioEnMemoria()
    if proveedor == "postgresql":
        return RepositorioPostgreSQL()
    if proveedor == "oracle":
        return RepositorioOracle()
    raise ValueError(f"Proveedor de base de datos no soportado: {proveedor}")


class RepositorioEnMemoria(RepositorioFacturas):
    """Adaptador de persistencia volátil en memoria."""

    def __init__(self):
        self._facturas: Dict[str, Factura] = {}

    def guardar(self, factura: Factura) -> None:
        self._facturas[factura.id] = factura
        print(f"  [BD Memoria] Factura {factura.id} guardada en diccionario en memoria.")

    def obtener_por_id(self, id: str) -> Union[Factura, None]:
        return self._facturas.get(id)


class RepositorioPostgreSQL(RepositorioFacturas):
    """Adaptador simulado para PostgreSQL que cumple exactamente el mismo contrato."""

    def __init__(self):
        self._facturas: Dict[str, Factura] = {}

    def guardar(self, factura: Factura) -> None:
        self._facturas[factura.id] = factura
        print(
            f"  [PostgreSQL] INSERT INTO facturas (id, cliente_id, total) "
            f"VALUES ('{factura.id}', '{factura.cliente_id}', {factura.total});"
        )

    def obtener_por_id(self, id: str) -> Union[Factura, None]:
        return self._facturas.get(id)


class RepositorioOracle(RepositorioFacturas):
    """Adaptador simulado para Oracle que cumple exactamente el mismo contrato."""

    def __init__(self):
        self._facturas: Dict[str, Factura] = {}

    def guardar(self, factura: Factura) -> None:
        self._facturas[factura.id] = factura
        print(
            f"  [Oracle DB] INSERT INTO TB_FACTURAS VALUES "
            f"('{factura.id}', '{factura.cliente_id}', {factura.total}); COMMIT;"
        )

    def obtener_por_id(self, id: str) -> Union[Factura, None]:
        return self._facturas.get(id)