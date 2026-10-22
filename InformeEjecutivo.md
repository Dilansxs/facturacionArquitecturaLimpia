# Informe ejecutivo — Sistema de facturación con Arquitectura Limpia

## Objetivo

Aplicar Arquitectura Limpia a la creación de facturas para permitir cambiar el
adaptador de entrada y el proveedor de persistencia sin trasladar esas decisiones
al dominio ni duplicar las reglas de negocio.

## Arquitectura implementada

- **Adaptadores de entrada:** `AdaptadorREST` traduce un cuerpo de petición y
  `AdaptadorBrokerAMQP` deserializa un mensaje JSON. Ambos invocan el contrato
  `CrearFactura`.
- **Aplicación:** `CrearFacturaUseCase` valida y transforma la solicitud,
  coordina fraude e impuestos y guarda la factura mediante `RepositorioFacturas`.
- **Dominio:** `Factura` y `LineaFactura` mantienen las invariantes de los
  importes; `ControlFraude` aplica el límite y la lista de clientes bloqueados;
  `PoliticaFiscal` aplica el 0 % a clientes `EXP-` y la tasa por defecto al resto.
- **Infraestructura:** los repositorios en memoria, PostgreSQL y Oracle cumplen
  el mismo contrato. `REPOSITORIO` selecciona el adaptador en esta capa.

El diagrama de clases correspondiente está en
[diagrama_arquitectura.puml](./diagrama_arquitectura.puml).

## Alcance y limitaciones

Las implementaciones PostgreSQL y Oracle son simulaciones, tal como permite el
enunciado: conservan los datos en memoria e imprimen la operación representativa;
no abren conexiones reales. Los adaptadores REST y AMQP representan la traducción
de los protocolos al contrato de aplicación, pero no incluyen un servidor HTTP ni
una conexión/consumidor real de RabbitMQ.

Los precios e importes usan `Decimal`, en lugar de `float`, para evitar errores
de precisión en cálculos monetarios. Las solicitudes inválidas se rechazan con
error controlado: REST devuelve estado 422 y el adaptador del broker devuelve
NACK.

## Pruebas

Ejecutar desde la raíz del proyecto:

```text
python -m unittest discover -v
```

Las pruebas cubren cálculo y persistencia, fraude por monto y cliente bloqueado,
política fiscal de exportación, solicitudes REST inválidas, mensajes JSON
incorrectos, simetría de adaptadores e intercambiabilidad de repositorios.

## Ventajas obtenidas

- Un cambio de adaptador de entrada no duplica el caso de uso.
- Las reglas de negocio se aplican en el dominio independientemente del adaptador.
- El proveedor de persistencia se selecciona en infraestructura, sin cambios en
  aplicación ni dominio.
- Los dobles en memoria permiten ejecutar las pruebas sin servicios externos.