import io
from pathlib import Path
import pandas as pd
import reportlab
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import SimpleDocTemplate,Paragraph,Spacer,Table,TableStyle,PageBreak
from xml.sax.saxutils import escape
from data_model import SCHEMA,related,timeline
fontdir=Path(reportlab.__file__).parent/'fonts'
for name,file in [('DaAm','Vera.ttf'),('DaAmB','VeraBd.ttf')]:pdfmetrics.registerFont(TTFont(name,str(fontdir/file)))

def report_part(d,p):
 rel=related(d,p['ID']);protos=sorted([x for x in d['Protocolos'] if x['ID'] in rel['Protocolo']],key=lambda x:(x['Fecha'],x['ID']))
 ncs=[x for x in d['NoConformidades'] if x['ID'] in rel['NoConformidad']];hall=[x for x in d['Hallazgos'] if x['ID'] in rel['Hallazgo']];tests=[x for x in d['Ensayos'] if x['ID'] in rel['Ensayo']]
 docs=timeline(d,p['ID']);mats=[]
 for m in d['Materiales']:
  if m['ID'] not in rel['Material']:continue
  ids={v['Documento'] for v in d['Vinculos'] if v['Entidad']=='Material' and v['Registro']==m['ID']}
  cert=[x['ID'] for x in docs if x['Tipo']=='Certificado' and (x['ID'] in ids or x.get('Entidad')=='Material' and x.get('Registro')==m['ID'])]
  mats.append(dict(m,Certificados=', '.join(cert) or 'Pendiente'))
 return dict(protocolos=protos,ncs=ncs,hallazgos=hall,ensayos=tests,materiales=mats,documentos=docs,estado=protos[-1]['Resultado'] if protos else 'Sin protocolo')

def build_excel(d):
 out=io.BytesIO();summary=[];chronology=[];materials=[]
 for p in d['Partidas']:
  r=report_part(d,p);x=next(x for x in d['Dossiers'] if x['Partida']==p['ID'])
  summary.append(dict(Partida=p['ID'],Nombre=p['Nombre'],Ubicacion=p['Ubicacion'],Estado_protocolo=r['estado'],Ultimo_protocolo=r['protocolos'][-1]['ID'] if r['protocolos'] else '',NC_abiertas=sum(n['Estado']!='Cerrada' for n in r['ncs']),NC_resueltas=sum(n['Estado']=='Cerrada' for n in r['ncs']),Hallazgos_pendientes=sum(n['Estado']!='Cerrada' for n in r['hallazgos']),Hallazgos_cerrados=sum(n['Estado']=='Cerrada' for n in r['hallazgos']),Lotes_con_certificado=sum(m['Certificados']!='Pendiente' for m in r['materiales']),Lotes_sin_certificado=sum(m['Certificados']=='Pendiente' for m in r['materiales']),Ensayos_cumplen=sum(e['Estado']=='Cumple' for e in r['ensayos']),Ensayos_no_cumplen=sum(e['Estado']=='No cumple' for e in r['ensayos']),Ensayos_pendientes=sum(e['Estado']=='Pendiente' for e in r['ensayos']),Estado_expediente=x['Estado'],Pendientes='; '.join(x['Faltantes']+x['Incumplimientos'])))
  chronology.extend(dict(Partida=p['ID'],Fecha=x['Fecha'],Documento=x['ID'],Nombre=x['Nombre'],Tipo=x['Tipo'],Revision=x['Revision']) for x in r['documentos'])
  materials.extend(dict(Partida=p['ID'],**m) for m in r['materiales'])
 with pd.ExcelWriter(out,engine='openpyxl') as w:
  for name,rows in [('Resumen_partidas',summary),('Historial_documental',chronology),('Certificados_por_partida',materials)]:pd.DataFrame(rows).to_excel(w,sheet_name=name,index=False)
  for name in SCHEMA:pd.DataFrame(d[name],columns=SCHEMA[name]).to_excel(w,sheet_name=name,index=False)
  pd.DataFrame(d['Adjuntos']).to_excel(w,sheet_name='Adjuntos',index=False);pd.DataFrame(d['Cargas']).to_excel(w,sheet_name='Historial_cargas',index=False)
  for s in w.book.worksheets:
   s.freeze_panes='A2';s.auto_filter.ref=s.dimensions
   for col in s.columns:s.column_dimensions[col[0].column_letter].width=min(65,max(16,max(len(str(c.value or '')) for c in col)+2))
 return out.getvalue()

