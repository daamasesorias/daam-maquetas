from pathlib import Path
from datetime import datetime,date
import json,sqlite3,hashlib,base64,io,uuid,copy,zipfile
import pandas as pd
from PIL import Image
SCHEMA=json.loads((Path(__file__).parent/'schema.json').read_text())
ENTITY={'Partida':'Partidas','Protocolo':'Protocolos','NoConformidad':'NoConformidades','Inspeccion':'Inspecciones','Hallazgo':'Hallazgos','Material':'Materiales','Ensayo':'Ensayos'}
def validate(d,external_docs=()):
 for name,cols in SCHEMA.items():
  if name not in d:raise ValueError('Falta hoja '+name)
  if any(not set(cols)<=set(row) for row in d[name]):raise ValueError('Columnas incompletas en '+name)
  if 'ID' in cols and (any(not row['ID'] for row in d[name]) or len({row['ID'] for row in d[name]})!=len(d[name])):raise ValueError('IDs vacíos o duplicados en '+name)
 maps={k:{r['ID']:r for r in d[v]} for k,v in ENTITY.items()};docs={r['ID']:r for r in d['Documentos']};evid={r['ID'] for r in d['Evidencias']}
 def ref(kind,id):
  if id not in maps[kind]:raise ValueError(f'Referencia inexistente: {kind} {id}')
 def document(id):
  if id and id not in docs and id not in external_docs:raise ValueError('Documento inexistente: '+id)
 for p in d['Partidas']:
  if p['EstadoDeclarado'] not in ('Validada','Pendiente'):raise ValueError('Estado declarado de partida inválido.')
  document(p['DocumentoValidacion'])
  if p['FechaValidacion']:date.fromisoformat(p['FechaValidacion'])
 for p in d['Protocolos']:
  ref('Partida',p['Partida']);document(p['Documento']);date.fromisoformat(p['Fecha'])
  if p['Resultado'] not in ('Conforme','No conforme','Pendiente'):raise ValueError('Resultado de protocolo inválido.')
 for i in d['Inspecciones']:document(i['Documento']);date.fromisoformat(i['Fecha'])
 for link in d['AlcancesInspeccion']:
  ref('Inspeccion',link['Inspeccion']);ref('Partida',link['Partida'])
 for sheet,origin in [('NoConformidades','Protocolo'),('Hallazgos','Inspeccion')]:
  for h in d[sheet]:
   ref(origin,h[origin])
   if sheet=='Hallazgos':
    ref('Partida',h['Partida'])
    if not any(x['Inspeccion']==h['Inspeccion'] and x['Partida']==h['Partida'] for x in d['AlcancesInspeccion']):raise ValueError('Hallazgo fuera del alcance de la inspección.')
   if h['Estado'] not in ('Abierta','En revisión','Cerrada'):raise ValueError('Estado de observación inválido.')
   for k in ('Fecha','Compromiso'):date.fromisoformat(h[k])
   for k in ('EvidenciaInicial','EvidenciaReparacion'):
    if h[k] and h[k] not in evid:raise ValueError('Evidencia inexistente: '+h[k])
   document(h['DocumentoCierre'])
 for m in d['Materiales']:date.fromisoformat(m['Recepcion'])
 for u in d['UsosMaterial']:
  ref('Material',u['Material']);ref('Partida',u['Partida']);date.fromisoformat(u['Fecha'])
  if not isinstance(u['Cantidad'],(int,float)) or u['Cantidad']<0:raise ValueError('Cantidad de uso inválida.')
 for e in d['Ensayos']:
  ref('Material',e['Material']);ref('Partida',e['Partida']);document(e['Informe']);date.fromisoformat(e['Muestreo'])
  if not any(u['Material']==e['Material'] and u['Partida']==e['Partida'] for u in d['UsosMaterial']):raise ValueError('Ensayo sin uso de material en la partida indicada.')
  if e['Estado'] not in ('Cumple','No cumple','Pendiente') or e['Estado']!='Pendiente' and not e['Resultado']:raise ValueError('Resultado de ensayo incompleto.')
 for v in d['Vinculos']:
  if v['Entidad'] not in ENTITY:raise ValueError('Tipo de vínculo inválido.')
  ref(v['Entidad'],v['Registro']);document(v['Documento'])
 for row in d['Documentos']+d['Evidencias']:
  p=Path(row['Archivo'])
  if p.is_absolute() or '..' in p.parts:raise ValueError('Ruta de archivo inválida.')
 date.fromisoformat(dict((r['Parametro'],r['Valor']) for r in d['Obra']).get('Fecha_corte',''))
 if not dict((r['Parametro'],r['Valor']) for r in d['Obra']).get('Nombre'):raise ValueError('Falta nombre de obra.')
 return d

