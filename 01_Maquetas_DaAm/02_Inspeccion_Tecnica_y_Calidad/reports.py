import io
from pathlib import Path
import reportlab
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
_FONT_DIR=Path(reportlab.__file__).parent/"fonts"
pdfmetrics.registerFont(TTFont("DaAmText",str(_FONT_DIR/"Vera.ttf")))
pdfmetrics.registerFont(TTFont("DaAmBold",str(_FONT_DIR/"VeraBd.ttf")))
from datetime import date,timedelta
from xml.sax.saxutils import escape
import pandas as pd
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate,Paragraph,Spacer,Table,TableStyle
from data_model import metrics


def report_rows(data,cut,period):
    end=date.fromisoformat(cut);start=end-timedelta(days=6 if period=='Semanal' else 0)
    inspections=[i for i in data['Inspecciones'] if i['Ejecutada'] and start.isoformat()<=i['Ejecutada']<=cut]
    changed={c['Hallazgo'] for c in data['Comentarios'] if start.isoformat()<=c['Fecha'][:10]<=cut}
    findings=[h for h in data['Hallazgos'] if start.isoformat()<=h['Creado']<=cut or h['ID'] in changed or h['Estado']!='Cerrada' and h['Creado']<=cut]
    return start.isoformat(),inspections,findings


def build_pdf(data,cut,period):
    start,ins,halls=report_rows(data,cut,period);m=metrics(data,cut);styles=getSampleStyleSheet();styles['BodyText'].fontName='DaAmText';styles['BodyText'].fontSize=9;styles['BodyText'].leading=13;styles['Title'].fontName='DaAmBold';styles['Title'].fontSize=17;styles['Title'].leading=22;styles['Heading2'].fontName='DaAmBold';styles['Heading2'].fontSize=12;styles['Heading2'].keepWithNext=True;buf=io.BytesIO();doc=SimpleDocTemplate(buf,pagesize=A4,rightMargin=35,leftMargin=35,topMargin=35,bottomMargin=35)
    P=lambda v:Paragraph(escape(str(v)),styles['BodyText']);story=[Paragraph('DaAm · Inspección Técnica y Calidad',styles['Title']),Spacer(1,8),P(data['obra']['Nombre']),P(f'Informe {period.lower()} · período {start} al {cut}'),P('DOCUMENTO DE EJEMPLO · DATOS FICTICIOS'),Spacer(1,14)]
    story+=[Paragraph('Resumen al corte',styles['Heading2']),P('Cumplimiento de criterios: '+(f"{m['quality']*100:.1f}%" if m['quality'] is not None else 'Sin criterios evaluados')),P(f"Inspecciones con resultado: {m['done']}. Aprobadas: {m['approved']}"),P(f"No conformidades: {m['open']} abiertas, {m['review']} en revisión, {m['closed']} cerradas."),Spacer(1,12)]
    def section(title,head,rows,widths):
        story.append(Paragraph(title,styles['Heading2']))
        matrix=[[P(h) for h in head]]+[[P(x) for x in r] for r in rows]
        if not rows:matrix.append([P('Sin registros en el período')]+[P('') for _ in head[1:]])
        t=Table(matrix,colWidths=widths,repeatRows=1,hAlign='LEFT');t.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),colors.HexColor('#e8eff7')),('VALIGN',(0,0),(-1,-1),'TOP'),('BOTTOMPADDING',(0,0),(-1,-1),7),('TOPPADDING',(0,0),(-1,-1),7),('LINEBELOW',(0,0),(-1,-1),.3,colors.HexColor('#dce5ef'))]));story.append(t)
    section('Inspecciones del período',['ID','Ubicación','Resultado','Fecha'],[[i['ID'],i['Ubicacion'],i['Estado'],i['Ejecutada']] for i in ins],[120,120,150,100])
    section('Hallazgos y pendientes',['ID','Descripción','Estado','Compromiso'],[[h['ID'],h['Descripcion'],h['Estado'],h['Compromiso']] for h in halls],[65,240,90,95])
    section('Referencias de evidencia',['Hallazgo','Inicial','Reparación'],[[h['ID'],h['Foto_inicial'],h['Foto_reparacion'] or 'Pendiente'] for h in halls],[90,200,200])
    story+=[Spacer(1,14),P('Este informe utiliza el estado registrado al generar la descarga y conserva las referencias a los protocolos y evidencias. Validación registrada en plataforma; sin firma electrónica avanzada.')]
    def footer(canvas,doc):canvas.setFont('DaAmText',8);canvas.setFillColor(colors.HexColor('#667b92'));canvas.drawString(35,20,'DaAm · Ejemplo ficticio');canvas.drawRightString(A4[0]-35,20,f'Página {doc.page}')
    doc.build(story,onFirstPage=footer,onLaterPages=footer);return buf.getvalue()


def build_excel(data,cut,period):
    start,ins,halls=report_rows(data,cut,period);out=io.BytesIO()
    with pd.ExcelWriter(out,engine='openpyxl') as writer:
        pd.DataFrame([{'Obra':data['obra']['Nombre'],'Desde':start,'Hasta':cut,'Tipo':period,**metrics(data,cut)}]).to_excel(writer,sheet_name='Resumen',index=False)
        pd.DataFrame(ins).to_excel(writer,sheet_name='Inspecciones',index=False)
        pd.DataFrame(halls).to_excel(writer,sheet_name='Hallazgos',index=False)
        pd.DataFrame(data['approvals']).to_excel(writer,sheet_name='Validaciones',index=False)
        for s in writer.book.worksheets:
            s.freeze_panes='A2'
            for col in s.columns:s.column_dimensions[col[0].column_letter].width=min(65,max(16,max(len(str(c.value or '')) for c in col)+2))
    return out.getvalue()
