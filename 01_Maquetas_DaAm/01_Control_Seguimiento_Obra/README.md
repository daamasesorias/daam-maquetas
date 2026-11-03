# DaAm · Control y Seguimiento de Obra — maqueta V2

Ejemplo de consulta de una sola obra, con datos ficticios. Incluye el logo aprobado «DaAm Plataformas · Control y Seguimiento de Obra». No requiere claves ni base de datos.

## Cinco hojas

1. **Resumen ejecutivo:** datos de obra y nueve tarjetas; sin curvas.
2. **Programa de obra:** Gantt de todo el programa con filtros combinados por fechas, semanas, familia y estado; fechas originales y nuevas fechas; grupos desplegables.
3. **Avance físico:** Curva S programada, real y forecast, y tabla de avance ponderado.
4. **Costos y presupuesto:** Curva S de costos y tabla de presupuesto, costos al corte y proyección final.
5. **KPIs:** indicadores al corte e histórico semanal; sin PPC ni CNC.

## Actualizar el repositorio existente

Extraer el ZIP y reemplazar el contenido del repositorio de la maqueta con el contenido de la carpeta `01_DaAm_Control_Obra`. Mantener la estructura: `app.py` en la raíz y `index.html`, `app.js`, `logo-control-obra.png` y `favicon.svg` dentro de `interfaz/`. Conservar también `.streamlit/config.toml` y `requirements.txt`.

No cargar solo el ZIP a GitHub. No mezclar con la plataforma INGESEP de obras reales. En Streamlit usar `app.py` como archivo principal y Python 3.11 o superior.

## Ejecución local

```bash
pip install -r requirements.txt
streamlit run app.py
```

También se puede abrir `interfaz/index.html` directamente para consultar la maqueta sin Streamlit. Se deben conservar los archivos de esa carpeta juntos.

## Criterios de cálculo del ejemplo

- Obra ficticia: centro logístico en Hualpén, 18 partidas, seis familias, programa base de 24 semanas. Semana de jueves a miércoles.
- El selector de control permite revisar S01 a S24. El calendario de la Gantt alcanza S28 para mostrar las reprogramaciones y proyecciones.
- Monto contractual y presupuesto de costo se mantienen separados. Los montos se expresan en millones de pesos chilenos, netos sin IVA.
- El avance físico se pondera por presupuesto de costo. La suma del avance ponderado coincide con el Resumen ejecutivo y el punto de la curva real en cada corte.
- Costo final proyectado = costo real incurrido + costo pendiente estimado. No se confunde costo con pago.
- Se mantiene la línea base para curvas y desempeño. La clasificación operativa de atraso usa el programa vigente a cada corte. Reprogramar no garantiza cumplimiento: una actividad puede volver a incumplir su nuevo programa.
- La tarjeta de reprogramaciones cuenta cambios registrados en la semana; el filtro Reprogramadas incluye todas las partidas con reprogramación vigente a ese corte.
- Una partida atrasada se cuenta una sola vez aunque tenga más de un incumplimiento. Las partidas activas y las retrasadas pueden superponerse.
- No se desplazan automáticamente las fechas de actividades que no empiezan. Solo dos partidas tienen reprogramaciones explícitas en el ejemplo; el histórico anterior a ellas se conserva.
- CPI = valor ganado / costo real; valor ganado = suma de presupuesto por porcentaje de avance físico. Divisiones sin denominador válido se muestran como «No aplica».
- El forecast distribuye el remanente por partida hasta términos estimados del escenario; no es un cálculo de ruta crítica ni una predicción de IA. Es demostrativo, no una herramienta para decidir sobre una obra real.
- Los datos se generan de forma reproducible dentro de `interfaz/app.js`. No hay edición, cargas de Excel, almacenamiento, usuarios ni conexión con fuentes reales.

Para integrar obras reales se requiere definir fuentes de datos, permisos, actualización y validación de programación y costos.
