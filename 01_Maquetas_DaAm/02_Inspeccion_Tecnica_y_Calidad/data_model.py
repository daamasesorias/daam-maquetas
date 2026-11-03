"""Fuente Excel de una obra y registros operativos locales en SQLite."""
import base64
import copy
import io
import json
import sqlite3
import uuid
from datetime import datetime, date
from pathlib import Path
from PIL import Image
import pandas as pd

REQUIRED={'Obra':['Parametro','Valor'],'Ubicaciones':['ID','Piso','Unidad','Nombre'],'Plantillas':['ID','Nombre','Familia','Contratista','Documento'],'Criterios':['ID','Plantilla','Orden','Texto'],'Inspecciones':['ID','Ubicacion','Plantilla','Programada','Ejecutada','Estado','Inspector','Revision'],'Respuestas':['Inspeccion','Criterio','Respuesta','Observacion'],'Hallazgos':['ID','Tipo','Inspeccion','Ubicacion','Descripcion','Responsable','Criticidad','Creado','Compromiso','Estado','Bloquea','X','Y','Foto_inicial','Foto_reparacion','Cierre'],'Comentarios':['ID','Hallazgo','Fecha','Autor','Rol','Texto'],'Documentos':['ID','Nombre','Categoria','Revision','Fecha','Ubicacion','Inspeccion','Hallazgo','Archivo','Indicacion'],'Evidencias':['ID','Titulo','Ubicacion','Inspeccion','Hallazgo','Archivo'],'Planos':['ID','Nombre','Piso','Especialidad','Revision','Archivo']}

def load_master(path):
    frames=pd.read_excel(path,sheet_name=None)
    result={}
    for name,cols in REQUIRED.items():
        if name not in frames or not set(cols)<=set(frames[name].columns):raise ValueError(f'Hoja {name}: columnas requeridas incompletas.')
        result[name]=[{k:('' if pd.isna(v) else v.isoformat()[:10] if isinstance(v,(date,datetime)) else v.item() if hasattr(v,'item') else v) for k,v in row.items()} for row in frames[name].to_dict('records')]
        if 'ID' in cols and len({r['ID'] for r in result[name]})!=len(result[name]):raise ValueError(f'IDs duplicados en {name}.')
    result['obra']={r['Parametro']:r['Valor'] for r in result['Obra']}
    for key in ['Nombre','Fecha_corte','Inicio','Termino']:
        if not result['obra'].get(key):raise ValueError(f'Falta {key} en Obra.')
    date.fromisoformat(result['obra']['Fecha_corte'])
    locs={r['ID'] for r in result['Ubicaciones']};tpls={r['ID'] for r in result['Plantillas']};ins={r['ID']:r for r in result['Inspecciones']};crit={r['ID']:r for r in result['Criterios']}
    for i in ins.values():
        if i['Ubicacion'] not in locs or i['Plantilla'] not in tpls or i['Estado'] not in ['Pendiente','Borrador','Aprobada','Rechazada']:raise ValueError(f"Inspección inválida: {i['ID']}")
        date.fromisoformat(i['Programada'])
    for r in result['Respuestas']:
        if r['Inspeccion'] not in ins or r['Criterio'] not in crit or crit[r['Criterio']]['Plantilla']!=ins[r['Inspeccion']]['Plantilla'] or r['Respuesta'] not in ['', 'Cumple','No cumple','No aplica']:raise ValueError('Respuesta inválida.')
    for h in result['Hallazgos']:
        if h['Inspeccion'] not in ins or h['Ubicacion'] not in locs or h['Estado'] not in ['Abierta','En revisión','Cerrada'] or not 0<=h['X']<=100 or not 0<=h['Y']<=100:raise ValueError(f"Hallazgo inválido: {h['ID']}")
        date.fromisoformat(h['Compromiso'])
    for name in ['Documentos','Evidencias','Planos']:
        for r in result[name]:
            p=Path(r['Archivo'])
            if p.is_absolute() or '..' in p.parts:raise ValueError('Ruta de recurso inválida.')
    return result


