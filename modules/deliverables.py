"""Two separate outputs: complete research XLSX and provisional editorial PDF."""
from io import BytesIO
from html import escape
import re
from artifact_tool import Workbook, SpreadsheetFile
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, KeepTogether, PageBreak
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.units import cm

NAVY='#10103F'; CYAN='#16C6DD'; PURPLE='#7D3CE6'; PINK='#EF258E'
DATA_KEYS=['keywords','clasificacion','facetas','sources','rejected','entities','concepts','wikidata','openalex','serp','competidores']

def excel_report(run):
    wb=Workbook.create(); sh=wb.worksheets.add('Resumen ejecutivo')
    sh.merge_cells('A1:H2'); sh.get_range('A1').values=[['INVESTIGACION SEMANTICA | '+run['topic']]]
    sh.get_range('A1:H2').format={'fill':NAVY,'font':{'color':'#FFFFFF','bold':True,'size':17}}
    sh.merge_cells('A4:H4');sh.get_range('A4').values=[[run['country']+' | Español | Demanda CSV Semrush']]
    sh.get_range('A4:H4').format={'fill':'#E8F8FC','font':{'color':NAVY,'bold':True}}
    for i,(label,key) in enumerate([('Keywords','keywords'),('Facetas provisionales','facetas'),('Fuentes','sources'),('Entidades','entities'),('Conceptos','concepts'),('Wikidata candidatos','wikidata'),('OpenAlex candidatos','openalex')]):
        row=6+i*2
        sh.merge_cells(f'A{row}:D{row}');sh.merge_cells(f'E{row}:H{row}')
        sh.get_range(f'A{row}').values=[[label]];sh.get_range(f'E{row}').values=[[len(run.get(key,[]))]]
        sh.get_range(f'A{row}:D{row}').format={'fill':'#F1F0F8','font':{'color':NAVY,'bold':True}}
        sh.get_range(f'E{row}:H{row}').format={'fill':'#F1F0F8','font':{'color':PURPLE,'bold':True,'size':14}}
    sh.merge_cells('A22:H24');sh.get_range('A22').values=[['Datos y facetas exploratorios. La propuesta editorial no sustituye validacion de SERP, canibalizacion ni inventario de URLs.']]
    sh.get_range('A22:H24').format={'fill':'#FCEAF4','font':{'color':NAVY},'wrap_text':True}
    sh.get_range('A:H').format.column_width=16
    for key in DATA_KEYS:
        frame=run.get(key)
        if frame is None:continue
        ws=wb.worksheets.add(key[:31]); cols=list(frame.columns) if len(frame.columns) else ['estado']
        ws.get_range_by_indexes(0,0,1,len(cols)).values=[cols]
        ws.get_range_by_indexes(0,0,1,len(cols)).format={'fill':NAVY,'font':{'color':'#FFFFFF','bold':True}}
        ws.get_range_by_indexes(0,0,1,len(cols)).format.column_width=26
        ws.freeze_panes.freeze_rows(1)
        if len(frame):
            data=[]
            for row in frame.itertuples(index=False,name=None):
                data.append([str(v)[:16000] if v is not None and str(v)!='nan' else None for v in row])
            # block writes to avoid excessive RPC payloads
            for start in range(0,len(data),300):
                chunk=data[start:start+300]
                ws.get_range_by_indexes(start+1,0,len(chunk),len(cols)).values=chunk
    import tempfile,os
    fd,path=tempfile.mkstemp(suffix='.xlsx');os.close(fd)
    try:
        SpreadsheetFile.export_xlsx(wb).save(path)
        with open(path,'rb') as f:return f.read()
    finally:
        os.unlink(path)

def editorial_plan(run,domain='',existing_urls=''):
    """Editorial hypotheses, not verified page decisions."""
    topic=run['topic'].strip(); country=run['country']
    domain=domain.strip().replace('https://','').replace('http://','').strip('/')
    existing=[x.strip() for x in existing_urls.splitlines() if x.strip()]
    facets=run.get('facetas')
    names=facets['grupo'].astype(str).tolist() if facets is not None and 'grupo' in facets else []
    names=[x for x in names if 'verificar' not in x.lower()][:6]
    if not names:names=['Conceptos fundamentales','Preguntas frecuentes']
    kw=run.get('keywords')
    top=kw.sort_values('volume',ascending=False).head(12) if kw is not None and 'volume' in kw else None
    return {'topic':topic,'country':country,'domain':domain,'existing':existing,'facets':names,'top':top,
      'status':'HIPOTESIS PARA REVISION: no se han validado intenciones ni URLs existentes',
      'note':'No crear ni actualizar URLs hasta contrastar inventario actual, intencion y riesgo de canibalizacion.'}

