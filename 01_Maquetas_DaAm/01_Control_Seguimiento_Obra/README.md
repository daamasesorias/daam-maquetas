# DaAm · Control y Seguimiento de Obra — versión Excel

Una obra de ejemplo. Las cinco hojas conservan el diseño aprobado y leen los datos desde `maestro_control_obra.xlsx`, junto a `app.py`. No hay datos de obra embebidos en JavaScript ni datos de respaldo que oculten errores del maestro.

## Hojas del Excel

- **Obra:** nombre, dirección, inicio y término programados, semanas totales, semana de control y monto contractual. Costos en millones de pesos chilenos, netos sin IVA.
- **Partidas:** ID, familia, nombre, unidad, cantidad total, presupuesto de costo y fechas originales.
- **Control_semanal:** un registro por semana e ID; cantidades programadas y reales acumuladas, costo real acumulado, costo pendiente estimado y fecha forecast de término.
- **Reprogramaciones:** ID, semana de entrada en vigencia y nuevas fechas. El histórico anterior se conserva.

Los datos iniciales son ficticios y reproducen el ejemplo de 24 semanas anterior. Last Planner es otro ejemplo de 52 semanas. Ambos leen un Excel en la raíz, cada uno con las columnas correspondientes a su método de control.

## Actualizar datos

1. Editar el Excel conservando las hojas, encabezados e ID relacionados.
2. Guardarlo con el mismo nombre y reemplazarlo en el repositorio.
3. Actualizar la aplicación. Cada ejecución lee el archivo, sin caché de datos.

Cambiar datos no requiere editar JavaScript. No se utiliza XML en esta versión. El Excel es la fuente única para los datos de obra. Mantener un registro por partida y semana para todo el programa: el ejemplo incluye los 24 cortes. Al ampliar el programa, agregar los registros correspondientes. Las cantidades deben estar entre cero y el total, los costos no pueden ser negativos, y el forecast de una partida incompleta debe ser posterior al corte. Las divisiones sin denominador válido muestran «No aplica».

La aplicación calcula ponderaciones, avances, desviaciones, CPI y proyecciones a partir del maestro. El forecast distribuye el remanente por partida hasta la fecha estimada indicada en el Excel; no calcula ruta crítica. El avance al corte y los totales de costo se concilian entre tablas, curvas y tarjetas. La clasificación de atraso usa el programa vigente, y las comparaciones de desempeño conservan la línea base.

## Publicar

Reemplazar todo el contenido del repositorio de esta maqueta con el contenido de `01_DaAm_Control_Obra`. Deben quedar en la raíz `app.py`, `data_model.py`, `requirements.txt` y `maestro_control_obra.xlsx`; mantener `interfaz/` y `.streamlit/`. En Streamlit seleccionar `app.py`.

## Ejecutar

`pip install -r requirements.txt`

`streamlit run app.py`

La aplicación requiere Streamlit para recibir los datos del Excel. Abrir directamente el HTML no carga el maestro. Si falta el archivo o contiene datos inválidos, se muestra un error en lugar de datos simulados.
