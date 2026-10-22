import json
import os
from modelo.modelo import ControlFraude, PoliticaFiscal
from aplicacion.crearFactura import CrearFacturaUseCase
from infraestructura.repositorios import seleccionar_repositorio
from infraestructura.adaptadoresEntrada import AdaptadorREST, AdaptadorBrokerAMQP


def construir_caso_de_uso(proveedor: str = "memoria") -> CrearFacturaUseCase:
    repositorio = seleccionar_repositorio(proveedor)
    control_fraude = ControlFraude()
    politica_fiscal = PoliticaFiscal()
    return CrearFacturaUseCase(
        repositorio=repositorio,
        control_fraude=control_fraude,
        politica_fiscal=politica_fiscal
    )


def main():
    # El selector de infraestructura interpreta memoria, postgresql u oracle.
    motor_configurado = os.getenv("REPOSITORIO", "postgresql")
    print("=" * 70)
    print(f" SISTEMA DE FACTURACIÓN - MOTOR CONFIGURADO: {motor_configurado.upper()}")
    print("=" * 70)

    # 1. Construimos el único caso de uso inyectando las dependencias
    caso_de_uso = construir_caso_de_uso(motor_configurado)

    # 2. Conectamos los dos adaptadores simétricos al mismo contrato de entrada
    adaptador_rest = AdaptadorREST(caso_de_uso)
    adaptador_broker = AdaptadorBrokerAMQP(caso_de_uso)

    # --- Prueba 1: Entrada síncrona por API REST (Cliente normal con 15% IVA) ---
    peticion_http = {
        "cliente_id": "CLI-001",
        "lineas": [
            {"descripcion": "Teclado Mecánico", "cantidad": 2, "precio_unitario": "120.50"},
            {"descripcion": "Mouse Gamer", "cantidad": 1, "precio_unitario": "45.00"}
        ]
    }
    respuesta_rest = adaptador_rest.crear_factura_http(peticion_http)
    print("  Respuesta REST:", json.dumps(respuesta_rest, ensure_ascii=False))

    # --- Prueba 2: Entrada asíncrona por Broker AMQP (Mismo caso de uso) ---
    mensaje_cola = json.dumps({
        "cliente_id": "CLI-002",
        "lineas": [
            {"descripcion": "Monitor 24 pulgadas", "cantidad": 1, "precio_unitario": "250.00"}
        ]
    })
    adaptador_broker.consumir_mensaje(mensaje_cola)

    # --- Prueba 3: Regla de Dominio (Control de Fraude rechaza monto > $10,000) ---
    peticion_fraude = {
        "cliente_id": "CLI-003",
        "lineas": [
            {"descripcion": "Servidor Empresarial", "cantidad": 2, "precio_unitario": "6000.00"}
        ]
    }
    respuesta_fraude = adaptador_rest.crear_factura_http(peticion_fraude)
    print("  Respuesta REST (Fraude bloqueado):", json.dumps(respuesta_fraude, ensure_ascii=False))


if __name__ == "__main__":
    main()