def connection(path):
    c=sqlite3.connect(path,timeout=15)
    c.execute('CREATE TABLE IF NOT EXISTS app_state(id INTEGER PRIMARY KEY CHECK(id=1), content TEXT NOT NULL)')
    c.execute('CREATE TABLE IF NOT EXISTS actions(id TEXT PRIMARY KEY)')
    return c


def empty_overlay():return {'ins':{},'answers':{},'halls':{},'comments':[],'files':{},'marks':{},'approvals':[]}


def merge(seed,overlay):
    d=copy.deepcopy(seed)
    for sheet,key in [('Inspecciones','ins'),('Hallazgos','halls')]:
        items={r['ID']:r for r in d[sheet]};items.update(overlay[key]);d[sheet]=list(items.values())
    for uid,rows in overlay['answers'].items():d['Respuestas']=[r for r in d['Respuestas'] if r['Inspeccion']!=uid]+rows
    d['Comentarios']+=overlay['comments'];d['files']=overlay['files'];d['marks']=overlay['marks'];d['approvals']=overlay['approvals']
    return d


def read_state(seed,db):
    with connection(db) as c:
        row=c.execute('SELECT content FROM app_state WHERE id=1').fetchone()
    return merge(seed,json.loads(row[0]) if row else empty_overlay())


def clean_text(value,maxlen=2000):return str(value or '').strip()[:maxlen]


def store_photo(value,overlay):
    if not value:return ''
    if not isinstance(value,str) or len(value)>8_000_000 or not value.startswith('data:image/'):raise ValueError('Adjunte una imagen PNG o JPEG de hasta 5 MB.')
    raw=base64.b64decode(value.split(',',1)[1],validate=True)
    if len(raw)>5_000_000:raise ValueError('La imagen supera 5 MB.')
    img=Image.open(io.BytesIO(raw));img.verify()
    if img.format not in ('PNG','JPEG','WEBP'):raise ValueError('Formato de imagen no admitido.')
    key='UP-'+uuid.uuid4().hex[:12];overlay['files'][key]=value
    return key


