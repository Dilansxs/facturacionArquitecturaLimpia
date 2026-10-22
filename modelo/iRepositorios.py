from abc import ABC, abstractmethod
from typing import Union
from modelo.modelo import Factura


class RepositorioFacturas(ABC):
    """
    Puerto de salida (Contrato de persistencia) definido en el Dominio.
    El dominio indica QUÉ necesita guardar, sin importar si es Memoria, PostgreSQL u Oracle.
    """

    @abstractmethod
    def guardar(self, factura: Factura) -> None:
        pass

    @abstractmethod
    def obtener_por_id(self, id: str) -> Union[Factura, None]:
        pass