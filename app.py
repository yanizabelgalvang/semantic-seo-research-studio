import io,zipfile
import pandas as pd
import streamlit as st
from modules.demanda import load_semrush
from modules.spacy_nlp import wikipedia_texts,analyze
from modules.wikidata import lookup
from modules.openalex import search
from modules.facetas import summarize

COUNTRIES=['Perú','Colombia','México','Argentina','Chile','Bolivia','Ecuador','Uruguay','Paraguay','Venezuela','Costa Rica','Panamá','Guatemala','El Salvador','Honduras','Nicaragua','República Dominicana','Cuba']
st.set_page_config(page_title='Semantic SEO Research Studio',page_icon='🔎',layout='wide')
st.title('🔎 Semantic SEO Research Studio')
st.caption('Prototipo 0.2 · CSV Semrush · spaCy · Wikipedia contextual · Wikidata · OpenAlex')
st.warning('ACCESO NO PROTEGIDO: no subas datos confidenciales hasta implementar acceso privado. GitHub público no equivale a aplicación privada.')
with st.sidebar:
    topic=st.text_input('Tema','Posicionamiento web')
    country=st.selectbox('País objetivo',COUNTRIES,index=2)
    st.caption('Idioma de investigación: español. País del CSV confirmado por el usuario.')
files=st.file_uploader('CSV de Semrush (uno o varios)',type=['csv'],accept_multiple_files=True)
if files:
    try:
        df=load_semrush(files)
        st.success(f'{len(df)} keywords únicas de {len(files)} CSV')
        a,b,c=st.columns(3)
        a.metric('Keywords',len(df));b.metric('Con volumen positivo',int(df.volume.gt(0).sum()));c.metric('Volumen no disponible',int(df.volume.isna().sum()))
        st.dataframe(df,height=280)
        facets=summarize(df)
        st.subheader('Facetas × demanda (exploratorio)')
        st.caption('Agrupación basada en reglas. Los volúmenes sumados son descriptivos, NO tráfico potencial ni demanda incremental.')
        st.dataframe(facets)
        confirmed=st.checkbox(f'Confirmo que los CSV corresponden a {country}')
        if st.button('Investigar con NLP',disabled=not confirmed,type='primary'):
            with st.spinner('Buscando fuentes contextualizadas y procesando spaCy...'):
                docs=wikipedia_texts(topic)
                if not docs:
                    st.error('No se recuperaron fuentes de Wikipedia verificables. No se genera análisis NLP sin corpus. Revisa conectividad o prueba otro tema.')
                else:
                    ents,concepts=analyze(docs)
                    st.session_state.results={'keywords':df,'facetas':facets,'entities':ents,'concepts':concepts,'sources':pd.DataFrame([{'titulo':d['titulo'],'url':d['url']} for d in docs]),'topic':topic,'country':country,'wikidata':pd.DataFrame(),'openalex':pd.DataFrame()}
        if 'results' in st.session_state:
            r=st.session_state.results
            if r['topic']!=topic or r['country']!=country:
                st.info('El tema o país cambió. Ejecuta de nuevo la investigación para actualizar los resultados.')
            else:
                st.subheader('Fuentes seleccionadas y resultados NLP')
                st.dataframe(r['sources'])
                t1,t2=st.tabs(['Entidades spaCy (sin validar)','Sintagmas nominales'])
                with t1:st.dataframe(r['entities'])
                with t2:st.dataframe(r['concepts'])
                if st.button('Consultar Wikidata y OpenAlex (opcional)'):
                    with st.spinner('Consultando fuentes abiertas con límites de peticiones...'):
                        # Consultas contextualizadas, no términos NER aislados como "Seo".
                        seed=['posicionamiento en buscadores','optimización de motores de búsqueda','Google'] if 'seo' in topic.lower() or 'posicionamiento' in topic.lower() else [topic]
                        r['wikidata']=lookup(seed,max_terms=3)
                        r['openalex']=search([f'"{topic}"',f'{topic} search engines'])
                if not r['wikidata'].empty:st.subheader('Wikidata · candidatos sin verificar');st.dataframe(r['wikidata'])
                if not r['openalex'].empty:st.subheader('OpenAlex · literatura por revisar');st.dataframe(r['openalex'])
                def md_table(key):
                    table=r[key]
                    return table.head(30).to_markdown(index=False) if not table.empty else 'Sin resultados / no ejecutado'
                report=(f"# Investigación exploratoria: {topic}\n\nPaís: {country}. Fuente de demanda: CSV Semrush.\n\n"
                        f"## Keywords\n\n{md_table('keywords')}\n\n## Facetas × demanda (reglas exploratorias)\n\n{md_table('facetas')}\n\n"
                        f"## Corpus validado por contexto\n\n{md_table('sources')}\n\n## Entidades spaCy (no verificadas)\n\n{md_table('entities')}\n\n"
                        f"## Conceptos spaCy\n\n{md_table('concepts')}\n\n## Wikidata (QIDs candidatos)\n\n{md_table('wikidata')}\n\n"
                        f"## OpenAlex (obras por revisar)\n\n{md_table('openalex')}\n\n## Limitaciones\n\n"
                        "Prototipo: sin SERP verificada ni clustering por similitud de SERP. Las facetas son reglas iniciales; los QIDs y estudios requieren revisión. Volumen no es tráfico potencial.\n")
                st.download_button('Descargar informe Markdown',report.encode('utf-8'),'research.md','text/markdown')
                out=io.BytesIO()
                with zipfile.ZipFile(out,'w',zipfile.ZIP_DEFLATED) as z:
                    z.writestr('research.md',report)
                    for key in ('keywords','facetas','entities','concepts','sources','wikidata','openalex'):
                        z.writestr(f'{key}.csv',r[key].to_csv(index=False))
                st.download_button('Descargar ZIP de resultados',out.getvalue(),'semantic_research_v02.zip','application/zip')
    except Exception as exc:
        st.error(f'Error al procesar CSV o ejecutar investigación: {exc}')