def build_pdf(d):
 out=io.BytesIO();styles=getSampleStyleSheet()
 for name in ['BodyText','Title','Heading2','Heading3']:styles[name].fontName='DaAmB' if name!='BodyText' else 'DaAm'
 styles['BodyText'].fontSize=9;styles['BodyText'].leading=13;styles['Title'].fontSize=18;styles['Title'].leading=24
 P=lambda value:Paragraph(escape(str(value)),styles['BodyText'])
 story=[Paragraph('Informe general de inspección y calidad',styles['Title']),P(d['obra']['Nombre']),P('Corte del consolidado: '+d['obra']['Fecha_corte']),P('DOCUMENTO DE EJEMPLO · DATOS FICTICIOS'),Spacer(1,15),P('Partidas obtenidas de los protocolos de calidad cargados. El estado del protocolo se presenta junto con las no conformidades, hallazgos y respaldos de cada partida.')]
 def section(title,lines):
  story.append(Paragraph(title,styles['Heading3']))
  story.extend(P(line) for line in lines or ['Sin registros cargados.'])
 for part in d['Partidas']:
  r=report_part(d,part);x=next(x for x in d['Dossiers'] if x['Partida']==part['ID'])
  story.extend([PageBreak(),Paragraph(escape(part['ID']+' · '+part['Nombre']),styles['Heading2']),P(part['Ubicacion']),P('Estado según último protocolo: '+r['estado']),P('Estado documental del expediente: '+x['Estado'])])
  section('Protocolos de calidad',[f"{p['ID']} · {p['Fecha']} · {p['Resultado']} · Responsable: {p['Responsable']} · Documento: {p['Documento']}" for p in r['protocolos']])
  section('No conformidades: abiertas y resueltas',[f"{n['ID']} · {n['Descripcion']} · {n['Estado']} · Protocolo: {n['Protocolo']} · Responsable: {n['Responsable']} · Compromiso: {n['Compromiso']} · Documento de cierre: {n['DocumentoCierre'] or 'Pendiente'}" for n in r['ncs']])
  rel=related(d,part['ID'])
  section('Inspecciones',[f"{i['ID']} · {i['Fecha']} · {i['Inspector']} · {i['Alcance']} · Documento: {i['Documento']}" for i in d['Inspecciones'] if i['ID'] in rel['Inspeccion']])
  section('Hallazgos de inspección',[f"{h['ID']} · {h['Descripcion']} · {h['Estado']} · Inspección: {h['Inspeccion']} · Cierre: {h['DocumentoCierre'] or 'Pendiente'}" for h in r['hallazgos']])
  section('Materiales, lotes y certificados',[f"{m['ID']} · {m['Material']} · Lote: {m['Lote']} · Proveedor: {m['Proveedor']} · Recepción: {m['Recepcion']} · Certificados: {m['Certificados']}" for m in r['materiales']])
  section('Ensayos y resultados',[f"{e['ID']} · {e['Tipo']} · Muestra: {e['Muestra']} · {e['Estado']} · Resultado: {e['Resultado'] or 'Pendiente'} · Criterio: {e['Criterio']} · Informe: {e['Informe'] or 'Pendiente'}" for e in r['ensayos']])
  section('Pendientes y respaldo de validación',x['Incumplimientos']+x['Faltantes'] or ['Respaldos completos según requisitos del consolidado.'])
  story.append(Paragraph('Historial documental cronológico',styles['Heading3']))
  rows=[[P('Fecha'),P('Documento'),P('Tipo / revisión')]]+[[P(doc['Fecha'][:10]),P(doc['ID']+' · '+doc['Nombre']),P(doc['Tipo']+' · '+doc['Revision'])] for doc in r['documentos']]
  tab=Table(rows,colWidths=[72,280,171],repeatRows=1);tab.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),colors.HexColor('#eaf0f7')),('VALIGN',(0,0),(-1,-1),'TOP'),('BOTTOMPADDING',(0,0),(-1,-1),7),('LINEBELOW',(0,0),(-1,-1),.3,colors.HexColor('#dce5ef'))]));story.append(tab)
 def footer(canvas,doc):canvas.setFont('DaAm',8);canvas.drawString(36,20,'DaAm · Ejemplo ficticio');canvas.drawRightString(A4[0]-36,20,str(doc.page))
 SimpleDocTemplate(out,pagesize=A4,leftMargin=36,rightMargin=36,topMargin=35,bottomMargin=35).build(story,onFirstPage=footer,onLaterPages=footer)
 return out.getvalue()
