"""Download exactly the visible rows; never export hidden source sheets."""
from io import BytesIO
from html.parser import HTMLParser
import re
import pandas as pd
from data_model import week_label
from openpyxl import Workbook
from openpyxl.styles import Font,PatternFill,Alignment
from openpyxl.utils import get_column_letter


def excel_bytes(df,config,title,filters=None):
    book=Workbook();sheet=book.active;sheet.title='Datos'
    metadata=[('Proyecto',config['Proyecto']),('Listado',title),('Semana de control',week_label(config,config['Semana_Control'])),('Fecha del corte',config['Fecha_Control'].to_pydatetime())]
    metadata+=list((filters or {}).items())
    for key,value in metadata:sheet.append([key,value])
    sheet.append([])
    sheet.append([str(c) for c in df.columns])
    header=sheet.max_row
    for row in df.itertuples(index=False,name=None):
        values=[]
        for value in row:
            if pd.isna(value):value=None
            elif isinstance(value,pd.Timestamp):value=value.to_pydatetime()
            elif hasattr(value,'item'):value=value.item()
            values.append(value)
        sheet.append(values)
        # Source text must remain text, even if it begins with '='.
        for cell,value in zip(sheet[sheet.max_row],values):
            if isinstance(value,str):cell.data_type='s'
    for cell in sheet[header]:cell.fill=PatternFill('solid',fgColor='0E294B');cell.font=Font(color='FFFFFF',bold=True)
    for row in sheet:
        for cell in row:
            cell.alignment=Alignment(vertical='top',wrap_text=True)
            if cell.is_date:cell.number_format='dd/mm/yyyy'
    for i,col in enumerate(df.columns,1):sheet.column_dimensions[get_column_letter(i)].width=min(55,max(18,len(str(col))+3))
    sheet.column_dimensions['B'].width=max(sheet.column_dimensions['B'].width,35)
    sheet.freeze_panes=f'A{header+1}';sheet.auto_filter.ref=f'A{header}:{get_column_letter(max(1,len(df.columns)))}{sheet.max_row}'
    out=BytesIO();book.save(out);return out.getvalue()


