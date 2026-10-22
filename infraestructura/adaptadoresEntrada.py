import json
from aplicacion.crearFactura import CrearFactura


class AdaptadorREST:
    """
    Adaptador primario síncrono (API Web HTTP/REST).
    Traduce la petición HTTP JSON al contrato de entrada CrearFactura.
    """

    def __init__(self, caso_uso: CrearFactura):
        self._caso_uso = caso_uso

    def crear_factura_http(self, body_http: dict) -> dict:
        print("\n[AdaptadorREST] Petición HTTP POST /facturas recibida (Síncrona)")
        try:
            if not isinstance(body_http, dict):
                raise ValueError("El cuerpo de la petición debe ser un objeto JSON.")

            # Traduce el formato HTTP al diccionario que espera el caso de uso
            solicitud = {
                "cliente_id": body_http.get("cliente_id"),
                "lineas": body_http.get("lineas", [])
            }
            resultado = self._caso_uso.ejecutar(solicitud)
            return {"status": 201, "data": resultado}
        except ValueError as error:
            return {"status": 422, "error": str(error)}


class AdaptadorBrokerAMQP:
    """
    Adaptador primario asíncrono (Broker de mensajería como RabbitMQ).
    Deserializa el mensaje de la cola e invoca exactamente el mismo contrato CrearFactura.
    """

    def __init__(self, caso_uso: CrearFactura):
        self._caso_uso = caso_uso

    def consumir_mensaje(self, mensaje_json: str) -> dict:
        print("\n[AdaptadorBrokerAMQP] Mensaje recibido desde cola RabbitMQ (Asíncrono)")
        try:
            if not isinstance(mensaje_json, str):
                raise ValueError("El mensaje AMQP debe ser texto JSON.")

            evento = json.loads(mensaje_json)
            if not isinstance(evento, dict):
                raise ValueError("El mensaje debe contener un objeto JSON.")

            solicitud = {
                "cliente_id": evento.get("cliente_id"),
                "lineas": evento.get("lineas", [])
            }
            resultado = self._caso_uso.ejecutar(solicitud)
            print(f"  [AdaptadorBrokerAMQP] ACK enviado. Factura procesada: {resultado['id']}")
            return {"ack": True, "data": resultado}
        except ValueError as error:
            print(f"  [AdaptadorBrokerAMQP] NACK enviado. Rechazado por negocio: {error}")
            return {"ack": False, "error": str(error)}