def load_master(file,external_docs=()):
 frames=pd.read_excel(file,sheet_name=None);d={}
 for name,cols in SCHEMA.items():
  if name not in frames or not set(cols)<=set(frames[name].columns):raise ValueError('Hoja '+name+': estructura incompleta. Use el maestro V7.')
  d[name]=[{k:('' if pd.isna(v) else v.isoformat()[:10] if isinstance(v,(datetime,date)) else v.item() if hasattr(v,'item') else v) for k,v in row.items()} for row in frames[name].to_dict('records')]
 return validate(d,external_docs)

def connect(db):
 c=sqlite3.connect(db,timeout=20);c.execute('CREATE TABLE IF NOT EXISTS source_versions(id INTEGER PRIMARY KEY,fecha TEXT,autor TEXT,nombre TEXT,sha256 TEXT,contenido TEXT)');c.execute('CREATE TABLE IF NOT EXISTS attachments(id TEXT PRIMARY KEY,nombre TEXT,tipo TEXT,entidad TEXT,registro TEXT,revision TEXT,fecha TEXT,autor TEXT,mime TEXT,archivo BLOB,sha256 TEXT)');c.execute('CREATE TABLE IF NOT EXISTS actions(id TEXT PRIMARY KEY)');return c

def read_state(seed,db):
 with connect(db) as c:
  row=c.execute('SELECT contenido FROM source_versions ORDER BY id DESC LIMIT 1').fetchone();d=json.loads(row[0]) if row else copy.deepcopy(seed)
  d['Adjuntos']=[dict(ID=r[0],Nombre=r[1],Tipo=r[2],Entidad=r[3],Registro=r[4],Revision=r[5],Fecha=r[6],Autor=r[7],Mime=r[8],Hash=r[9]) for r in c.execute('SELECT id,nombre,tipo,entidad,registro,revision,fecha,autor,mime,sha256 FROM attachments ORDER BY fecha DESC')]
  d['Cargas']=[dict(ID=r[0],Fecha=r[1],Autor=r[2],Archivo=r[3],Hash=r[4]) for r in c.execute('SELECT id,fecha,autor,nombre,sha256 FROM source_versions ORDER BY id DESC')]
 d['obra']=dict((r['Parametro'],r['Valor']) for r in d['Obra']);d['Dossiers']=[dossier(d,p['ID']) for p in d['Partidas']];return d

def related(d,pid):
 protocols={p['ID'] for p in d['Protocolos'] if p['Partida']==pid};ncs={h['ID'] for h in d['NoConformidades'] if h['Protocolo'] in protocols};hs={h['ID'] for h in d['Hallazgos'] if h['Partida']==pid};ins={a['Inspeccion'] for a in d['AlcancesInspeccion'] if a['Partida']==pid};mats={u['Material'] for u in d['UsosMaterial'] if u['Partida']==pid};tests={e['ID'] for e in d['Ensayos'] if e['Partida']==pid}
 return {'Partida':{pid},'Protocolo':protocols,'NoConformidad':ncs,'Inspeccion':ins,'Hallazgo':hs,'Material':mats,'Ensayo':tests}

