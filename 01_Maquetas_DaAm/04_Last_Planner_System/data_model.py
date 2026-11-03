from pathlib import Path
import pandas as pd
import re

def load(path):
    book = pd.ExcelFile(path)
    config = pd.read_excel(book, sheet_name='00_Configuracion').dropna(subset=['Parametro'])
    config = dict(zip(config.Parametro, config.Valor))
    # Los períodos explícitos del programa prevalecen sobre la fecha de corte.
    raw = pd.read_excel(book, sheet_name='01_Programa_6S', header=None, nrows=7) if '01_Programa_6S' in book.sheet_names else pd.DataFrame()
    periods = {}
    for col in raw.columns:
        match = re.fullmatch(r'S(\d+)', str(raw.iloc[6, col]).strip())
        if match:
            start = pd.to_datetime(raw.iloc[4, col], errors='coerce')
            end = pd.to_datetime(raw.iloc[5, col], errors='coerce')
            if pd.notna(start) and pd.notna(end):
                if (end.normalize()-start.normalize()).days != 6:
                    raise ValueError(f'El período S{match[1]} del Excel debe tener siete días.')
                periods[int(match[1])] = (start.normalize(), end.normalize())
    config['Periodos_Semana'] = periods
    sheets = {}
    catalogo = pd.read_excel(book, sheet_name='00_Catalogo_Habilitantes')
    catalogo.columns = [str(c).strip() for c in catalogo.columns]
    for key, name, header in [('programa','01_Programa_6S',6),('lookahead','02_Lookahead',0),('habilitantes','03_Habilitantes_Restricciones',0),('plan','04_Plan_Semanal_Historico',0)]:
        if name not in book.sheet_names and key=='programa':
            sheets[key]=pd.DataFrame(columns=['ID_Project','Actividad_Project','Inicio_Maestro','Termino_Maestro'])
            continue
        df = pd.read_excel(book, sheet_name=name, header=header)
        if key=='plan':
            df=df.rename(columns={'Tarea_Comprometida':'Tarea_Lookahead','Semana':'Semana_Compromiso','Responsable_Ejecución_Tarea':'Responsable_Tarea','%_Comprometido':'Comprometido_%','%_Avance':'Avance_%','Causa_de_No_Cumplimiento':'Causa_No_Cumplimiento'})
            if 'ID_Compromiso' not in df:
                df['ID_Compromiso']=['C-'+str(i+1) for i in range(len(df))]
            # Excel guarda los porcentajes nuevos como fracciones (1 = 100%).
            for col in ['Comprometido_%','Avance_%']:
                if col in df and '%_Comprometido' in pd.read_excel(book,sheet_name=name,nrows=0).columns:
                    df[col]=pd.to_numeric(df[col],errors='coerce')*100
        df.columns = [str(c).strip() for c in df.columns]
        anchor = 'Actividad_Project' if key=='programa' else 'Tarea_Lookahead'
        df = df[df[anchor].notna()].copy()
        for col in df.columns:
            if col.startswith(('Inicio','Fin','Termino','Fecha')):
                df[col] = pd.to_datetime(df[col], errors='coerce')
        sheets[key] = df
    hab = sheets['habilitantes']
    hab['Tipo_Habilitante'] = hab['Actividad_Habilitante'].map(catalogo.dropna(subset=['Actividad_Habilitante']).drop_duplicates('Actividad_Habilitante').set_index('Actividad_Habilitante')['Tipo_Habilitante'])
    hab['Fecha_Liberacion_Requerida'] = pd.to_datetime(hab['Fecha_Liberacion_Requerida'] if 'Fecha_Liberacion_Requerida' in hab else hab['Fecha_Requerida_Liberacion_'], errors='coerce')
    hab['Estado_Habilitante'] = hab['Liberada'].fillna('').astype(str).str.strip().str.casefold().map({'sí':'Liberado','si':'Liberado','no':'Pendiente'}).fillna('Pendiente')
    plan = sheets['plan']
    plan['Semana'] = pd.to_numeric(plan.Semana_Compromiso.astype(str).str.strip().str.extract(r'(?i)^S?([1-9]\d*)(?:\.0)?$',expand=False),errors='coerce')
    plan['Avance'] = pd.to_numeric(plan['Avance_%'].astype(str).str.replace('%','',regex=False).str.replace(',','.',regex=False),errors='coerce')
    # Ambos porcentajes corresponden al trabajo de la misma semana, escala 0–100.
    target=plan['Comprometido_%'] if 'Comprometido_%' in plan else pd.Series(100,index=plan.index)
    plan['Comprometido'] = pd.to_numeric(target.astype(str).str.replace('%','',regex=False).str.replace(',','.',regex=False),errors='coerce')
    # El estado lo determina exclusivamente Cumplida, no los porcentajes de avance.
    flags = plan['Cumplida'].fillna('').astype(str).str.strip().str.casefold()
    plan['Resultado'] = 'Pendiente de cierre'
    plan.loc[flags.isin(['sí','si']), 'Resultado'] = 'Cumplido'
    plan.loc[flags.eq('no'), 'Resultado'] = 'No cumplido'
    if sum(len(frame.index) for frame in sheets.values()) == 0:
        config['Sin_Datos']=True
        return config,sheets,[]
    # Un maestro aún sin semana y fecha no debe generar indicadores.
    required=['Semana_Control','Semanas_Totales','Fecha_Control']
    missing=[key for key in required if pd.isna(config.get(key)) or str(config.get(key)).strip()=='']
    if missing:
        config['Sin_Datos']=True
        config['Configuracion_Pendiente']=missing
        return config,sheets,[]
    config['Semana_Control'] = int(config['Semana_Control'])
    config['Semanas_Totales'] = int(config['Semanas_Totales'])
    config['Fecha_Control'] = pd.Timestamp(config['Fecha_Control'])
    # La semana vigente se publica abierta; el corte histórico avanza con Semana_Control.
    plan.loc[plan.Semana.eq(config['Semana_Control']) & plan.Resultado.eq('Pendiente de cierre'),'Resultado']='En proceso'
    issues=[]
    look=sheets['lookahead']
    if '01_Programa_6S' not in book.sheet_names and 'Semana' in look:
        # Referencia de calendario consistente con las semanas explícitas del lookahead.
        anchors=[]
        for _,row in look.iterrows():
            match=re.fullmatch(r'S(\d+)',str(row.Semana).strip(),re.I)
            if match and pd.notna(row.Inicio_Tarea):
                date=row.Inicio_Tarea.normalize()
                anchors.append(date-pd.Timedelta(days=(date.weekday()-3)%7+7*(int(match[1])-1)))
        if anchors and pd.isna(config.get('Inicio_Semana_Control')):
            origin=pd.Series(anchors).mode().iloc[0]
            config['Inicio_Semana_Control']=origin+pd.Timedelta(weeks=config['Semana_Control']-1)
        if config['Fecha_Control'] < week_start(config,config['Semana_Control']):
            issues.append('Fecha_Control es anterior al inicio de la semana de control; revise la configuración del Maestro. Las fechas de corte se conservan sin modificación.')
    if plan.Semana.isna().any():
        invalid=plan.loc[plan.Semana.isna(),'ID_Compromiso'].astype(str).tolist()
        issues.append('Control histórico: cada compromiso requiere una sola semana (ejemplo S7), sin rangos. Corrija: '+', '.join(invalid)+'. Los registros inválidos se excluyen de los cálculos y el PCP de las semanas afectadas queda sin publicar hasta corregirlos.')
    if plan.duplicated(['Semana','ID_Compromiso']).any(): issues.append('Hay compromisos duplicados dentro de una misma semana.')
    if ((plan.Avance<0)|(plan.Avance>100)).any(): issues.append('Hay avances fuera de la escala 0–100.')
    if plan.Comprometido.isna().any() or (~plan.Comprometido.dropna().between(0,100)).any(): issues.append('Complete Comprometido_% con una meta semanal válida entre 0 y 100.')
    if (plan.Resultado.eq('No cumplido') & plan.Causa_No_Cumplimiento.fillna('').astype(str).str.strip().eq('')).any(): issues.append('Hay compromisos no cumplidos sin causa registrada; complete Causa_No_Cumplimiento.')
    for key in ['lookahead','habilitantes']:
        id_col='ID_Tarea' if key=='lookahead' else 'ID_Habilitante'
        if sheets[key][id_col].duplicated().any(): issues.append(f'Hay identificadores duplicados en {key}.')
    ids=set(sheets['lookahead'].ID_Tarea)
    if not sheets['habilitantes'].ID_Tarea.isin(ids).all(): issues.append('Hay habilitantes sin una tarea vinculada en el Lookahead.')
    return config,sheets,issues

