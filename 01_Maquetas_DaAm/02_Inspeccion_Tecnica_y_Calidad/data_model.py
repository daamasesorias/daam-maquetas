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

REQUIRED.pop('Planos',None)
REQUIRED.update({'Materiales':['ID','Material','Proveedor','Lote','Recepcion','Guia','Certificado','Ubicacion','Elemento','Inspeccion'],'Ensayos':['ID','Material','Muestra','Tipo','Muestreo','Laboratorio','Resultado','Criterio','Estado','Informe','Hallazgo']})

def load_master(path):
    frames=pd.read_excel(path,sheet_name=None)
    result={}
    for name,cols in REQUIRED.items():
        if name in ('Materiales','Ensayos') and name not in frames:
            result[name]=[];continue
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
    for name in ['Documentos','Evidencias']:
        for r in result[name]:
            p=Path(r['Archivo'])
            if p.is_absolute() or '..' in p.parts:raise ValueError('Ruta de recurso inválida.')
    materials={m['ID']:m for m in result['Materiales']};documents={d['ID'] for d in result['Documentos']}
    for m in materials.values():
        if m['Ubicacion'] not in locs or m['Inspeccion'] not in ins:raise ValueError('Material con ubicación o inspección inexistente.')
        date.fromisoformat(m['Recepcion'])
        if any(m[k] and m[k] not in documents for k in ('Guia','Certificado')):raise ValueError('Documento de material inexistente.')
    for e in result['Ensayos']:
        if e['Material'] not in materials or e['Estado'] not in ('Cumple','No cumple','Pendiente'):raise ValueError('Ensayo con material o estado inválido.')
        date.fromisoformat(e['Muestreo'])
        if e['Informe'] and e['Informe'] not in documents:raise ValueError('Informe de ensayo inexistente.')
        if e['Estado']!='Pendiente' and not e['Resultado']:raise ValueError('Ensayo evaluado sin resultado.')
        if e['Hallazgo'] and not any(h['ID']==e['Hallazgo'] for h in result['Hallazgos']):raise ValueError('Hallazgo de ensayo inexistente.')
    return result


def connection(path):
    c=sqlite3.connect(path,timeout=15)
    c.execute('CREATE TABLE IF NOT EXISTS app_state(id INTEGER PRIMARY KEY CHECK(id=1), content TEXT NOT NULL)')
    c.execute('CREATE TABLE IF NOT EXISTS actions(id TEXT PRIMARY KEY)')
    return c


def empty_overlay():return {'ins':{},'answers':{},'halls':{},'comments':[],'files':{},'marks':{},'approvals':[]}


def merge(seed,overlay):
    d=copy.deepcopy(overlay.get('source') or seed)
    d.setdefault('Materiales',[]);d.setdefault('Ensayos',[])
    d['Documentos']+=overlay.get('documents',[])
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
        if role!='ITO' or not author:raise ValueError('Ingrese el nombre del responsable ITO.')
        kind=action.get('kind');now=datetime.now().astimezone().isoformat(timespec='seconds');today=now[:10]
        # La fecha de corte demo no limita la fecha real de nuevos registros.
        if kind=='import_excel':
            encoded=action.get('file','')
            if len(encoded)>21_000_000:raise ValueError('El Excel supera 15 MB.')
            raw=base64.b64decode(encoded.split(',',1)[1],validate=True)
            if len(raw)>15_000_000:raise ValueError('El Excel supera 15 MB.')
            imported=load_master(io.BytesIO(raw))
            for sheet in ('Documentos','Evidencias'):
                for item in imported[sheet]:
                    if not (Path(__file__).parent/'interfaz'/item['Archivo']).is_file():raise ValueError('Recurso no encontrado: '+item['Archivo'])
            o['source']=imported
            for key in ('ins','answers','halls'):o[key]={}
            o['comments']=[];o['approvals']=[]
            msg='Planilla validada y cargada. Datos de inspecciones y hallazgos actualizados.'
        elif kind=='attach_document':
            encoded=action.get('file','')
            if not isinstance(encoded,str) or len(encoded)>14_000_000:raise ValueError('Documento demasiado grande.')
            header,body=encoded.split(',',1);raw=base64.b64decode(body,validate=True)
            if len(raw)>10_000_000:raise ValueError('Máximo 10 MB.')
            if header=='data:application/pdf;base64':
                if not raw.startswith(b'%PDF-'):raise ValueError('PDF inválido.')
            else:
                image=Image.open(io.BytesIO(raw));image.verify()
                if image.format not in ('PNG','JPEG'):raise ValueError('Adjunte PDF, PNG o JPEG.')
            inspection=next((i for i in d['Inspecciones'] if i['ID']==action.get('inspection')),None)
            if not inspection:raise ValueError('Inspección no encontrada.')
            finding=action.get('finding','')
            if finding and not any(h['ID']==finding and h['Inspeccion']==inspection['ID'] for h in d['Hallazgos']):raise ValueError('Hallazgo e inspección no coinciden.')
            material=action.get('material','');test=action.get('test','')
            if material and not any(m['ID']==material and m['Inspeccion']==inspection['ID'] for m in d['Materiales']):raise ValueError('Material e inspección no coinciden.')
            if test and not any(e['ID']==test and e['Material']==material for e in d['Ensayos']):raise ValueError('Ensayo y material no coinciden.')
            uid='DOC-'+uuid.uuid4().hex[:8];o['files'][uid]=encoded
            o.setdefault('documents',[]).append({'ID':uid,'Nombre':clean_text(action.get('name'),150),'Categoria':action.get('category') if action.get('category') in ('Protocolo','Certificado','Acta','Otros','No conformidad','Observación','Respuesta','Cierre de hallazgo','Informe de ensayo','Guía de despacho') else 'Otros','Revision':'Registro ITO','Fecha':today,'Ubicacion':inspection['Ubicacion'],'Inspeccion':inspection['ID'],'Hallazgo':finding,'Material':action.get('material',''),'Ensayo':action.get('test',''),'Archivo':uid,'Indicacion':'Documento adjuntado por la ITO.'})
            msg='Documento adjuntado y vinculado a '+inspection['ID']+'.'
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
