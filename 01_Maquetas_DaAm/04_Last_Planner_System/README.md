# DaAm · Control Last Planner System — ejemplo 52 semanas

Una obra ficticia: Edificio de oficinas demostrativo DaAm. Programa 03/09/2026–01/09/2027 (364 días, 52 semanas jueves–miércoles). Semana de control S12; horizonte S12–S17. Datos de demostración; no son antecedentes de INGESEP ni de UCSC.

Cinco hojas: Resumen LPS, Programa resumen a 6 semanas, Lookahead y restricciones, Plan semanal, PPC y CNC. El programa maestro abarca 52 semanas; la Gantt Lookahead presenta seis semanas, conforme al modelo. Se incluyen 156 tareas distribuidas en nueve familias, habilitantes vinculados y compromisos históricos S1–S11 cerrados, S12 en proceso, más un saldo reprogramado.

Acceso público de consulta, sin contraseña ni sesiones. No admite cambios ni escritura de datos desde el navegador. Conserva filtros y exportaciones del modelo base.

## Publicar
Crear un repositorio independiente para esta maqueta. Subir el contenido de esta carpeta a la raíz, conservando `assets/`, `.streamlit/` y `maestro_demo.xlsx`. En Streamlit seleccionar `app.py`. No reemplazar el repositorio de las obras reales.

## Ejecutar
`pip install -r requirements.txt`

`streamlit run app.py`

El maestro ficticio está en `maestro_demo.xlsx`. El inicio de la semana y el período de control se definen en su configuración. Los resultados de PPC se basan en la columna Cumplida, no en inferencias de los porcentajes. La semana abierta se identifica como preliminar.