def invalid_week_records(plan,week):
    if 'Semana_Compromiso' not in plan:return False
    invalid=plan[plan.Semana.isna()]
    return any(not task_weeks(value) or int(week) in task_weeks(value) for value in invalid.Semana_Compromiso)


def pcp(plan,week):
    if invalid_week_records(plan,week):return None
    rows=plan[plan.Semana==week]
    if rows.empty or rows.ID_Compromiso.duplicated().any(): return None
    evaluated=rows[rows.Resultado.isin(['Cumplido','No cumplido'])]
    if evaluated.empty:return None
    return 100*evaluated.Resultado.eq('Cumplido').sum()/len(evaluated)

CNC_GROUPS = {
 'Materiales / Suministros':['Materiales no disponibles','Suministro de materiales interrumpido','Materiales defectuosos o incorrectos'],
 'Mano de Obra':['Personal insuficiente o ausente','Bajo rendimiento de cuadrilla'],
 'Maquinaria':['Maquinaria insuficiente o indisponible','Fallas de maquinaria'],
 'Subcontratos':['Inasistencia del subcontratista','Dotación insuficiente del subcontratista','Bajo rendimiento del subcontratista'],
 'Ingeniería / Información':['Información técnica pendiente','Errores en información técnica'],
 'Aprobación Documental':['Documentación pendiente de aprobación'],
 'Aprobación Operativa Mandante / ITO':['Aprobación operativa pendiente por mandante','Paralización instruida por mandante'],
 'Permisos / Autorizaciones':['Permisos o autorizaciones pendientes'],
 'Predecesoras / Frente':['Frente no disponible','Actividad previa pendiente','Actividades habilitantes pendientes'],
 'Planificación / Coordinación':['Interferencia entre especialidades','Descoordinación entre cuadrillas','Error de planificación','Cambio de prioridades','Reprogramación','Tarea reprogramada'],
 'Calidad':['Inspección o recepción pendiente','Corrección de trabajos defectuosos'],
 'Seguridad':['Paralización por condiciones inseguras'],
 'Clima':['Condiciones climáticas adversas'],
 'Eventos Excepcionales':['Eventos imprevistos excepcionales'],
 'Otro':['Otra causa']}
