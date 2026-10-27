import io, hashlib, zipfile
import pandas as pd
import streamlit as st
from modules.demanda import load_semrush
from modules.facetas import build
from modules.spacy_nlp import wikipedia_texts, analyze
from modules.wikidata import lookup
from modules.openalex import search
from modules.quality import curate_sources, curate_entities
from modules.architecture import parse_sitemap, verify_entities, facet_matrix, plan_pages, brief_rows
from modules.deliverables import full_excel, editorial_pdf_v2

COUNTRIES=['Perú','Colombia','México','Argentina','Chile','Bolivia','Ecuador','Uruguay','Paraguay','Venezuela','Costa Rica','Panamá','Guatemala','El Salvador','Honduras','Nicaragua','República Dominicana','Cuba']
st.set_page_config(page_title='Semantic SEO Research Studio',page_icon='🔎',layout='wide')
st.title('Semantic SEO Research Studio')
st.caption('Semrush Keywords + Questions → Wikipedia → spaCy → Wikidata → OpenAlex → Facetas → PAI / clúster → Brief trazable')
st.error('Acceso no protegido: no subas CSV confidenciales hasta configurar acceso privado para las tres cuentas autorizadas.')
with st.sidebar:
    topic=st.text_input('Consulta semilla','Posicionamiento web')
    country=st.selectbox('País',COUNTRIES,index=2)
    st.caption('Idioma: español')
    domain=st.text_input('Dominio del proyecto (opcional)','')
st.subheader('1 · Exportaciones obligatorias de Semrush')
c1,c2=st.columns(2)
with c1: keyword_files=st.file_uploader('CSV de todas las keywords (Keyword Magic Tool)',type='csv',accept_multiple_files=True)
with c2: question_files=st.file_uploader('CSV de preguntas (Questions)',type='csv',accept_multiple_files=True)
sitemap_file=st.file_uploader('Sitemap XML o XML.GZ (recomendado para arquitectura)',type=['xml','gz'])
st.caption('No se exige SERP ni exportación de competidores. Si falta el sitemap, las URLs quedarán pendientes de inventario.')
if not keyword_files or not question_files:
    st.info('Adjunta los dos tipos de CSV de Semrush para comenzar: keywords y preguntas.')
    st.stop()