def dossier(d,pid):
 p=next(p for p in d['Partidas'] if p['ID']==pid);rel=related(d,pid);docids={v['Documento'] for v in d['Vinculos'] if v['Registro'] in rel.get(v['Entidad'],set())};docs=[x for x in d['Documentos'] if x['ID'] in docids];attached=[a for a in d.get('Adjuntos',[]) if a['Registro'] in rel.get(a['Entidad'],set())];types={x['Tipo'] for x in docs+attached};missing=[];blocking=[]
 for typ in p['TiposRequeridos'].split('|'):
  if typ and typ not in types:missing.append('Falta respaldo: '+typ)
 protos=sorted([x for x in d['Protocolos'] if x['Partida']==pid],key=lambda x:(x['Fecha'],x['ID']))
 if not protos or protos[-1]['Resultado']=='Pendiente':missing.append('Protocolo pendiente de evaluación')
 elif protos[-1]['Resultado']=='No conforme':blocking.append('Último protocolo no conforme')
 for sheet,entity in [('NoConformidades','NoConformidad'),('Hallazgos','Hallazgo')]:
  for h in d[sheet]:
   if h['ID'] in rel[entity]:
    if h['Estado']!='Cerrada':blocking.append(h['ID']+': '+h['Estado'])
    else:
     closeids={v['Documento'] for v in d['Vinculos'] if v['Entidad']==entity and v['Registro']==h['ID']}
     if not any(x['ID']==h['DocumentoCierre'] and x['Tipo']=='Cierre' and x['ID'] in closeids for x in docs) and not any(a['ID']==h['DocumentoCierre'] and a['Tipo']=='Cierre' and a['Entidad']==entity and a['Registro']==h['ID'] for a in attached):missing.append('Falta documento de cierre vinculado: '+h['ID'])
 tests=[e for e in d['Ensayos'] if e['Partida']==pid]
 if p['RequiereEnsayo'] and not tests:missing.append('Sin ensayo requerido')
 for e in tests:
  if e['Estado']=='No cumple':blocking.append(e['ID']+': ensayo no cumple')
  elif e['Estado']=='Pendiente':missing.append(e['ID']+': ensayo pendiente')
  if not e['Informe']:missing.append(e['ID']+': informe de ensayo faltante')
 for mid in rel['Material']:
  materialdocs={v['Documento'] for v in d['Vinculos'] if v['Entidad']=='Material' and v['Registro']==mid};hascert=any(x['ID'] in materialdocs and x['Tipo']=='Certificado' for x in docs) or any(a['Entidad']=='Material' and a['Registro']==mid and a['Tipo']=='Certificado' for a in attached)
  if not hascert:missing.append(mid+': certificado faltante')
 if p['EstadoDeclarado']!='Validada':missing.append('Validación profesional pendiente')
 if not any(x['ID']==p['DocumentoValidacion'] and x['Tipo']=='Acta de validación' for x in docs+attached):missing.append('Acta de validación no vinculada al expediente')
 if not p['Validador'] or not p['FechaValidacion'] or not p['DocumentoValidacion']:missing.append('Acta, fecha o responsable de validación faltante')
 status='Con incumplimientos' if blocking else 'Pendiente de validación' if missing else 'Validada'
 return dict(Partida=pid,Estado=status,Faltantes=list(dict.fromkeys(missing)),Incumplimientos=blocking,Documentos=[x['ID'] for x in docs],Adjuntos=[a['ID'] for a in attached])

