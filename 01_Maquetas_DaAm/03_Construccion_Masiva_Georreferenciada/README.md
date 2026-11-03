# DaAm · Construcción Masiva Georreferenciada

Una obra ficticia, 36 viviendas en el entorno de Talcahuano, en los mismos puntos de la maqueta original. Viviendas impares Tipo A de un piso (60 m², 2 dormitorios, 1 baño); pares Tipo B de dos pisos (90 m², 3 dormitorios, 2 baños). Hay 18 de cada tipología. Planos y renders referenciales.

## Ejecutar

Requiere Python 3.10 o superior.

```bash
pip install -r requirements.txt
streamlit run app.py
```

En Streamlit Community Cloud, seleccionar `app.py` como archivo principal y conservar esta estructura. Reemplazar todos los archivos de la plataforma anterior por el contenido de esta carpeta; no mezclar interfaces de versiones diferentes. No se requiere carpeta `proyectos` ni base de datos externa.

## Fuente única de datos

`maestro_construccion_masiva.xlsx` está en la raíz, junto a `app.py`. La plataforma lo lee al iniciar o actualizar la aplicación. Los datos no están incrustados en el HTML. Después de editar el archivo, guardar en Excel para recalcular las fórmulas y actualizar la aplicación; en Cloud, subir también el Excel actualizado al repositorio.

| Hoja de Excel | Contenido editable |
|---|---|
| Obra | Nombre, dirección, fechas, monto contractual, semanas y semana de control predeterminada |
| Tipologias | Pisos, superficie, dormitorios, baños y nombres de archivos de plano y render |
| Viviendas | ID, sector, etapa, tipología, coordenadas, fechas reales y presupuesto de costo |
| Programa | Nueve partidas por vivienda, peso, presupuesto por fórmula y fechas de línea base |
| Control_semanal | Una fila por vivienda y semana, avances acumulados P01–P09, gasto real, costo pendiente estimado y término proyectado |
| Reprogramaciones | Vivienda y partida, semana desde la que aplica, nuevas fechas y motivo |

Montos en millones de CLP netos, sin IVA: `48` significa $48.000.000. Avances en fracción: `0,5` equivale al 50 %; Excel los muestra como porcentaje. Los campos vacíos no representan automáticamente cero. Cada semana registrada requiere sus 36 viviendas. Los cortes van de lunes a domingo, desde el 13/07/2026. Semana predeterminada S12, corte 04/10/2026. El ejemplo incluye 35 semanas y comienza con datos ficticios completos para explorar distintos cortes.

Al registrar información real, dejar en blanco los inicios y términos reales que todavía no ocurren. El ejemplo tiene fechas reales ficticias posteriores al corte inicial para permitir recorrer su historia; la plataforma las oculta hasta el corte correspondiente. Las viviendas terminadas deben tener sus nueve avances en 100 %, fecha real de término y costo pendiente cero. Registrar nuevas reprogramaciones en filas adicionales; conservar la línea base.

## Cinco hojas de la plataforma

1. **Resumen ejecutivo:** datos de la obra, avance programado/real, desviación y forecast de término; gasto programado/real, desviación al corte y forecast final; viviendas terminadas, en proceso, atrasadas, con sobrecosto e inicios pendientes. Tabla comparativa agrupada por tipología. Sin curvas ni mapa.
2. **Programación rítmica:** Gantt con dos equipos que comienzan simultáneamente. Equipo 1 para viviendas de un piso, con ciclo de 7 días por partida; Equipo 2 para dos pisos, con ciclo de 9 días por partida. Cada especialidad avanza por las 18 viviendas sin solaparse consigo misma. Nueve segmentos de colores por vivienda, fechas, avance y línea de corte; comparación con línea base y programa vigente. Filtros por sector, etapa, tipología, vivienda, semanas y fechas. Las filas se ordenan por equipo y secuencia de construcción.
3. **Mapa del proyecto:** 36 puntos originales, vistas por estado/atraso/sobrecosto y ficha seleccionable que abre el detalle. Fondo satelital Esri con atribución. Si falla la cartografía, los puntos siguen disponibles; si no carga Leaflet, hay una vista esquemática por las mismas coordenadas.
4. **Detalle de vivienda:** estado, atraso, fechas base/vigentes/reales, avance y costos, plano y render ampliables de la tipología. Selector para revisar otras viviendas.
5. **Avance por partidas por vivienda:** filtros por etapa, tipología, vivienda y semana; sin filtro ni encabezados por sector. Excavaciones; Fundaciones; Estructura Muro; Cubierta; Pisos interiores; Muros interiores; Terminaciones; Instalaciones; Obras Exteriores. Fechas base y vigentes, peso, avance programado, real y aporte al total, con alertas por partida.

## Criterios de cálculo

- Avance de una vivienda = suma de peso de cada partida × avance real de esa partida. Los nueve pesos deben sumar 100 %.
- Avance del conjunto = promedio de avances de vivienda ponderado por su presupuesto de costo. Así se consideran las dos tipologías. Las cinco vistas usan el mismo cálculo.
- Avance programado de cada partida = distribución lineal entre inicio y fin inclusivos de la línea base. El ejemplo no utiliza calendario de feriados ni rendimientos diarios variables. El avance real proviene del control semanal; no se deduce de fechas.
- Costo programado al corte = suma del presupuesto por partida × avance programado. Es una distribución referencial del gasto, no una programación de pagos o anticipos.
- Desviación de avance = real − programado en puntos porcentuales. Se conserva la línea base para esta comparación.
- Atraso operativo = avance real inferior al exigido por la programación vigente al corte. Incluye viviendas que debían iniciar y aún están en cero. Una reprogramación cuyo nuevo inicio aún no vence no genera atraso por su fecha original.
- Una vivienda en proceso puede estar atrasada y con sobrecosto. Las tarjetas no son categorías sumables. Las terminadas se comparan con la fecha base para informar si terminaron con atraso.
- Costo final proyectado = gasto real acumulado + costo pendiente estimado al corte. El forecast no es el gasto acumulado extrapolado automáticamente. Sobrecosto = costo final proyectado − presupuesto de costo.
- La desviación de gasto real vs. programado al corte no se califica por sí sola como ahorro o sobrecosto. Comparar viviendas de la misma tipología mediante su costo final proyectado y desviación respecto del presupuesto.
- Forecast del plazo global = fecha de término más tardía entre viviendas, según los forecasts registrados en el corte. Se compara con el término contractual programado.
- El monto contractual representa el ingreso contratado; el presupuesto de costo (inicialmente $2.106 MM) representa el costo previsto. No se confunden.

Los planos SVG, renders PNG y el único logo están en `interfaz`. El Excel relaciona cada tipología con sus imágenes. El render es una imagen exterior, no un modelo 3D navegable. Los planos son esquemas de demostración, no documentos constructivos. La aplicación requiere internet para instalar dependencias y para la cartografía satelital.

## Verificación de la entrega

Se revisaron los seis esquemas del Excel, las 36 coordenadas, la alternancia de las tipologías, los 35 cortes, los 324 registros de programa, la suma de ponderaciones, la consistencia de fechas/estados, las reprogramaciones y la reconciliación de costos y avances. Se ejecutaron pruebas de las cinco vistas y filtros con un DOM de prueba. No se realizó una sesión visual en un navegador real en este entorno.

Los marcadores del mapa representan casas de uno o dos pisos con su número visible, manteniendo los colores de estado y alertas. El logo mantiene el diseño existente con mayor espacio alrededor.
