# DaAm · Inspección Técnica y Calidad · Versión corregida

Plataforma para una sola obra ficticia, de uso exclusivo de la ITO. Logo completo en un único archivo SVG, con «Inspección Técnica y Calidad» integrado en una sola línea.

## Ejecutar

```bash
pip install -r requirements.txt
streamlit run app.py
```

Reemplazar la carpeta de código anterior completa. Entrada: `app.py`. Si existen registros propios, respaldar el Excel y `registros_calidad.sqlite3` antes de actualizar; no eliminar la base para aplicar esta versión.

## Flujo de información

La información se toma en terreno fuera de la plataforma y se consolida en Excel. En «Inspecciones y carga de datos», descargar la planilla actual, actualizar los resultados y cargar el archivo .xlsx. La aplicación valida la estructura antes de aceptarlo. No se confeccionan ni emiten protocolos en pantalla.

El Excel maestro incluye: Obra, Ubicaciones, Plantillas (catálogo de tipos de inspección), Criterios, Inspecciones, Respuestas, Hallazgos, Comentarios, Documentos, Evidencias y Planos. Mantener las hojas, columnas e identificadores de la plantilla. `Programada` se conserva como campo de fecha de referencia para compatibilidad con el maestro; no constituye un calendario de protocolos en la interfaz. `Ejecutada` corresponde a la fecha de inspección registrada.

Al importar, el Excel consolidado reemplaza los datos fuente y resultados anteriores de inspecciones y hallazgos, incluyendo su trazabilidad. Conservar estos cambios en el consolidado antes de cargarlo. Los documentos adjuntados desde la plataforma y las anotaciones de planos se conservan. Las validaciones de actas se reinician para revisar el nuevo consolidado.

La fuente inicial es `maestro_inspeccion_calidad.xlsx`, junto a `app.py`. Las planillas importadas y las gestiones posteriores quedan guardadas en `registros_calidad.sqlite3`. Para cargar información nueva después de comenzar a trabajar, utilizar el importador de la plataforma. Respaldar Excel y SQLite.

## Cinco pestañas

1. Panel Central: datos de obra, cumplimiento de criterios, no conformidades abiertas/en revisión/cerradas, inspecciones registradas/aprobadas/sin resultado y alertas urgentes.
2. Inspecciones y carga de datos: importar/exportar Excel y consultar resultados. Sin selector de roles ni formularios de emisión.
3. Planos de inspección: nueve planos 2D con recintos, mobiliario, puertas, ventanas, ejes y referencias; variantes de arquitectura, estructura e instalaciones sanitarias. Pines consultables y herramientas Línea, Círculo y Flecha, disponibles directamente para ITO. Dibujar arrastrando y pulsar Guardar anotaciones. Deshacer retira la última marca; volver a guardar para persistir el cambio.
4. Hallazgos y No Conformidades: evidencia inicial y de reparación, plazos, comentarios y cierre. Consulta de registros y carga de documentos elaborados fuera de la plataforma. El estado se actualiza mediante Excel.
5. Archivo Técnico y Reportes: adjuntar protocolos u otros documentos PDF/PNG/JPEG vinculados a una inspección, consultar imágenes y descargar reportes PDF/Excel. Los PDF adjuntos se descargan; las imágenes se amplían dentro de la plataforma.

## Ejemplo y alcance

24 inspecciones, cinco hallazgos, 17 documentos ilustrativos, nueve planos y 12 fotografías ficticias. Los documentos son láminas de referencia; los planos no tienen validez constructiva. Fecha de corte inicial: 03/11/2026.

Cumplimiento = criterios Cumple / criterios aplicables evaluados. No aplica se excluye. Aprobación = inspecciones aprobadas / inspecciones con resultado. Las observaciones no aumentan el contador de no conformidades. Se muestra el estado actual registrado, no una reconstrucción histórica de estados.

Máximos de carga: Excel 15 MB, documento 10 MB y fotografía de reparación 5 MB. El importador requiere recursos de documentos, evidencias y planos existentes dentro de `interfaz/`; los nuevos protocolos se incorporan mediante «Adjuntar protocolo o documento».

No incluye cuentas de contratistas, autenticación, visor BIM ni firma electrónica avanzada. La validación de actas es un registro interno. En un despliegue con disco temporal, sustituir SQLite por almacenamiento persistente antes de usar datos reales.

## Verificación

Comprobadas importación y validación del Excel, conservación de adjuntos/anotaciones, documento PDF vinculado, consulta de estados y documentos vinculados, exportaciones, cinco vistas y arrastre de las tres herramientas mediante DOM simulado. Logo y plano revisados mediante renderizado. La revisión visual final en el navegador de publicación queda pendiente.


## Corrección V3
Logo con texto convertido en trazos, en una línea y sin sustitución de tipografía. Hallazgos y No Conformidades es una vista de consulta de la información de Excel y de carga/descarga de documentos confeccionados externamente. Se retiraron los comentarios editables y las acciones de reparar, cerrar o reabrir hallazgos. El estado y la trazabilidad se actualizan mediante la planilla consolidada. Adjuntar documentos no cambia el estado. Los documentos adjuntos quedan asociados al ID del hallazgo y se conservan al importar Excel.
