"""Lectura validada del Excel. Sin datos de respaldo embebidos."""
from pathlib import Path
import math
import pandas as pd

def load_master(path):
    path=Path(path)
    if not path.is_file():raise ValueError('Falta maestro_control_obra.xlsx junto a app.py.')
    book=pd.read_excel(path,sheet_name=None,dtype={'ID':str})
    for sheet in ['Obra','Partidas','Control_semanal','Reprogramaciones']:
        if sheet not in book:raise ValueError(f'Falta la hoja {sheet}.')
    info=book['Obra']
    if info.Parametro.duplicated().any():raise ValueError('Parámetros duplicados en Obra.')
    m=dict(zip(info.Parametro,info.Valor))
    required=['Nombre','Direccion','Inicio_programado','Termino_programado','Semanas_totales','Semana_control','Monto_contractual_MM_CLP']
    for key in required:
        if key not in m or pd.isna(m[key]):raise ValueError(f'Complete {key} en Obra.')
    def date(value):
        d=pd.to_datetime(value,errors='coerce')
        if pd.isna(d):raise ValueError(f'Fecha inválida: {value}')
        return d.normalize()
    origin=date(m['Inicio_programado'])
    def offset(value):return int((date(value)-origin).days)
    def num(value,label):
        try:v=float(value)
        except (TypeError,ValueError):raise ValueError(f'Valor numérico inválido en {label}.')
        if not math.isfinite(v):raise ValueError(f'Valor no finito en {label}.')
        return v
    def integer(value,label):
        v=num(value,label)
        if int(v)!=v or v<1:raise ValueError(f'{label} debe ser un entero positivo.')
        return int(v)
    weeks=integer(m['Semanas_totales'],'Semanas_totales');control=integer(m['Semana_control'],'Semana_control')
    if control>weeks:raise ValueError('Semana de control fuera del programa.')
    if offset(m['Termino_programado'])<0:raise ValueError('Término anterior al inicio.')
    tasks=[]
    for row in book['Partidas'].dropna(subset=['ID']).to_dict('records'):
        qty=num(row['Cantidad_total'],'Cantidad_total');budget=num(row['Presupuesto_MM_CLP'],'Presupuesto_MM_CLP')
        if qty<=0 or budget<0:raise ValueError('Las cantidades deben ser positivas y los presupuestos no negativos.')
        a,b=offset(row['Inicio_original']),offset(row['Termino_original'])
        if a>b:raise ValueError('Fechas originales invertidas.')
        tasks.append(dict(id=str(row['ID']),family=str(row['Familia']),name=str(row['Nombre']),unit=str(row['Unidad']),qty=qty,budget=budget,start=a,end=b))
    ids={t['id'] for t in tasks}
    if not tasks or len(ids)!=len(tasks):raise ValueError('Partidas vacías o ID duplicado.')
    if sum(t['budget'] for t in tasks)<=0:raise ValueError('El presupuesto total debe ser positivo.')
    lookup={t['id']:t for t in tasks};records=[];keys=set()
    for r in book['Control_semanal'].dropna(subset=['ID']).to_dict('records'):
        tid=str(r['ID']);w=integer(r['Semana'],'Semana')
        if tid not in ids or w>weeks:raise ValueError('ID o semana inválido en Control_semanal.')
        if (tid,w) in keys:raise ValueError(f'Registro duplicado: {tid}, S{w}.')
        keys.add((tid,w));qp=num(r['Cantidad_programada_acum'],'Cantidad programada');qr=num(r['Cantidad_real_acum'],'Cantidad real');cost=num(r['Costo_real_acum_MM_CLP'],'Costo real');remaining=num(r['Costo_pendiente_MM_CLP'],'Costo pendiente')
        if not 0<=qp<=lookup[tid]['qty']+1e-8 or not 0<=qr<=lookup[tid]['qty']+1e-8 or min(cost,remaining)<0:raise ValueError(f'Cantidades o costos fuera de rango en {tid}, S{w}.')
        forecast=offset(r['Termino_forecast'])
        if qr<lookup[tid]['qty']-1e-8 and forecast<w*7:raise ValueError(f'El término forecast de {tid}, S{w}, debe ser posterior al corte.')
        records.append(dict(id=tid,week=w,qtyPlan=qp,qtyReal=qr,cost=cost,remaining=remaining,forecastEnd=forecast))
    # El programa semanal y el histórico deben tener todos los ID, sin silencios ni ceros ficticios.
    if keys!={(tid,w) for tid in ids for w in range(1,weeks+1)}:raise ValueError('Complete un registro por partida y semana en Control_semanal para todo el programa.')
    replans=[];seen=set()
    for r in book['Reprogramaciones'].dropna(subset=['ID']).to_dict('records'):
        tid=str(r['ID']);w=integer(r['Semana_vigencia'],'Semana_vigencia');a,b=offset(r['Nuevo_inicio']),offset(r['Nuevo_termino'])
        if tid not in ids or w>weeks or a>b or (tid,w) in seen:raise ValueError('Reprogramación inválida o duplicada.')
        seen.add((tid,w));replans.append(dict(id=tid,week=w,start=a,end=b))
    return dict(obra=dict(name=str(m['Nombre']),address=str(m['Direccion']),start=origin.strftime('%Y-%m-%d'),end=date(m['Termino_programado']).strftime('%Y-%m-%d'),weeks=weeks,control=control,contract=num(m['Monto_contractual_MM_CLP'],'Monto contractual')),tasks=tasks,records=records,replans=replans)
