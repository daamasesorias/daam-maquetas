# DaAm · Inspección Técnica y Calidad · V9

Plataforma reestructurada para una sola obra ficticia. Los documentos y registros técnicos se elaboran fuera de la plataforma. Aquí se cargan, vinculan y conservan para la trazabilidad y el expediente de validación de cada partida.

## Instalación y actualización

Para revisar el ejemplo, extraer la carpeta completa del ZIP, instalar `requirements.txt` y ejecutar:

```bash
pip install -r requirements.txt
streamlit run app.py
```

El archivo de entrada sigue siendo `app.py`. Se conserva la estructura común de las plataformas DaAm: `.streamlit/config.toml` junto a `app.py`, los módulos Python, `requirements.txt`, el maestro Excel y la carpeta `interfaz`. Mantener `.streamlit` en la raíz de la aplicación. Su configuración de tema es la misma de la versión anterior.

Utiliza `maestro_calidad.xlsx` y crea automáticamente `registros_calidad_v7.sqlite3`. Conservar el archivo antiguo y la base de versiones anteriores como respaldo. Esta versión no migra automáticamente los registros o adjuntos de las versiones V1–V6; para continuar con datos propios es necesario adaptarlos al nuevo maestro y cargar nuevamente sus respaldos. No borrar los archivos anteriores.

## Las cinco pestañas

1. Panel Central: estado del expediente de cada partida, NC pendientes, hallazgos pendientes, ensayos pendientes y alertas al corte del consolidado.
2. Protocolos de Calidad y No Conformidades: el protocolo pertenece a una partida; las no conformidades pertenecen a su protocolo. Carga de documentos arriba, fichas y documentos en dos columnas debajo.
3. Inspecciones y Hallazgos: la planilla de inspección documenta un recorrido; su alcance puede incluir varias partidas. Cada hallazgo pertenece a una inspección y a una partida de su alcance. No se convierte automáticamente en una NC.
4. Materiales y Ensayos: lotes, recepción, guías, certificados, cantidades y elementos donde se utilizaron; muestras, laboratorio, criterio, resultado e informe del ensayo.
5. Archivo Técnico y Reportes: línea de tiempo documental por partida y generación del informe general PDF/Excel.

## Flujo de trabajo

Los protocolos de calidad, planillas de inspección, NC, hallazgos, materiales, ensayos y validaciones profesionales se confeccionan y controlan externamente. Descargar el consolidado actual en Protocolos de Calidad y No Conformidades, actualizar sus hojas y cargarlo nuevamente. Cada carga se conserva como una versión con fecha, responsable, nombre del archivo y SHA-256. Los archivos adjuntos mantienen su propia revisión y fecha; una nueva carga del consolidado no los sobrescribe.

La plataforma no interpreta automáticamente un protocolo arbitrario ni extrae sus datos desde una imagen/PDF. El consolidado debe seguir las columnas del ejemplo. Los protocolos y planillas originales se adjuntan aparte como respaldo, en PDF, XLSX, PNG o JPEG.

Cada archivo se vincula a Partida, Protocolo, NoConformidad, Inspeccion, Hallazgo, Material o Ensayo. El expediente de una partida reúne esos vínculos. Se rechaza una nueva carga que elimine un ID con adjuntos ya vinculados, para evitar que pierdan su trazabilidad. Conservar los identificadores al actualizar.

## Maestro Excel

- Obra: datos de la única obra y fecha de corte del consolidado.
- Protocolos: ID del protocolo y de su partida, nombre de la partida, ubicación, familia, fecha, resultado, responsable y documento original. Incluye requisitos documentales y validación profesional declarada.
- NoConformidades: ID y protocolo de origen, descripción, estado, responsable, fechas, evidencias y documento de cierre.
- Inspecciones: ID, fecha, inspector, alcance y documento de la planilla original.
- AlcancesInspeccion: relación entre inspecciones y partidas; una inspección puede abarcar varias partidas.
- Hallazgos: ID, inspección y partida, descripción, estado, responsable, fechas, evidencias y documento de cierre.
- Materiales: material, proveedor, lote y recepción.
- UsosMaterial: material, partida, elemento, cantidad, unidad y fecha de uso.
- Ensayos: material y partida de uso, muestra, tipo, muestreo, laboratorio, resultado, criterio, estado e informe.
- Documentos: ID, nombre, tipo, revisión, fecha y ruta relativa del archivo de ejemplo.
- Vinculos: documento, tipo de entidad y registro al que pertenece.
- Evidencias: ID, título y ruta de fotografía.

