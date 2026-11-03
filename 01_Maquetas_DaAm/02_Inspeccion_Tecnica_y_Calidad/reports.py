import io,json
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
from data_model import SCHEMA
fontdir=Path(reportlab.__file__).parent/'fonts'
for name,file in [('DaAm','Vera.ttf'),('DaAmB','VeraBd.ttf')]:pdfmetrics.registerFont(TTFont(name,str(fontdir/file)))
def build_excel(d):
 out=io.BytesIO();parts={p['ID']:p for p in d['Partidas']}
 rows=[dict(Partida=x['Partida'],Nombre=parts[x['Partida']]['Nombre'],Ubicacion=parts[x['Partida']]['Ubicacion'],Estado=x['Estado'],Faltantes='; '.join(x['Faltantes']),Incumplimientos='; '.join(x['Incumplimientos'])) for x in d['Dossiers']]
 with pd.ExcelWriter(out,engine='openpyxl') as w:
  pd.DataFrame(rows).to_excel(w,sheet_name='Validacion_partidas',index=False)
  for name in SCHEMA:pd.DataFrame(d[name],columns=SCHEMA[name]).to_excel(w,sheet_name=name,index=False)
  pd.DataFrame(d['Adjuntos']).to_excel(w,sheet_name='Adjuntos',index=False);pd.DataFrame(d['Cargas']).to_excel(w,sheet_name='Historial_cargas',index=False)
  for s in w.book.worksheets:
   s.freeze_panes='A2'
   for col in s.columns:s.column_dimensions[col[0].column_letter].width=min(65,max(16,max(len(str(c.value or '')) for c in col)+2))
 return out.getvalue()
def build_pdf(d):
 out=io.BytesIO();styles=getSampleStyleSheet()
 for name in ['BodyText','Title','Heading2','Heading3']:
  styles[name].fontName='DaAmB' if name!='BodyText' else 'DaAm'
 styles['BodyText'].fontSize=9;styles['BodyText'].leading=13;styles['Title'].fontSize=18;styles['Title'].leading=24
 P=lambda value:Paragraph(escape(str(value)),styles['BodyText']);story=[Paragraph('Informe general de inspección y calidad',styles['Title']),P(d['obra']['Nombre']),P('Corte del consolidado: '+d['obra']['Fecha_corte']),P('DOCUMENTO DE EJEMPLO · DATOS FICTICIOS'),Spacer(1,15)]
 for state in ['Validada','Pendiente de validación','Con incumplimientos']:story.append(P(state+': '+str(sum(x['Estado']==state for x in d['Dossiers']))))
 story+=[Spacer(1,10),P('El informe consolida los registros elaborados externamente y sus documentos cargados. La validación exige declaración profesional, acta y respaldos completos. No se emiten aprobaciones automáticas al adjuntar archivos.')]
 for part in d['Partidas']:
  x=next(x for x in d['Dossiers'] if x['Partida']==part['ID']);story+=[PageBreak(),Paragraph(escape(part['ID']+' · '+part['Nombre']),styles['Heading2']),P(part['Ubicacion']),P('Estado del expediente: '+x['Estado']),P('Validación declarada: '+part['EstadoDeclarado']+' · '+(part['Validador'] or 'Responsable pendiente')+' · '+(part['FechaValidacion'] or 'Fecha pendiente')),P('Acta: '+(part['DocumentoValidacion'] or 'Pendiente')),Spacer(1,10)]
  story.append(Paragraph('Requisitos y pendientes',styles['Heading3']))
  for msg in x['Incumplimientos']+x['Faltantes'] or ['Requisitos y respaldos completos.']:story.append(P(msg))
  story.append(Paragraph('Documentos del expediente',styles['Heading3']))
  rows=[[P('ID'),P('Documento'),P('Tipo / revisión')]]
  for doc in d['Documentos']:
   if doc['ID'] in x['Documentos']:rows.append([P(doc['ID']),P(doc['Nombre']),P(doc['Tipo']+' · '+doc['Revision'])])
  for doc in d['Adjuntos']:
   if doc['ID'] in x['Adjuntos']:rows.append([P(doc['ID']),P(doc['Nombre']),P(doc['Tipo']+' · '+doc['Revision'])])
  tab=Table(rows,colWidths=[90,260,170],repeatRows=1);tab.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),colors.HexColor('#eaf0f7')),('VALIGN',(0,0),(-1,-1),'TOP'),('BOTTOMPADDING',(0,0),(-1,-1),7),('LINEBELOW',(0,0),(-1,-1),.3,colors.HexColor('#dce5ef'))]));story.append(tab)
  tests=[e for e in d['Ensayos'] if e['Partida']==part['ID']]
  if tests:
   story.append(Paragraph('Ensayos y criterios registrados',styles['Heading3']))
   for e in tests:story.append(P(e['ID']+' · '+e['Tipo']+' · '+e['Estado']+' · Resultado: '+(e['Resultado'] or 'Pendiente')+' · Criterio: '+e['Criterio']+' · Informe: '+(e['Informe'] or 'Pendiente')))
 def footer(canvas,doc):canvas.setFont('DaAm',8);canvas.drawString(36,20,'DaAm · Ejemplo ficticio');canvas.drawRightString(A4[0]-36,20,str(doc.page))
 SimpleDocTemplate(out,pagesize=A4,leftMargin=36,rightMargin=36,topMargin=35,bottomMargin=35).build(story,onFirstPage=footer,onLaterPages=footer)
 return out.getvalue()