CNC_MAP={cause:group for group,causes in CNC_GROUPS.items() for cause in causes}

def cnc(plan):
    causes = plan.loc[plan.Resultado.eq('No cumplido'), 'Causa_No_Cumplimiento']
    # Excel puede inferir una columna vacía como numérica.
    causes = causes[causes.map(lambda value: isinstance(value, str))].astype('string').str.strip()
    return causes[causes.ne('')].value_counts()


def tasks_in_week(look, config, week):
    if 'Semana' in look:
        return look[look['Semana'].map(lambda value: int(week) in task_weeks(value))].copy()
    start=week_start(config,week)
    end=week_end(config,week)
    return look[(look.Inicio_Tarea<=end)&(look.Fin_Tarea>=start)].copy()


def task_weeks(value):
    """Semanas explícitas: S7, S7–S8, S7-S8 o S7, S9 (sin rellenar huecos)."""
    text=str(value).strip().upper()
    weeks=set()
    pattern=r'S?(\d+)\s*[-–—]\s*S?(\d+)'
    for match in re.finditer(pattern,text):
        first,last=map(int,match.groups())
        if 1<=first<=last<=10000:weeks.update(range(first,last+1))
    text=re.sub(pattern,'',text)
    weeks.update(int(n) for n in re.findall(r'\d+',text))
    return weeks


def pending_habilitantes(hab):
    return hab[hab.Estado_Habilitante.fillna('').astype(str).str.strip().str.casefold().ne('liberado')].copy()

def management_summary(config,sheets):
    week=config['Semana_Control'];plan=sheets['plan']
    failed=plan[(plan.Semana==week-1)&plan.Resultado.eq('No cumplido')].copy()
    current_ids=set(plan.loc[plan.Semana==week,'ID_Tarea'].dropna().astype(str).str.strip())
    current_ids.discard('')
    missing=failed[~failed.ID_Tarea.fillna('').astype(str).str.strip().isin(current_ids)].copy()
    # La unidad del indicador es una tarea, aunque tenga varios compromisos.
    missing['_task_key']=missing.ID_Tarea.fillna('').astype(str).str.strip()
    missing['_task_key']=missing['_task_key'].where(missing['_task_key'].ne(''), 'sin_id_'+missing.index.astype(str))
    missing=missing.drop_duplicates('_task_key').drop(columns='_task_key')
    pending=pending_habilitantes(sheets['habilitantes'])
    next_tasks=tasks_in_week(sheets['lookahead'],config,week+1)
    upcoming=pending[pending.ID_Tarea.isin(next_tasks.ID_Tarea)].copy()
    overdue=pending[pending.Fecha_Liberacion_Requerida<config['Fecha_Control']]
    return failed,missing,pending,upcoming,overdue


def weekly_snapshot(plan,week):
    """Estado explícito de cumplimiento, sin inferirlo del avance."""
    return plan[plan.Semana.eq(week)].copy()


def week_start(config, week):
    """Inicio por semana, independiente de la fecha de corte de indicadores.

    Inicio_Semana_Control permite fijar la referencia explícita en el Maestro.
    Dia_Inicio_Semana usa lunes=0 ... domingo=6; por defecto jueves=3.
    """
    periods = config.get('Periodos_Semana', {})
    if int(week) in periods:
        return periods[int(week)][0]
    if periods:
        anchor = min(periods, key=lambda value: abs(value-int(week)))
        return periods[anchor][0]+pd.Timedelta(days=7*(int(week)-anchor))
    reference = config.get('Inicio_Semana_Control')
    if reference is None or pd.isna(reference):
        reference = pd.Timestamp(config['Fecha_Control']).normalize()
        weekday = int(config.get('Dia_Inicio_Semana', 3))
        if weekday not in range(7):
            raise ValueError('Dia_Inicio_Semana debe estar entre 0 y 6.')
        reference += pd.Timedelta(days=-((reference.weekday()-weekday)%7))
    return pd.Timestamp(reference).normalize()+pd.Timedelta(days=7*(int(week)-config['Semana_Control']))


def week_end(config, week):
    periods = config.get('Periodos_Semana', {})
    return periods[int(week)][1] if int(week) in periods else week_start(config, week)+pd.Timedelta(days=6)


def week_label(config, week):
    return f'S{int(week)}({week_start(config, week).strftime("%d/%m/%Y")})'
