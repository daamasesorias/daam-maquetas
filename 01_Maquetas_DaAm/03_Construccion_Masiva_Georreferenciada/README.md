# DaAm · Construcción masiva georreferenciada

Maqueta aprobada, con diseño compacto para computador y celular. Datos de demostración; consulta sin edición. La vista satelital necesita conexión a Internet para cargar Leaflet y las imágenes de Esri.

## Cargar a GitHub

1. Extraer este ZIP.
2. Crear un repositorio independiente para esta maqueta.
3. Cargar el contenido de `03_DaAm_Construccion_Masiva` en la raíz del repositorio, conservando las carpetas.
4. Deben quedar `app.py`, `requirements.txt`, `README.md`, la carpeta `interfaz` y la carpeta `.streamlit` en la raíz. `.gitignore` es opcional.

No subir solamente el ZIP. No mezclar estas maquetas con el repositorio `ingesep-lps` de obras reales.

## Publicar en Streamlit Community Cloud

Seleccionar el repositorio, su rama principal y `app.py` como archivo de entrada. La instalación utiliza `requirements.txt`. Se recomienda Python 3.11 o superior.

## Ejecutar localmente

```bash
pip install -r requirements.txt
streamlit run app.py
```

La interfaz aprobada se encuentra en `interfaz/index.html`. Las imágenes y el mapa se conservan con sus archivos asociados. No requiere claves ni bases de datos. Para información real será necesario integrar la fuente de cada obra.