def editorial_pdf(run,domain='',existing_urls=''):
    p=editorial_plan(run,domain,existing_urls)
    out=BytesIO(); doc=SimpleDocTemplate(out,pagesize=(21*cm,29.7*cm),leftMargin=1.8*cm,rightMargin=1.8*cm,topMargin=1.8*cm,bottomMargin=1.6*cm)
    styles=getSampleStyleSheet()
    styles.add(ParagraphStyle(name='HeroSEO',parent=styles['Title'],fontName='Helvetica-Bold',fontSize=20,leading=25,textColor=colors.HexColor(NAVY),spaceAfter=14))
    styles.add(ParagraphStyle(name='HeadSEO',parent=styles['Heading2'],fontSize=12,leading=16,textColor=colors.HexColor(PURPLE),spaceBefore=15,spaceAfter=8))
    styles.add(ParagraphStyle(name='BodySEO',parent=styles['BodyText'],fontSize=9,leading=14,spaceAfter=8))
    styles.add(ParagraphStyle(name='SmallSEO',parent=styles['BodyText'],fontSize=8,leading=11))
    def P(t,style='BodySEO'):return Paragraph(escape(str(t)),styles[style])
    story=[P('INFORME EDITORIAL | BRIEF Y ARQUITECTURA','HeroSEO'),P(f"Tema: {p['topic']}   |   Mercado: {p['country']}"),P(p['status'])]
    story += [P('01  Resumen ejecutivo','HeadSEO'),P('La investigación aporta datos de demanda y conceptos semánticos. Las recomendaciones de contenido siguientes son hipótesis editoriales, no decisiones de publicación validadas.')]
    story += [P('02  Brief SEO preliminar','HeadSEO'),P('Objetivo: responder a la necesidad principal del tema y cubrir facetas respaldadas por el corpus y las keywords.'),P('Audiencia: usuarios que investigan el tema en el mercado seleccionado. Definir segmento específico antes de redactar.'),P('Keyword principal candidata: '+p['topic']+'. Validar intención y demanda exacta antes de asignarla.')]
    if p['top'] is not None:
        cells=[[P('Keyword','SmallSEO'),P('Volumen','SmallSEO'),P('Intención Semrush','SmallSEO')]]
        for _,r in p['top'].head(8).iterrows():cells.append([P(r.get('keyword',''),'SmallSEO'),P(r.get('volume',''),'SmallSEO'),P(r.get('intent','Sin dato'),'SmallSEO')])
        t=Table(cells,colWidths=[9*cm,2.2*cm,5.8*cm],repeatRows=1,hAlign='LEFT');t.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),colors.HexColor(NAVY)),('TEXTCOLOR',(0,0),(-1,0),colors.white),('ROWBACKGROUNDS',(0,1),(-1,-1),[colors.white,colors.HexColor('#F2F3F8')]),('VALIGN',(0,0),(-1,-1),'TOP'),('BOTTOMPADDING',(0,0),(-1,-1),7)]));story.append(t)
    story += [P('03  Estructura H1–H3 propuesta','HeadSEO'),P('H1: '+p['topic']),P('H2: Qué es y cómo funciona'),P('H2: Aspectos esenciales para '+p['country'])]
    for f in p['facets'][:5]:story.append(P('H3 (hipótesis): '+f))
    story += [P('H2: Preguntas frecuentes (seleccionar preguntas reales de Semrush; no inventar demanda)')]
    story += [P('04  Arquitectura de URLs propuesta','HeadSEO')]
    slug=re.sub(r'[^a-z0-9]+','-',__import__('unicodedata').normalize('NFKD',p['topic'].lower()).encode('ascii','ignore').decode()).strip('-')
    suggested=('/'+slug+'/')
    story += [P('Página pilar candidata: '+(f'https://{p["domain"]}{suggested}' if p['domain'] else suggested)),P('Estado: URL sugerida, NO verificada como disponible ni necesaria.')]
    for f in p['facets'][:4]:
        sf=re.sub(r'[^a-z0-9]+','-',__import__('unicodedata').normalize('NFKD',f.lower()).encode('ascii','ignore').decode()).strip('-')
        story.append(P('Subtema candidato: '+suggested+sf+'/ — revisar si debe ser sección H2 o URL independiente.'))
    story += [P('URLs existentes aportadas: '+str(len(p['existing']))),P('No se ha realizado crawling del dominio ni validación de canibalización. El inventario proporcionado solo permite una revisión preliminar.')]
    story += [P('05  Enlazado y validación antes de publicar','HeadSEO'),P('Vincular páginas relacionadas solo cuando se compruebe que existen y sus intenciones son distintas.'),P(p['note'])]
    story += [P('06  Límites y trazabilidad','HeadSEO'),P('Wikidata: candidatos hasta validación de identidad. OpenAlex: metadatos no equivalen a lectura científica. Grupos: hipótesis, no clusters SERP. Volumen: estimación de demanda, no tráfico potencial.')]
    def footer(canvas,doc):
        canvas.setStrokeColor(colors.HexColor(CYAN));canvas.line(1.8*cm,1.2*cm,19.2*cm,1.2*cm)
        canvas.setFont('Helvetica',8);canvas.setFillColor(colors.HexColor(NAVY));canvas.drawString(1.8*cm,.9*cm,'INVESTIGACION SEMANTICA  |  INFORME EDITORIAL');canvas.drawRightString(19.2*cm,.9*cm,str(doc.page))
    doc.build(story,onFirstPage=footer,onLaterPages=footer)
    return out.getvalue()
