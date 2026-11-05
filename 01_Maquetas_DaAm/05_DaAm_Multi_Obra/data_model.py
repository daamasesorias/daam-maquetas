"""Load and validate the single portfolio master; physical progress stays project-specific."""
from datetime import datetime,date
from pathlib import Path
import math
import pandas as pd
SCHEMA={
 'Configuracion':['Parametro','Valor'],
 'Obras':['ID','Nombre','Tipo','Region','Comuna','Direccion','Latitud','Longitud','Mandante','Administrador','Inicio_programado','Fin_programado','Inicio_real','Fin_real','Monto_contractual_MM_CLP','Presupuesto_MM_CLP'],
 'Programa':['ID','Obra','Actividad','Inicio','Fin'],
 'Avance_fisico':['Obra','Fecha_corte','Programado','Real'],
 'Costos':['Obra','Fecha_corte','Programado_MM_CLP','Real_MM_CLP','Pendiente_MM_CLP'],
 'Forecast':['Obra','Fecha_corte','Fin_proyectado'],
 'Fotografias':['ID','Obra','Fecha','Descripcion','Archivo','Tipo']}
def load_master(file):
 frames=pd.read_excel(file,sheet_name=None,engine='openpyxl');d={}
 for name,columns in SCHEMA.items():
  if name not in frames or not set(columns)<=set(frames[name].columns):raise ValueError(f'Hoja {name}: faltan columnas. Mantenga la estructura del maestro de ejemplo.')
  frame=frames[name].dropna(how='all')
  d[name]=[{k:('' if pd.isna(v) else v.isoformat()[:10] if isinstance(v,(date,datetime)) else v.item() if hasattr(v,'item') else v) for k,v in row.items() if k in columns} for row in frame.to_dict('records')]
 def dt(value):
  try:return date.fromisoformat(str(value))
  except Exception:raise ValueError(f'Fecha inválida: {value}. Use una fecha Excel o AAAA-MM-DD.')
 def number(value,label,minimum=None,maximum=None):
  if isinstance(value,bool) or not isinstance(value,(int,float)) or not math.isfinite(value) or minimum is not None and value<minimum or maximum is not None and value>maximum:raise ValueError('Valor numérico inválido: '+label)
 ids=[p['ID'] for p in d['Obras']]
 if not ids or len(set(ids))!=len(ids) or any(not x for x in ids):raise ValueError('IDs de obra vacíos o duplicados.')
 for p in d['Obras']:
  if not all(p[x] for x in ['Nombre','Tipo','Region','Comuna']):raise ValueError('Complete identificación de '+p['ID'])
  if dt(p['Inicio_programado'])>dt(p['Fin_programado']):raise ValueError('Fechas invertidas: '+p['ID'])
  for k in ['Inicio_real','Fin_real']:
   if p[k]:dt(p[k])
  if p['Fin_real'] and (not p['Inicio_real'] or dt(p['Fin_real'])<dt(p['Inicio_real'])):raise ValueError('Fechas reales inconsistentes: '+p['ID'])
  number(p['Latitud'],'Latitud',-90,90);number(p['Longitud'],'Longitud',-180,180)
  number(p['Monto_contractual_MM_CLP'],'Monto contractual',0);number(p['Presupuesto_MM_CLP'],'Presupuesto',.000001)
 for name in ['Programa','Avance_fisico','Costos','Forecast','Fotografias']:
  keys=[]
  for row in d[name]:
   if row['Obra'] not in ids:raise ValueError('Obra inexistente en '+name+': '+str(row['Obra']))
   key=row.get('ID') if 'ID' in SCHEMA[name] else (row['Obra'],row['Fecha_corte']);keys.append(key)
   if name=='Programa':
    if dt(row['Inicio'])>dt(row['Fin']):raise ValueError('Actividad con fechas invertidas: '+row['ID'])
   if name in ['Avance_fisico','Costos','Forecast']:dt(row['Fecha_corte'])
   if name=='Avance_fisico':
    for k in ['Programado','Real']:number(row[k],name+' '+k,0,1)
   if name=='Costos':
    for k in ['Programado_MM_CLP','Real_MM_CLP','Pendiente_MM_CLP']:number(row[k],name+' '+k,0)
   if name=='Forecast':dt(row['Fin_proyectado'])
   if name=='Fotografias':
    dt(row['Fecha']);path=Path(str(row['Archivo']))
    if path.is_absolute() or '..' in path.parts or path.suffix.lower() not in ['.svg','.png','.jpg','.jpeg','.webp']:raise ValueError('Ruta de imagen inválida: '+str(path))
  if len(keys)!=len(set(keys)) or any(not x for x in keys):raise ValueError('Registros duplicados o sin ID en '+name)
 keys={n:{(x['Obra'],x['Fecha_corte']) for x in d[n]} for n in ['Avance_fisico','Costos','Forecast']}
 if keys['Avance_fisico']!=keys['Costos'] or keys['Avance_fisico']!=keys['Forecast']:raise ValueError('Cada obra/corte necesita avance, costos y forecast con la misma fecha.')
 for id in ids:
  if not any(x['Obra']==id for x in d['Avance_fisico']):raise ValueError('Faltan cortes para '+id)
 d['config']={x['Parametro']:x['Valor'] for x in d['Configuracion']};dt(d['config'].get('Fecha_corte',''))
 d['cortes']=sorted({x['Fecha_corte'] for x in d['Avance_fisico']})
 return d
