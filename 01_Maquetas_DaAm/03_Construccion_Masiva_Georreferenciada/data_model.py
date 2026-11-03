"""Lectura estricta del Excel: no genera ni reemplaza datos de obra."""
from pathlib import Path
from datetime import datetime, date
import math
import pandas as pd


def load_master(path):
    sheets = pd.read_excel(path, sheet_name=None)
    required = {
        'Obra': ['Parametro', 'Valor'],
        'Tipologias': ['ID', 'Nombre', 'Pisos', 'Superficie_m2', 'Dormitorios', 'Banos', 'Plano', 'Render'],
        'Viviendas': ['ID', 'Sector', 'Etapa', 'Tipologia', 'Latitud', 'Longitud', 'Inicio_real', 'Fin_real'],
        'Programa': ['Vivienda', 'Partida', 'Nombre', 'Peso', 'Presupuesto_MM_CLP', 'Inicio_base', 'Fin_base'],
        'Control_semanal': ['Semana', 'Vivienda'] + [f'P{i:02d}' for i in range(1, 10)] + ['Costo_real_MM_CLP', 'Costo_pendiente_MM_CLP', 'Fin_forecast'],
        'Reprogramaciones': ['Vivienda', 'Partida', 'Semana_vigencia', 'Nuevo_inicio', 'Nuevo_fin'],
    }
    for name, cols in required.items():
        if name not in sheets or not set(cols) <= set(sheets[name].columns):
            raise ValueError(f'Hoja {name}: faltan columnas requeridas {cols}.')
    def rows(name):
        result = []
        for record in sheets[name].to_dict('records'):
            result.append({k: (None if pd.isna(v) else v.isoformat()[:10] if isinstance(v, (datetime, date)) else v.item() if hasattr(v, 'item') else v) for k, v in record.items()})
        return result
    data = {name: rows(name) for name in required}
    info = dict(zip(sheets['Obra'].Parametro, sheets['Obra'].Valor))
    for key in ['Nombre', 'Direccion', 'Inicio_programado', 'Fin_programado', 'Monto_contractual_MM_CLP', 'Semana_control', 'Semanas_totales']:
        if key not in info or pd.isna(info[key]):
            raise ValueError(f'Obra: falta {key}.')
    data['obra'] = {k: (v.isoformat()[:10] if isinstance(v, (datetime, date)) else v) for k,v in info.items()}
    units = data['Viviendas']; ids = {x['ID'] for x in units}
    types = {t['ID'] for t in data['Tipologias']}
    if len(ids) != len(units) or not units:
        raise ValueError('Viviendas: identificadores vacíos o duplicados.')
    for u in units:
        if u['Tipologia'] not in types or not -90 <= u['Latitud'] <= 90 or not -180 <= u['Longitud'] <= 180:
            raise ValueError(f"Vivienda {u['ID']}: tipología o coordenadas inválidas.")
        if u['Fin_real'] and (not u['Inicio_real'] or u['Fin_real'] < u['Inicio_real']):
            raise ValueError(f"Vivienda {u['ID']}: fechas reales inválidas.")
    keys=set()
    for p in data['Programa']:
        key=(p['Vivienda'],p['Partida'])
        if key in keys or p['Vivienda'] not in ids or not 0 < p['Peso'] <= 1 or p['Presupuesto_MM_CLP'] <= 0 or p['Fin_base'] < p['Inicio_base']:
            raise ValueError(f'Programa: fila inválida o duplicada {key}.')
        keys.add(key)
    for u in ids:
        tasks=[p for p in data['Programa'] if p['Vivienda']==u]
        if {p['Partida'] for p in tasks} != {f'P{i:02d}' for i in range(1,10)} or not math.isclose(sum(p['Peso'] for p in tasks),1,abs_tol=1e-8):
            raise ValueError(f'{u}: deben existir nueve partidas, con ponderaciones que sumen 100 %.')
    controls=set(); previous={}
    for c in sorted(data['Control_semanal'],key=lambda c:(c['Semana'],c['Vivienda'])):
        key=(c['Semana'],c['Vivienda'])
        if key in controls or c['Vivienda'] not in ids or int(c['Semana']) != c['Semana'] or not 1 <= c['Semana'] <= info['Semanas_totales']:
            raise ValueError(f'Control semanal: clave inválida {key}.')
        controls.add(key)
        values=[c[f'P{i:02d}'] for i in range(1,10)]
        if any(v is None or not math.isfinite(v) or not 0 <= v <= 1 for v in values) or c['Costo_real_MM_CLP'] < 0 or c['Costo_pendiente_MM_CLP'] < 0 or not c['Fin_forecast']:
            raise ValueError(f'Control semanal: avances/costos inválidos en {key}.')
        prev=previous.get(c['Vivienda'])
        if prev and (any(a < b-1e-8 for a,b in zip(values,prev[0])) or c['Costo_real_MM_CLP'] < prev[1]-1e-8):
            raise ValueError(f'Control semanal: acumulados decrecientes en {key}.')
        previous[c['Vivienda']] = (values,c['Costo_real_MM_CLP'])
        cut=pd.Timestamp(info['Inicio_programado'])+pd.Timedelta(days=int(c['Semana'])*7-1)
        complete=all(v>=1-1e-8 for v in values)
        unit=next(u for u in units if u['ID']==c['Vivienda'])
        ended=bool(unit['Fin_real'] and pd.Timestamp(unit['Fin_real'])<=cut)
        if complete != ended or complete and c['Costo_pendiente_MM_CLP']>1e-8:
            raise ValueError(f'Control semanal: término/avance/costo pendiente incoherentes en {key}.')
    weeks=sorted({c['Semana'] for c in data['Control_semanal']})
    if info['Semana_control'] not in weeks or any((w,u) not in controls for w in weeks for u in ids):
        raise ValueError('Cada semana registrada debe contener un corte de todas las viviendas.')
    for r in data['Reprogramaciones']:
        if (r['Vivienda'],r['Partida']) not in keys or r['Nuevo_fin'] < r['Nuevo_inicio'] or r['Semana_vigencia'] not in weeks:
            raise ValueError('Reprogramación inválida.')
    data['weeks']=weeks
    return data
