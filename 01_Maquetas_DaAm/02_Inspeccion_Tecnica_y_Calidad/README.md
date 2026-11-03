# DaAm · Inspección Técnica y Calidad

Una obra ficticia. Instalar requirements.txt y ejecutar `streamlit run app.py`.

## Actualización V5

Se reemplazó Planos de inspección por Materiales y Ensayos. Las cinco pestañas son Panel Central, Inspecciones y carga de datos, Materiales y Ensayos, Hallazgos y No Conformidades, Archivo Técnico y Reportes.

Los levantamientos, protocolos, hallazgos, registros de materiales y ensayos se confeccionan externamente, en Excel. La plataforma recibe el consolidado y sus documentos terminados, vincula los respaldos y mantiene la trazabilidad. No se crean inspecciones ni hallazgos en pantalla.

Materiales incluye material, proveedor, lote, recepción, guía, certificado, ubicación de uso, elemento e inspección vinculada. Ensayos incluye muestra, material/lote, tipo de ensayo, fecha de muestreo, laboratorio, resultado, criterio, estado, informe y hallazgo asociado. Los archivos PDF/PNG/JPEG adicionales pueden adjuntarse a un material o ensayo. Cargar un informe no cambia el resultado o estado: estos se actualizan mediante el consolidado externo.

El maestro de ejemplo incluye cuatro lotes y tres ensayos con resultados Cumple, No cumple y Pendiente. Los criterios son ficticios y los documentos son imágenes ilustrativas. No representan certificación ni requisitos normativos de una obra real.

## Archivos que actualizar

Actualizar app.py, data_model.py, reports.py y la carpeta interfaz. El maestro incluido agrega las hojas Materiales y Ensayos; para mantener datos propios, añadir esas hojas con las mismas columnas al consolidado existente y cargarlo desde Inspecciones y carga de datos. No reemplazar un Excel propio por el ejemplo. Conservar y respaldar registros_calidad.sqlite3.

Si ya existe una planilla importada en SQLite, reemplazar el Excel local no sustituye ese consolidado: cargar la versión ampliada desde la plataforma. Las versiones anteriores sin Materiales y Ensayos siguen abriendo, pero esa pestaña se mostrará vacía hasta cargar los nuevos registros.

## Vínculos del maestro

Las relaciones utilizan ID. Materiales.Inspeccion y Materiales.Ubicacion deben existir; Guia y Certificado apuntan a Documentos.ID. Ensayos.Material apunta a Materiales.ID; Informe apunta a Documentos.ID y Hallazgo a Hallazgos.ID. Puede dejar los documentos aún no recibidos en blanco. Mantener los ID al actualizar para conservar los adjuntos vinculados.

Las cargas consolidadas reemplazan los datos y comentarios del consolidado anterior; incluir en el nuevo Excel todo lo que se desea mantener. Los documentos adjuntos desde la plataforma se conservan en SQLite. No incluye autenticación ni firma electrónica avanzada. Para alojamiento con disco temporal, usar almacenamiento persistente antes de operar con información real.

## Verificación

Verificadas las cinco vistas mediante DOM simulado, vínculos entre lotes, ensayos e informes, rechazo de relaciones cruzadas, compatibilidad con datos anteriores y carga de documentos PDF. Revisadas visualmente las hojas nuevas y el logo. Pendiente revisión visual final en navegador de publicación.