def apply_action(seed,db,action):
    if not isinstance(action,dict) or not action.get('id'):raise ValueError('Acción sin identificador.')
    with connection(db) as c:
        c.execute('BEGIN IMMEDIATE')
        if c.execute('SELECT 1 FROM actions WHERE id=?',(str(action['id']),)).fetchone():return 'Acción ya registrada.'
        row=c.execute('SELECT content FROM app_state WHERE id=1').fetchone();o=json.loads(row[0]) if row else empty_overlay();d=merge(seed,o)
        role=action.get('role');author=clean_text(action.get('author'),100)
        if role not in ('ITO','Contratista') or not author:raise ValueError('Seleccione rol y nombre del responsable.')
        kind=action.get('kind');now=datetime.now().astimezone().isoformat(timespec='seconds');today=now[:10]
        # La fecha de corte demo no limita la fecha real de nuevos registros.
        if kind in ('draft','submit'):
            if role!='ITO':raise ValueError('La inspección debe registrarla la ITO.')
            uid=action.get('inspection');i=next((r for r in d['Inspecciones'] if r['ID']==uid),None)
            if not i:raise ValueError('Inspección no encontrada.')
            if i['Estado'] in ('Aprobada','Rechazada'):raise ValueError('La inspección ya fue emitida. Cree una reinspección.')
            criteria=[r for r in d['Criterios'] if r['Plantilla']==i['Plantilla']];values=action.get('answers',{})
            rows=[]
            for item in criteria:
                v=values.get(item['ID'],{});answer=v.get('answer','')
                if answer not in ('','Cumple','No cumple','No aplica'):raise ValueError('Respuesta inválida.')
                if kind=='submit' and not answer:raise ValueError('Complete todos los criterios antes de emitir.')
                rows.append({'Inspeccion':uid,'Criterio':item['ID'],'Respuesta':answer,'Observacion':clean_text(v.get('note'))})
            if kind=='submit' and not any(r['Respuesta'] in ('Cumple','No cumple') for r in rows):raise ValueError('Debe existir al menos un criterio aplicable para emitir.')
            negative=any(r['Respuesta']=='No cumple' for r in rows)
            if kind=='submit' and negative and (not clean_text(action.get('description')) or not action.get('photo')):raise ValueError('Un incumplimiento requiere descripción y fotografía.')
            photo=store_photo(action.get('photo'),o)
            updated={**i,'Estado':'Borrador' if kind=='draft' else 'Rechazada' if negative else 'Aprobada','Inspector':author,'Ejecutada':'' if kind=='draft' else today,'Foto':photo or i.get('Foto','')}
            o['ins'][uid]=updated;o['answers'][uid]=rows
            if kind=='submit' and negative:
                hid='H-'+uuid.uuid4().hex[:6].upper();tpl=next(t for t in d['Plantillas'] if t['ID']==i['Plantilla']);deadline=clean_text(action.get('deadline'),10);date.fromisoformat(deadline)
                if deadline<today:raise ValueError('La fecha compromiso de un hallazgo nuevo no puede ser anterior a hoy.')
                o['halls'][hid]={'ID':hid,'Tipo':'No conformidad','Inspeccion':uid,'Ubicacion':i['Ubicacion'],'Descripcion':clean_text(action.get('description')),'Responsable':tpl['Contratista'],'Criticidad':action.get('criticality','Media') if action.get('criticality') in ('Alta','Media','Baja') else 'Media','Creado':today,'Compromiso':deadline,'Estado':'Abierta','Bloquea':bool(action.get('blocks')),'X':50,'Y':50,'Foto_inicial':photo,'Foto_reparacion':'','Cierre':''}
                o['comments'].append({'ID':'C-'+uuid.uuid4().hex[:8],'Hallazgo':hid,'Fecha':now,'Autor':author,'Rol':role,'Texto':'Hallazgo creado desde '+uid+': '+clean_text(action.get('description'))})
            msg='Borrador guardado.' if kind=='draft' else 'Inspección emitida'+(' y no conformidad creada.' if negative else '.')
        elif kind=='reinspect':
            if role!='ITO':raise ValueError('Solo ITO puede abrir una reinspección.')
            old=next((i for i in d['Inspecciones'] if i['ID']==action.get('inspection')),None)
            if not old:raise ValueError('Inspección no encontrada.')
            if old['Estado'] not in ('Aprobada','Rechazada'):raise ValueError('La inspección aún no ha sido emitida.')
            uid='I-'+uuid.uuid4().hex[:6].upper();o['ins'][uid]={**old,'ID':uid,'Estado':'Pendiente','Programada':today,'Ejecutada':'','Inspector':author,'Revision':old['Revision']+1,'Origen':old['ID'],'Foto':''};msg='Reinspección creada: '+uid
        elif kind in ('comment','repair','close','reopen'):
            h=next((h for h in d['Hallazgos'] if h['ID']==action.get('finding')),None)
            if not h:raise ValueError('Hallazgo no encontrado.')
            text=clean_text(action.get('text'));new=copy.deepcopy(h)
            if not text:raise ValueError('Ingrese un comentario de trazabilidad.')
            if kind=='repair':
                if role!='Contratista' or h['Estado']!='Abierta':raise ValueError('La reparación debe solicitarla el contratista sobre un hallazgo abierto.')
                photo=store_photo(action.get('photo'),o)
                if not photo:raise ValueError('Adjunte evidencia de reparación.')
                new.update(Estado='En revisión',Foto_reparacion=photo)
            if kind=='close':
                if role!='ITO' or h['Estado']!='En revisión' or not h['Foto_reparacion']:raise ValueError('Solo ITO puede cerrar un hallazgo en revisión con evidencia.')
                new.update(Estado='Cerrada',Cierre=today)
            if kind=='reopen':
                if role!='ITO' or h['Estado']=='Abierta':raise ValueError('Solo ITO puede devolver o reabrir un hallazgo.')
                new.update(Estado='Abierta',Cierre='')
            o['halls'][h['ID']]=new;o['comments'].append({'ID':'C-'+uuid.uuid4().hex[:8],'Hallazgo':h['ID'],'Fecha':now,'Autor':author,'Rol':role,'Texto':text,'Accion':kind});msg='Registro actualizado.'
        elif kind=='mark':
            if role!='ITO':raise ValueError('Solo ITO puede guardar anotaciones.')
            plan=next((p for p in d['Planos'] if p['ID']==action.get('plan')),None)
            if not plan:raise ValueError('Plano no encontrado.')
            marks=action.get('marks',[])
            if not isinstance(marks,list) or len(marks)>100:raise ValueError('Cantidad de marcas inválida.')
            for m in marks:
                if m.get('kind') not in ('line','circle','arrow'):raise ValueError('Marca inválida.')
                if any(not isinstance(m.get(k),(int,float)) or not 0<=m[k]<=100 for k in ('x1','y1','x2','y2')):raise ValueError('Coordenadas inválidas.')
            o['marks'][plan['ID']]={'revision':plan['Revision'],'items':marks,'author':author,'date':now};msg='Anotaciones guardadas para '+plan['ID']+' '+plan['Revision']+'.'
        elif kind=='approve':
            if role!='ITO':raise ValueError('La validación debe realizarla la ITO.')
            uid=action.get('inspection');i=next((i for i in d['Inspecciones'] if i['ID']==uid),None)
            if not i or i['Estado']!='Aprobada':raise ValueError('Seleccione un protocolo aprobado.')
            if any(h['Inspeccion']==uid and h['Estado']!='Cerrada' for h in d['Hallazgos']):raise ValueError('El protocolo tiene hallazgos pendientes.')
            if any(a['Inspeccion']==uid for a in o['approvals']):raise ValueError('El protocolo ya tiene validación registrada.')
            if not action.get('accepted'):raise ValueError('Confirme la validación del acta.')
            o['approvals'].append({'Inspeccion':uid,'Autor':author,'Rol':role,'Fecha':now,'Declaracion':'Validación registrada en plataforma de demostración'});msg='Validación registrada. No corresponde a firma electrónica avanzada.'
        else:raise ValueError('Acción no admitida.')
        c.execute('INSERT INTO app_state(id,content) VALUES(1,?) ON CONFLICT(id) DO UPDATE SET content=excluded.content',(json.dumps(o,ensure_ascii=False),));c.execute('INSERT INTO actions(id) VALUES(?)',(str(action['id']),))
    return msg


def metrics(data,cut):
    due=[i for i in data['Inspecciones'] if i['Programada']<=cut]
    done=[i for i in due if i['Estado'] in ('Aprobada','Rechazada') and i['Ejecutada'] and i['Ejecutada']<=cut];ids={i['ID'] for i in done}
    rows=[r for r in data['Respuestas'] if r['Inspeccion'] in ids and r['Respuesta'] in ('Cumple','No cumple')]
    halls=[h for h in data['Hallazgos'] if h['Creado']<=cut];ncr=[h for h in halls if h['Tipo']=='No conformidad']
    return {'criteria':len(rows),'pass':sum(r['Respuesta']=='Cumple' for r in rows),'quality':sum(r['Respuesta']=='Cumple' for r in rows)/len(rows) if rows else None,'scheduled':len(due),'done':len(done),'approved':sum(i['Estado']=='Aprobada' for i in done),'coverage':len(done)/len(due) if due else None,'approval':sum(i['Estado']=='Aprobada' for i in done)/len(done) if done else None,'open':sum(h['Estado']=='Abierta' for h in ncr),'review':sum(h['Estado']=='En revisión' for h in ncr),'closed':sum(h['Estado']=='Cerrada' for h in ncr)}