def apply_action(seed,db,a):
 if not a.get('id'):raise ValueError('Acción sin ID.')
 with connect(db) as c:
  c.execute('BEGIN IMMEDIATE')
  if c.execute('SELECT 1 FROM actions WHERE id=?',(a['id'],)).fetchone():return 'Acción ya procesada.'
  row=c.execute('SELECT contenido FROM source_versions ORDER BY id DESC LIMIT 1').fetchone();d=json.loads(row[0]) if row else seed
  author=str(a.get('author','ITO')).strip()[:100] or 'ITO';now=datetime.now().astimezone().isoformat(timespec='seconds');kind=a.get('kind')
  if kind=='import_excel':
   encoded=a.get('file','')
   if len(encoded)>22_000_000:raise ValueError('Excel de máximo 15 MB.')
   raw=base64.b64decode(encoded.split(',',1)[1],validate=True)
   if len(raw)>15_000_000:raise ValueError('Excel de máximo 15 MB.')
   new=load_master(io.BytesIO(raw),{row[0] for row in c.execute('SELECT id FROM attachments')})
   for ent,key in c.execute('SELECT entidad,registro FROM attachments'):
    if not any(x['ID']==key for x in new[ENTITY[ent]]):raise ValueError('La carga dejaría adjuntos sin vínculo: '+ent+' '+key+'. Conserve el ID en el consolidado.')
   for x in new['Documentos']+new['Evidencias']:
    if not (Path(__file__).parent/'interfaz'/x['Archivo']).is_file():raise ValueError('Archivo referenciado no encontrado: '+x['Archivo'])
   c.execute('INSERT INTO source_versions(fecha,autor,nombre,sha256,contenido) VALUES(?,?,?,?,?)',(now,author,str(a.get('name','Consolidado.xlsx'))[:200],hashlib.sha256(raw).hexdigest(),json.dumps(new,ensure_ascii=False)));msg='Consolidado cargado. Se conservó la versión anterior y sus adjuntos.'
  elif kind=='attach_document':
   ent=a.get('entity');key=a.get('record')
   if ent not in ENTITY or not any(x['ID']==key for x in d[ENTITY[ent]]):raise ValueError('Seleccione un registro válido para vincular el documento.')
   value=a.get('file','')
   if len(value)>14_000_000:raise ValueError('Documento de máximo 10 MB.')
   header,encoded=value.split(',',1);raw=base64.b64decode(encoded,validate=True)
   if len(raw)>10_000_000:raise ValueError('Documento de máximo 10 MB.')
   mime=header[5:].split(';')[0]
   if mime=='application/pdf':
    if not raw.startswith(b'%PDF-'):raise ValueError('PDF inválido.')
   elif mime in ('application/vnd.openxmlformats-officedocument.spreadsheetml.sheet','application/octet-stream'):
    with zipfile.ZipFile(io.BytesIO(raw)) as z:
     if 'xl/workbook.xml' not in z.namelist():raise ValueError('Excel inválido.')
    mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
   elif mime in ('image/png','image/jpeg'):
    im=Image.open(io.BytesIO(raw));im.verify()
    if im.format not in ('PNG','JPEG'):raise ValueError('Imagen inválida.')
   else:raise ValueError('Formatos admitidos: PDF, XLSX, PNG y JPEG.')
   name=str(a.get('name','')).strip()[:200];rev=str(a.get('revision','')).strip()[:30];typ=str(a.get('docType','')).strip()[:80]
   if not name or not rev or typ not in ('EETT','Plano','Protocolo de calidad','Planilla de inspección','No conformidad','Hallazgo','Respuesta','Cierre','Certificado','Guía de despacho','Informe de ensayo','Acta de validación','Otros'):raise ValueError('Complete nombre, tipo y revisión del documento.')
   c.execute('INSERT INTO attachments VALUES(?,?,?,?,?,?,?,?,?,?,?)',('AD-'+uuid.uuid4().hex[:10],name,typ,ent,key,rev,now,author,mime,raw,hashlib.sha256(raw).hexdigest()));msg='Documento cargado con revisión y vínculo. No modifica resultados ni validaciones profesionales.'
  else:raise ValueError('Acción no admitida. Los registros técnicos se elaboran externamente.')
  c.execute('INSERT INTO actions VALUES(?)',(a['id'],))
 return msg

def download_attachment(db,id):
 with connect(db) as c:row=c.execute('SELECT nombre,mime,archivo FROM attachments WHERE id=?',(id,)).fetchone()
 if not row:raise ValueError('Adjunto no encontrado.')
 return row
