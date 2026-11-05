# DaAm · Multi Obra

Demostración con seis obras ficticias en Santiago, Talca, Concepción (dos), Temuco y Puerto Montt. El avance físico se revisa por proyecto; únicamente los importes económicos se consolidan. Moneda: millones de pesos chilenos netos (MM CLP).

## Publicar en Streamlit Community Cloud

1. Descomprima y suba la carpeta completa `05_DaAm_Multi_Obra` al repositorio. Conserve `interfaz`, `.streamlit`, el Excel y los archivos Python. No reemplace las carpetas de las otras plataformas.
2. Cree una aplicación y seleccione `05_DaAm_Multi_Obra/app.py` como archivo principal. Si está dentro de `01_Maquetas_DaAm`, anteponga ese directorio a la ruta. Seleccione Python 3.12.
3. Las dependencias están en `requirements.txt`. Para ejecutar localmente: `pip install -r requirements.txt` y `streamlit run app.py` desde esta carpeta.

## Uso

Seis hojas: resumen ejecutivo, programa general de obras, mapa de obras, detalle, comparativo económico y flujo financiero anual. Los filtros se aplican al corte seleccionado. Los nombres de las obras y la lista del mapa abren el detalle. El mapa permite acercar y seleccionar pines; sus íconos representan edificio, clínica, colegio y bodegas. El color representa estado: gris sin iniciar/sin datos; azul terminada; rojo en ejecución atrasada; amarillo en ejecución sin atraso.

Las seis coordenadas son referenciales. Leaflet está incluido dentro de la carpeta. El fondo cartográfico de OpenStreetMap necesita conexión; si no está disponible, los pines y la lista mantienen el acceso a cada obra. El mapa solo se carga al abrir su hoja. Se incluyen seis renders arquitectónicos generados con IA de obras ficticias; no son fotografías de obras reales.

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

Atraso físico: avance real inferior al programado, o inicio programado vencido sin inicio real. El atraso de término compara forecast con término programado; se muestra por separado. Una obra terminada requiere fecha de término real. El programa base y el historial del ejemplo usan curvas S con ritmos variables. La proyección gráfica del pendiente usa un perfil S referencial desde el último registro hasta el término informado; no modifica los registros del Excel ni constituye un nuevo programa contractual.

Si falta el corte exacto se usa el último disponible y se advierte su fecha; no se inventan registros.  El comparativo puede descargarse en CSV. Los datos, imágenes y nombres incluidos son ficticios para revisión de uso.

## Flujo financiero anual

`Plan_base` contiene el programa completo: Obra, Fecha, Avance_programado (0–1) y Costo_programado_MM_CLP. Los gráficos no limitan el programa a los registros históricos.

`Flujo_financiero` contiene una fila por obra, versión de corte y mes (día 1). Sus columnas son: Obra, Fecha_corte, Mes, Ingreso_programado_MM_CLP, Egreso_programado_MM_CLP, Ingreso_real_MM_CLP, Egreso_real_MM_CLP, Ingreso_proyectado_MM_CLP y Egreso_proyectado_MM_CLP. Mantenga doce meses por año para todas las obras, incluyendo ceros cuando corresponda.

Real es cobrado/pagado hasta el corte; proyectado es únicamente lo pendiente. Un mes cerrado tiene real y deja proyectado vacío; un mes futuro deja real vacío y contiene proyectado. El mes del corte admite real parcial y proyección del resto. Real + proyectado suma ambos sin duplicarlos. El programa corresponde al mes completo y es una referencia separada.

La hoja selecciona la última versión del flujo no posterior al corte. El ejemplo incluye una versión al 05/11/2026 con 2026 y 2027 completos; los cortes anteriores muestran que no existe una versión financiera disponible. Puede agregar versiones históricas conservando los mismos encabezados.

Ingresos del ejemplo: cobros con desfase de 30 días, 5% retenido y liberado 45 días tras el término. Egresos: desembolsos de obra según el perfil de costo del ejemplo; se supone pago en el mismo período. Estos supuestos solo generan datos ficticios; la plataforma consume los importes del maestro. Saldo inicial de origen cero al 01/01/2026; cada año arrastra el saldo de los años anteriores. No incluye IVA, deuda, gastos corporativos ni caja bancaria. Flujo de caja y utilidad contable son conceptos diferentes.

El gráfico y la tabla mensual muestran real + proyectado. La vista Programado/Real/Proyectado y el concepto Ingresos/Egresos/Flujo neto controlan la matriz mensual por obra. Los saldos negativos y la necesidad máxima de fondos hacen visible el financiamiento requerido por la cartera seleccionada.
