# DaAm · Multi Obra

Demostración con seis obras ficticias en Santiago, Talca, Concepción (dos), Temuco y Puerto Montt. El avance físico se revisa por proyecto; únicamente los importes económicos se consolidan. Moneda: millones de pesos chilenos netos (MM CLP).

## Publicar en Streamlit Community Cloud

1. Descomprima y suba la carpeta completa `05_DaAm_Multi_Obra` al repositorio. Conserve `interfaz`, `.streamlit`, el Excel y los archivos Python. No reemplace las carpetas de las otras plataformas.
2. Cree una aplicación y seleccione `05_DaAm_Multi_Obra/app.py` como archivo principal. Si está dentro de `01_Maquetas_DaAm`, anteponga ese directorio a la ruta. Seleccione Python 3.12.
3. Las dependencias están en `requirements.txt`. Para ejecutar localmente: `pip install -r requirements.txt` y `streamlit run app.py` desde esta carpeta.

## Uso

Cinco hojas: resumen ejecutivo, programa general de obras, mapa de obras, detalle y comparativo económico. Los filtros se aplican al corte seleccionado. Los nombres de las obras y la lista del mapa abren el detalle. El mapa permite acercar y seleccionar pines; sus íconos representan edificio, clínica, colegio y bodegas. El color representa estado: gris sin iniciar/sin datos; azul terminada; rojo en ejecución atrasada; amarillo en ejecución sin atraso.

Las seis coordenadas son referenciales. La cartografía de OpenStreetMap y Leaflet necesita conexión; si no está disponible, la lista mantiene el acceso a cada obra. El mapa solo se carga al abrir su hoja. Las imágenes incluidas son ilustraciones de ejemplo, no fotografías de obras reales.

## Excel maestro

Reemplace `maestro_multi_obra.xlsx` conservando hojas, encabezados e identificadores. No cambie los nombres de las columnas. La aplicación valida duplicados, vínculos, fechas y rangos antes de cargar los datos; recarga cuando cambia el archivo. Los Excel de cada obra y su consolidación al maestro se gestionan fuera de esta plataforma.

- `Configuracion`: cartera, fecha de corte y moneda.
- `Obras`: identidad, responsables, ubicación, fechas de inicio/término programadas y reales, contrato y presupuesto de costo.
- `Programa`: actividades/hitos por obra, con inicio y fin.
- `Avance_fisico`: obra, corte, programado y real como fracción entre 0 y 1.
- `Costos`: obra, corte, gasto programado, gasto real acumulado y costo pendiente estimado, todos en MM CLP.
- `Forecast`: obra, corte y término proyectado.
- `Fotografias`: obra, fecha, descripción, ruta relativa de imagen y tipo. Coloque los archivos dentro de `interfaz`; las rutas se resuelven desde esa carpeta.

Cada obra/corte debe existir en las tres hojas de avance, costos y forecast. Conserve el historial para consultar cortes anteriores. Los registros se vinculan por ID de obra. Cada obra tiene una única fila por corte en esas tres hojas. Las imágenes deben ser SVG, PNG, JPEG o WebP y usar rutas relativas sin `..`.

## Criterios de cálculo

Costo final proyectado = costo real + pendiente estimado. Desviación final = costo final proyectado − presupuesto. Desviación del gasto al corte = real − programado: por sí sola no representa ahorro ni sobrecosto. El contrato no es el presupuesto de costo.

Atraso físico: avance real inferior al programado, o inicio programado vencido sin inicio real. El atraso de término compara forecast con término programado; se muestra por separado. Una obra terminada requiere fecha de término real. La proyección gráfica individual de avance es una referencia lineal hasta la fecha de término informada, no un nuevo programa contractual.

Si falta el corte exacto se usa el último disponible y se advierte su fecha; no se inventan registros. Bodegas Austral tiene intencionalmente un reporte pendiente para ilustrar esta alerta. El comparativo puede descargarse en CSV. Los datos, imágenes y nombres incluidos son ficticios para revisión de uso.