def download_table(df,config,title,filters=None,key='data'):
    import streamlit as st
    slug=lambda x:re.sub(r'[^\w-]+','_',str(x)).strip('_')
    filename=f'{slug(config["Proyecto"])}_{slug(title)}_S{config["Semana_Control"]}.xlsx'
    st.download_button('Descargar tabla',excel_bytes(df,config,title,filters),file_name=filename,mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',key=f'download_{key}',on_click='ignore',disabled=df.empty)


class VisibleTables(HTMLParser):
    def __init__(self):
        super().__init__();self.title='Datos';self.heading=False;self.inside=False;self.cell=False;self.text='';self.rows=[];self.tables=[]
    def handle_starttag(self,tag,attrs):
        if tag=='h2':self.heading=True;self.title=''
        if tag=='table':self.inside=True;self.rows=[]
        if self.inside and tag=='tr':self.row=[]
        if self.inside and tag in ('td','th'):self.cell=True;self.text=''
        if self.cell and tag=='br':self.text+=' '
        if self.cell and tag=='span' and dict(attrs).get('class')=='bar':self.text+='Programada'
    def handle_data(self,data):
        if self.heading:self.title+=data
        if self.cell:self.text+=data
    def handle_endtag(self,tag):
        if tag=='h2':self.heading=False
        if self.inside and tag in ('td','th'):self.row.append(self.text.strip());self.cell=False
        if self.inside and tag=='tr':self.rows.append(self.row)
        if tag=='table':
            if self.rows:self.tables.append((self.title,pd.DataFrame(self.rows[1:],columns=self.rows[0])))
            self.inside=False


def export_page_tables(body,config,route):
    import streamlit as st
    parser=VisibleTables();parser.feed(body)
    if not parser.tables:return
    with st.expander('Descargar listados en Excel'):
        st.caption('Cada archivo contiene el listado mostrado y los datos del corte.')
        for i,(title,df) in enumerate(parser.tables):download_table(df,config,title,{'Página':route},f'{route}_{i}')


def download_cnc(plan,config):
    import streamlit as st
    from data_model import weekly_snapshot,pcp,cnc
    from matplotlib.figure import Figure
    import textwrap
    week=config['Semana_Control'];weeks=[w for w in range(max(1,week-2),week+1)]
    counts={w:cnc(weekly_snapshot(plan,w) if w==week else plan[plan.Semana.eq(w)]) if pcp(weekly_snapshot(plan,w) if w==week else plan[plan.Semana.eq(w)],w) is not None else None for w in weeks}
    causes=sorted(set().union(*(set(v.index) for v in counts.values() if v is not None)),key=lambda cause:(-sum(v.get(cause,0)>0 for v in counts.values() if v is not None),-sum(v.get(cause,0) for v in counts.values() if v is not None),cause))
    df=pd.DataFrame({'Causa':causes})
    for w,v in counts.items():df[week_label(config,w)+(' · preliminar' if w==week else '')]=[None if v is None else int(v.get(cause,0)) for cause in causes]
    with st.expander('Descargar gráfico CNC y sus datos'):
        download_table(df,config,'CNC por causa',{'Período':', '.join(week_label(config,w) for w in weeks)},'cnc_comparison')
        if not causes:return
        fig=Figure(figsize=(max(10,len(causes)*2.2),4.3),layout='constrained');ax=fig.subplots()
        colors=['#a9bfd7','#426b98','#0e294b'][-len(weeks):]
        for j,(w,v) in enumerate(counts.items()):
            vals=[0 if v is None else int(v.get(c,0)) for c in causes]
            positions=[i+(j-(len(weeks)-1)/2)*.22 for i in range(len(causes))]
            bars=ax.bar(positions,vals,width=.2,color=colors[j],label=week_label(config,w)+(' · preliminar' if w==week else ''))
            ax.bar_label(bars,labels=[str(n) if n else '' for n in vals],fontsize=9,padding=3)
        ax.set_xticks(range(len(causes)),['\n'.join(textwrap.wrap(c,26)) for c in causes],fontsize=9)
        ax.tick_params(axis='y',labelsize=9);ax.set_ylabel('Cantidad',fontsize=9)
        from matplotlib.ticker import MaxNLocator
        ax.yaxis.set_major_locator(MaxNLocator(integer=True));ax.set_axisbelow(True);ax.grid(axis='y',alpha=.15)
        ax.legend(fontsize=9);ax.set_title(config['Proyecto']+'\nCNC por causa',fontsize=12)
        for i,c in enumerate(causes):
            if sum(v.get(c,0)>0 for v in counts.values() if v is not None)>1:ax.axvspan(i-.45,i+.45,color='#edf3fa',zorder=0)
        buffer=BytesIO();fig.savefig(buffer,format='png',dpi=160)
        st.download_button('Descargar gráfico CNC · PNG',buffer.getvalue(),file_name=f'CNC_S{weeks[0]}_S{week}.png',mime='image/png',key='cnc_png',on_click='ignore')


def graph_png(html,title,config):
    import base64,xml.etree.ElementTree as ET
    from matplotlib.figure import Figure
    from matplotlib.patches import Rectangle,Circle
    fig=Figure(figsize=(11,4),layout='constrained');ax=fig.subplots();ax.axis('off')
    match=re.search(r'data:image/svg\+xml;base64,([^"\s]+)',html)
    if match:
        root=ET.fromstring(base64.b64decode(match.group(1)));_,_,width,height=map(float,root.attrib['viewBox'].split())
        ax.set_xlim(0,width);ax.set_ylim(height,0)
        for node in root:
            tag=node.tag.split('}')[-1];a=node.attrib
            f=lambda k:float(a.get(k,0))
            if tag=='rect':ax.add_patch(Rectangle((f('x'),f('y')),f('width'),f('height'),color=a.get('fill','#294e78'),linewidth=0))
            elif tag=='circle':ax.add_patch(Circle((f('cx'),f('cy')),f('r'),color=a.get('fill','#294e78')))
            elif tag=='line':ax.plot([f('x1'),f('x2')],[f('y1'),f('y2')],color=a.get('stroke','#e2eaf4'),linewidth=float(a.get('stroke-width',1)),linestyle='--' if 'stroke-dasharray' in a else '-')
            elif tag=='text':ax.text(f('x'),f('y'),''.join(node.itertext()),fontsize=9,color=a.get('fill','#173960'),ha={'middle':'center','end':'right'}.get(a.get('text-anchor'),'left'),va='baseline',fontweight='bold' if a.get('font-weight')=='700' else 'normal')
        # Legend for the comparison graph is outside its SVG.
        legend=re.findall(r'</span>(S\d+(?: · preliminar)?)</span>',html)
        if legend:
            from matplotlib.patches import Patch
            ax.legend(handles=[Patch(color=color,label=label) for color,label in zip(['#a9bfd7','#426b98','#0e294b'][-len(legend):],legend)],loc='upper right',fontsize=9)
    else:
        from html import unescape
        rows=re.findall(r'<div class="barcol"><b>(\d+)</b><div class="pillar"[^>]*></div>(.*?)</div>',html)
        if not rows:return None
        ax.axis('on');names=[unescape(c) for _,c in rows];values=[int(n) for n,_ in rows]
        import textwrap
        bars=ax.bar(range(len(rows)),values,color='#294e78',width=.35);ax.bar_label(bars,fontsize=9,padding=3)
        ax.set_xticks(range(len(rows)),['\n'.join(textwrap.wrap(c,27)) for c in names],fontsize=9);ax.tick_params(axis='y',labelsize=9)
    ax.set_title(config['Proyecto']+'\n'+title,fontsize=11,pad=15)
    out=BytesIO();fig.savefig(out,format='png',dpi=160);return out.getvalue()


def render_downloads(body,config,route,css):
    import streamlit as st
    # Every panel is rendered intact, then its direct download buttons.
    starts=[m.start() for m in re.finditer(r'<div class="panel(?: |")',body)]
    if not starts:st.html(f'<style>{css}</style>'+body);return
    if starts[0]:st.html(f'<style>{css}</style>'+body[:starts[0]])
    for i,start in enumerate(starts):
        chunk=body[start:starts[i+1] if i+1<len(starts) else len(body)]
        st.html(f'<style>{css}</style>'+chunk)
        parser=VisibleTables();parser.feed(chunk)
        for j,(title,df) in enumerate(parser.tables):download_table(df,config,title,{'Página':route},f'{route}_{i}_{j}')
        if 'data:image/svg+xml' in chunk or 'class="bars"' in chunk:
            title=re.search(r'<h2>(.*?)</h2>',chunk).group(1)
            data=graph_png(chunk,title,config)
            if data:st.download_button('Descargar gráfico',data,file_name=f'Grafico_{i}_S{config["Semana_Control"]}.png',mime='image/png',key=f'graph_{route}_{i}',on_click='ignore')
