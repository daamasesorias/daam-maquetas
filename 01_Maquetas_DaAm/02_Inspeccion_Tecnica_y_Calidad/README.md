# DaAm · Inspección Técnica y Calidad

Demostración para una sola obra ficticia: Edificio Mirador Biobío. Mantiene la identidad gráfica de las plataformas DaAm, con el logo original y el subtítulo de esta especialidad.

## Inicio

Desde esta carpeta:

```bash
pip install -r requirements.txt
streamlit run app.py
```

Para actualizar la plataforma anterior, reemplazar su carpeta de código por el contenido completo de este paquete. El archivo de entrada es `app.py`. Conservar cualquier respaldo previo antes de reemplazarlo.

## Cinco pestañas

1. Panel Central: datos de obra, cumplimiento de criterios aplicables, no conformidades, alertas y cobertura de inspecciones.
2. Inspecciones en Terreno: ubicación y plantilla, Cumple / No cumple / No aplica, borrador, fotografía y emisión del protocolo. Un resultado no conforme exige descripción, fecha y evidencia, y genera un hallazgo.
3. Planos e Interacción Visual: planos 2D por piso y especialidad, pines de hallazgos e inspecciones aprobadas, líneas, círculos y flechas guardadas por plano y revisión.
4. Hallazgos y No Conformidades: fotografías, plazos, responsable, comentarios y reparación. El contratista solicita revisión; ITO verifica y cierra o devuelve.
5. Archivo Técnico y Reportes: documentos e imágenes de ejemplo, informes diarios/semanales PDF y Excel y registro de validación de protocolos aprobados.

## Datos y archivos

`maestro_inspeccion_calidad.xlsx`, junto a `app.py`, es la fuente inicial. Contiene 11 hojas: Obra, Ubicaciones, Plantillas, Criterios, Inspecciones, Respuestas, Hallazgos, Comentarios, Documentos, Evidencias y Planos. Las relaciones se realizan mediante ID; mantener los ID al editar el maestro.

El ejemplo contiene 24 inspecciones, cinco hallazgos, 17 documentos, nueve planos y 12 imágenes referenciales. Los documentos son láminas ilustrativas, no expedientes técnicos completos. Planos y fotografías son ficticios, sin validez para construir o certificar trabajos.

Los registros nuevos se conservan en `registros_calidad.sqlite3`, que la aplicación crea automáticamente. El Excel se lee al ejecutar la aplicación; las modificaciones operativas se superponen desde SQLite. Respaldar ambos archivos. Cambiar un ID existente en Excel puede invalidar la relación con registros guardados. Para reiniciar exclusivamente la demostración, detener la aplicación y retirar su SQLite, conservando un respaldo si corresponde.

Las rutas de documentos, planos y fotos son relativas a `interfaz/`. Las fotografías nuevas se conservan con el registro en SQLite; el límite por imagen es 5 MB.

## Interpretación

Cumplimiento = criterios Cumple / criterios aplicables evaluados. No aplica queda fuera del denominador. Cobertura = protocolos ejecutados / programados al corte. Aprobación = protocolos aprobados / ejecutados. Una inspección ejecutada puede estar rechazada: no equivale a aprobación. Las observaciones se muestran en hallazgos, pero no aumentan el contador de no conformidades.

La fecha de corte inicial es 03/11/2026. Los filtros permiten cortes posteriores; se presenta el estado actual registrado, no una reconstrucción histórica de estados. Los informes incluyen actividad del período y pendientes al corte, utilizando el estado registrado al generar la descarga.

## Alcance de la demostración

Los roles ITO y Contratista son selectores demostrativos, sin autenticación. La validación de actas es un registro interno, no una firma electrónica avanzada. Se incluyen planos 2D; no se incluye visor BIM.

Para uso compartido real se requiere autenticación y almacenamiento persistente. En alojamientos que reinician el disco local, SQLite puede perderse; usar un volumen permanente o una base de datos duradera antes de operar con información real.

## Verificación

Se verificaron lectura y relaciones del Excel, cálculos del panel, emisión y rechazo de formularios incompletos, flujo de reparación/cierre por rol, reinspección, persistencia, anotaciones, validación de actas, idempotencia y exportaciones PDF/Excel. Se ejecutaron las cinco vistas con DOM simulado y se revisó la salida PDF. La revisión visual final en navegador queda pendiente en el entorno de publicación.