try:
    keywords=load_semrush(keyword_files)
    questions=load_semrush(question_files)
    if keywords.empty or questions.empty:raise ValueError('Una exportación está vacía.')
    sitemap=parse_sitemap(sitemap_file.getvalue(),sitemap_file.name) if sitemap_file else pd.DataFrame(columns=['url','lastmod','origen'])
    detail,facets=build(keywords,topic)
    matrix=facet_matrix(detail,questions)
    st.subheader('2 · Demanda y preguntas')
    a,b,c=st.columns(3);a.metric('Keywords',len(keywords));b.metric('Preguntas observadas',len(questions));c.metric('URLs en sitemap',len(sitemap))
    with st.expander('Keywords y preguntas importadas'):
        st.dataframe(keywords.head(100),hide_index=True);st.dataframe(questions.head(100),hide_index=True)
    st.dataframe(matrix,hide_index=True)
    confirmed=st.checkbox(f'Confirmo que ambos CSV corresponden a {country} y al tema investigado')
    fingerprint=hashlib.sha256((topic+country+''.join(hashlib.sha256(f.getvalue()).hexdigest() for f in keyword_files+question_files)+(hashlib.sha256(sitemap_file.getvalue()).hexdigest() if sitemap_file else '')).encode()).hexdigest()
    if st.button('Ejecutar las cuatro capas',disabled=not confirmed,type='primary'):
        with st.spinner('Construyendo corpus Wikipedia y ejecutando spaCy...'):
            docs,rejected=wikipedia_texts(topic)
            if not docs:st.error('Wikipedia no devolvió corpus pertinente; investigación detenida, sin inventar resultados.')
            else:
                entities,concepts=analyze(docs,topic)
                sources=curate_sources(pd.DataFrame([{'titulo':d['titulo'],'url':d['url'],'coincidencias':d['coincidencias']} for d in docs]),topic)
                st.session_state['run']={'key':fingerprint,'topic':topic,'country':country,'keywords':keywords,'questions':questions,'clasificacion':detail,'facetas':facets,'matriz':matrix,'sitemap':sitemap,'sources':sources,'rejected':pd.DataFrame(rejected,columns=['titulo','motivo']),'entities':curate_entities(entities),'concepts':concepts,'wikidata':pd.DataFrame(),'openalex':pd.DataFrame()}
    r=st.session_state.get('run')
    if r and r['key']==fingerprint:
        st.subheader('3 · Corpus y spaCy')
        st.dataframe(r['sources'],hide_index=True)
        with st.expander('Entidades y conceptos'):st.dataframe(r['entities'],hide_index=True);st.dataframe(r['concepts'],hide_index=True)
        if st.button('Consultar Wikidata y OpenAlex'):
            with st.spinner('Consultando fuentes abiertas...'):
                terms=[topic]+r['sources'].titulo.head(5).tolist()
                r['wikidata']=lookup(terms,topic)
                r['openalex']=search([topic,topic+' investigación',topic+' aprendizaje'],topic)
        if not r['wikidata'].empty:
            st.subheader('4 · Revisar Wikidata')
            st.caption('Aprobar significa que has comprobado el significado y el QID. No se aprueba automáticamente.')
            edits=r['wikidata'].copy();edits['revision_humana']='pendiente'
            edited=st.data_editor(edits,hide_index=True,column_config={'revision_humana':st.column_config.SelectboxColumn('Revisión',options=['pendiente','aprobar','descartar'])},disabled=[c for c in edits.columns if c!='revision_humana'],key='qid_editor')
            decisions=dict(zip(edited.qid_candidato.astype(str),edited.revision_humana.astype(str)))
            r['entidades_revisadas']=verify_entities(r['wikidata'],decisions)
        if not r['openalex'].empty:
            st.subheader('5 · OpenAlex')
            st.dataframe(r['openalex'],hide_index=True)
            st.warning('Los metadatos no equivalen a lectura académica. Los trabajos sin revisión permanecen pendientes.')
        st.subheader('6 · Arquitectura y briefs con evidencia')
        if st.button('Generar arquitectura, Excel y PDF'):
            with st.spinner('Preparando propuestas y matrices de evidencia...'):
                pages=plan_pages(topic,country,detail,questions,sitemap,r['sources'],r.get('entidades_revisadas',pd.DataFrame()),r['openalex'])
                r['arquitectura']=pages
                r['brief']=brief_rows(pages,detail,questions,r['sources'],r.get('entidades_revisadas',pd.DataFrame()),r['openalex'])
                try:
                    r['xlsx']=full_excel(r);r['pdf']=editorial_pdf_v2(r)
                except Exception as e:st.error(f'Error al generar archivos: {type(e).__name__}: {e}')
        if 'arquitectura' in r:
            st.dataframe(r['arquitectura'],hide_index=True)
            st.dataframe(r['brief'],hide_index=True)
        if 'xlsx' in r:st.download_button('Descargar investigación completa (Excel)',r['xlsx'],'investigacion_semantica.xlsx','application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        if 'pdf' in r:st.download_button('Descargar arquitectura y briefs (PDF)',r['pdf'],'arquitectura_y_briefs.pdf','application/pdf')
        if 'arquitectura' in r:
            buf=io.BytesIO()
            with zipfile.ZipFile(buf,'w',zipfile.ZIP_DEFLATED) as z:
                for k,v in r.items():
                    if isinstance(v,pd.DataFrame):z.writestr(k+'.csv',v.to_csv(index=False))
            st.download_button('Descargar evidencia técnica (ZIP)',buf.getvalue(),'evidencia.zip','application/zip')
    elif r:st.info('Cambiaron los archivos, tema o país. Ejecuta una investigación nueva.')
except Exception as e:
    st.error(f'Error: {type(e).__name__}: {e}')