Los archivos nuevos se adjuntan desde la plataforma; no es necesario inventar una ruta en el maestro. Su ID AD-… aparece en los expedientes, descargas e informe Excel. Puede utilizar ese ID como DocumentoValidacion o DocumentoCierre en el consolidado, siempre que sea del tipo correcto y esté vinculado al expediente o registro correspondiente.

## Validación de partidas

La plataforma verifica la consistencia del expediente; la aprobación profesional se realiza fuera de ella y se incorpora mediante el consolidado y el acta.

Una partida se muestra Validada cuando su declaración profesional, responsable, fecha y acta están cargados, dispone de los tipos documentales requeridos, su último protocolo es Conforme, no tiene NC ni hallazgos pendientes, sus cierres están respaldados, los materiales usados tienen certificados y los ensayos requeridos cumplen y tienen informe.

Si tiene un protocolo no conforme, una NC/hallazgo pendiente o un ensayo No cumple, se muestra Con incumplimientos. Si faltan respaldos, resultados o validación profesional, se muestra Pendiente de validación. Adjuntar un acta por sí solo no aprueba una partida. Los tipos requeridos se definen por partida en el consolidado; no son exigencias normativas preconfiguradas.

Los estados son los del último consolidado. El historial conserva las versiones anteriores para respaldo; la interfaz no reconstruye estados históricos seleccionando una fecha.

## Ejemplo y límites

Seis partidas, seis protocolos, tres NC, dos inspecciones, tres hallazgos, cuatro lotes, tres ensayos, 33 láminas documentales y 12 imágenes referenciales. Los documentos y criterios son ficticios, sin validez constructiva, normativa ni de certificación. El PDF general reúne estado, pendientes, índice documental y ensayos por partida; el Excel general incluye los datos y los vínculos.

Límites de carga: consolidado 15 MB y adjunto 10 MB. No incluye autenticación ni firma electrónica avanzada. Para una implantación con información real, usar almacenamiento persistente para SQLite y sus archivos. En alojamientos con disco temporal los registros pueden perderse al reiniciar.

## Verificación realizada

Probados los dos flujos independientes, relaciones de origen, alcance de inspecciones, lotes/uso/ensayos, validación de expedientes, bloqueo ante incumplimientos, adjuntos/revisiones, descargas, idempotencia, historial de cargas y exportaciones PDF/Excel. Ejecutadas las cinco vistas con DOM simulado; revisados los documentos, hojas y páginas renderizadas del informe. La revisión visual final en navegador de publicación queda pendiente.


Se incluyen 33 vistas PNG de los documentos de ejemplo. PDF, imágenes y Excel tienen vista de consulta; se conserva el original para descarga. Se mantiene .streamlit/config.toml original.


## V9: historial documental por partida

Las partidas se obtienen de los protocolos de calidad. El nuevo maestro no lleva una hoja Partidas independiente: Protocolos contiene el ID, nombre, ubicación y los datos de la partida. Si existen varios protocolos, se utiliza el más reciente por fecha e ID para el estado y metadatos. Mantenga los ID para conservar vínculos y adjuntos. Se admite la lectura de los consolidados anteriores con hoja Partidas y se conserva la misma base registros_calidad_v7.sqlite3.

La carga del consolidado se encuentra en Protocolos de Calidad y No Conformidades; los documentos se adjuntan en Protocolos, Inspecciones o Materiales y Ensayos. Los respaldos generales de la partida, como EETT, se vinculan a Partida desde Protocolos.

Archivo Técnico y Reportes muestra una línea de tiempo por partida, con documentos de todas las secciones ordenados de fecha más antigua a reciente; a igual fecha se ordenan por ID. Los adjuntos utilizan su fecha de carga. Seleccione el nombre para abrir la vista. Los Excel muestran los valores de las primeras 200 filas de cada hoja; el original conserva el formato completo y puede descargarse. Esta hoja no tiene formularios de ingreso ni carga.

El informe general PDF/Excel reúne el estado del último protocolo, NC abiertas/resueltas, hallazgos, inspecciones, materiales/lotes, certificados, ensayos, criterios, resultados y el historial documental. El estado del protocolo se distingue del diagnóstico de respaldos del expediente.

Actualización: reemplazar app.py, data_model.py, reports.py, schema.json, maestro_calidad.xlsx, README.md y la carpeta interfaz por los del paquete. Conservar .streamlit/config.toml y la base SQLite existente. No se modifica la estructura de carpetas.
