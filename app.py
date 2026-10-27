import io,zipfile,hashlib
import pandas as pd
import streamlit as st
from modules.demanda import load_semrush
from modules.facetas import build
from modules.spacy_nlp import wikipedia_texts,analyze
from modules.wikidata import lookup
from modules.openalex import search

COUNTRIES=['Perú','Colombia','México','Argentina','Chile','Bolivia','Ecuador','Uruguay','Paraguay','Venezuela','Costa Rica','Panamá','Guatemala','El Salvador','Honduras','Nicaragua','República Dominicana','Cuba']
st.set_page_config(page_title='Semantic SEO Research Studio',page_icon='🔎',layout='wide')
st.title('🔎 Semantic SEO Research Studio')
st.caption('Investigación exploratoria · Semrush CSV · spaCy · Wikipedia · Wikidata · OpenAlex')
st.error('ACCESO NO PROTEGIDO: esta aplicación no implementa autenticación. No subas datos confidenciales ni la compartas como aplicación privada.')
with st.sidebar:
    topic=st.text_input('Tema','Posicionamiento web')
    country=st.selectbox('País objetivo',COUNTRIES,index=2)
    st.caption('Idioma: español. Las métricas provienen exclusivamente de CSV Semrush.')
files=st.file_uploader('CSV Semrush (uno o varios)',type=['csv'],accept_multiple_files=True)
if files:
    try:
        df=load_semrush(files)
        st.success(f'{len(df)} keywords únicas importadas')
        a,b,c,d=st.columns(4)
        a.metric('Keywords',len(df));b.metric('Volumen positivo',int(df.volume.gt(0).sum()));c.metric('Volumen 0',int(df.volume.eq(0).sum()));d.metric('Sin dato',int(df.volume.isna().sum()))
        st.dataframe(df,height=250,use_container_width=True)
        detail,facets=build(df,topic)
        st.subheader('Grupos de consultas × demanda (exploratorios)')
        st.info('Agrupación heurística por necesidad expresada. No es clustering validado por SERP. «Intención por verificar» conserva las consultas ambiguas sin forzarlas. Los volúmenes sumados son descriptivos, NO tráfico potencial.')
        st.dataframe(facets,use_container_width=True)
        pending=int(detail['grupo'].eq('Intención por verificar').sum())
        if pending: st.warning(f'{pending} consultas requieren revisión de intención; no se asignan automáticamente a un cluster editorial.')
        st.download_button('Descargar clasificación provisional',detail.to_csv(index=False).encode('utf-8-sig'),'keywords_clasificadas.csv','text/csv')
        confirmed=st.checkbox(f'Confirmo que estos CSV corresponden a {country}')
        fingerprint=hashlib.sha256((topic+country+''.join(f.name+hashlib.sha256(f.getvalue()).hexdigest() for f in files)).encode()).hexdigest()
        if st.button('Investigar con NLP',disabled=not confirmed,type='primary'):
            with st.spinner('Buscando artículos de Wikipedia y ejecutando spaCy...'):
                docs,rejected=wikipedia_texts(topic)
                if not docs:st.error('No se obtuvo un corpus pertinente de Wikipedia. No se simularán entidades. Prueba una semilla más general o revisa conectividad.')
                else:
                    ents,concepts=analyze(docs,topic)
                    st.session_state['research']={'fingerprint':fingerprint,'topic':topic,'country':country,'keywords':df,'facetas':facets,'clasificacion':detail,'entities':ents,'concepts':concepts,'sources':pd.DataFrame([{'titulo':d['titulo'],'url':d['url'],'coincidencias':d['coincidencias']} for d in docs]),'wikidata':pd.DataFrame(),'openalex':pd.DataFrame(),'rejected':pd.DataFrame(rejected,columns=['titulo','motivo'])}
        r=st.session_state.get('research')
        if r and r['fingerprint']==fingerprint:
            st.subheader('Fuentes y análisis lingüístico')
            st.dataframe(r['sources'],use_container_width=True)
            with st.expander('Fuentes rechazadas y motivos'):st.dataframe(r['rejected'])
            t1,t2=st.tabs(['Entidades sin verificar','Sintagmas nominales'])
            with t1:st.dataframe(r['entities'],use_container_width=True)
            with t2:st.dataframe(r['concepts'],use_container_width=True)
            if st.button('Consultar Wikidata y OpenAlex'):
                with st.spinner('Consultando fuentes abiertas...'):
                    # No enviar NER bruto a Wikidata: consultas explícitas relacionadas con el tema.
                    terms=[topic]+r['sources'].titulo.head(3).tolist()
                    r['wikidata']=lookup(terms,topic)
                    r['openalex']=search([topic,f'{topic} motores de búsqueda',f'{topic} marketing digital'],topic)
            if not r['wikidata'].empty:
                st.subheader('Wikidata: candidatos por revisar');st.warning('Los QID son candidatos, no verificaciones definitivas. Los descartados por contexto no deben usarse como entidades.');st.dataframe(r['wikidata'])
            if not r['openalex'].empty:
                st.subheader('OpenAlex: candidatos y exclusiones');st.caption('Filtrado inicial por metadatos; no confirma calidad científica ni relevancia editorial.');st.dataframe(r['openalex'])
            def table(name,n=30):
                frame=r[name];return frame.head(n).to_markdown(index=False) if not frame.empty else 'No ejecutado / sin datos'
            report=(f'# Investigación exploratoria: {topic}\n\nMercado: {country} · Idioma: español · Demanda: CSV Semrush\n\n'
                    f'## Keywords\n\n{table("keywords")}\n\n## Facetas provisionales\n\n{table("facetas")}\n\n'
                    f'## Fuentes Wikipedia\n\n{table("sources")}\n\n## Entidades spaCy (sin validar)\n\n{table("entities")}\n\n'
                    f'## Conceptos spaCy\n\n{table("concepts")}\n\n## Wikidata (candidatos)\n\n{table("wikidata")}\n\n'
                    f'## OpenAlex (metadatos por revisar)\n\n{table("openalex")}\n\n'
                    '## Limitaciones\n\nSin SERP real ni análisis de competidores. Los QIDs no están verificados. Los grupos TF-IDF son exploratorios, no facetas ni clusters SEO definitivos. Las publicaciones no están validadas académicamente. Volumen no equivale a tráfico potencial.\n')
            st.download_button('Descargar informe',report.encode('utf-8'),'research.md','text/markdown')
            bundle=io.BytesIO()
            with zipfile.ZipFile(bundle,'w',zipfile.ZIP_DEFLATED) as z:
                z.writestr('research.md',report)
                for name in ('keywords','facetas','clasificacion','sources','rejected','entities','concepts','wikidata','openalex'):
                    z.writestr(name+'.csv',r[name].to_csv(index=False))
            st.download_button('Descargar ZIP',bundle.getvalue(),'semantic_research.zip','application/zip')
        elif r:st.info('El tema, país o los CSV cambiaron. Vuelve a ejecutar la investigación.')
    except Exception as exc:
        st.error(f'No se pudo procesar: {exc}')
