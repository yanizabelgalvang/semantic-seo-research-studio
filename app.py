import io, zipfile
import pandas as pd
import streamlit as st
from modules.demanda import load_semrush
from modules.spacy_nlp import wikipedia_texts, analyze
from modules.wikidata import lookup
from modules.openalex import search

COUNTRIES=['Perú','Colombia','México','Argentina','Chile','Bolivia','Ecuador','Uruguay','Paraguay','Venezuela','Costa Rica','Panamá','Guatemala','El Salvador','Honduras','Nicaragua','República Dominicana','Cuba']
st.set_page_config(page_title='Semantic SEO Research Studio',page_icon='🔎',layout='wide')
st.title('🔎 Semantic SEO Research Studio')
st.caption('Prototipo 0.1 · CSV manual de Semrush · Python + spaCy · Wikipedia · Wikidata · OpenAlex')
st.error('SIN AUTENTICACIÓN: no desplegar públicamente ni cargar datos confidenciales hasta configurar acceso privado.')
with st.sidebar:
    topic=st.text_input('Tema','Comprar USDT en Perú')
    country=st.selectbox('País objetivo',COUNTRIES)
    st.caption('Idioma: español. Confirma que los CSV corresponden al país seleccionado.')
files=st.file_uploader('CSV de Semrush (uno o varios)',type=['csv'],accept_multiple_files=True)
if files:
    try:
        df=load_semrush(files)
        st.success(f'{len(df)} keywords únicas desde {len(files)} CSV')
        c1,c2,c3=st.columns(3)
        c1.metric('Keywords',len(df));c2.metric('Volumen positivo',int(df.volume.gt(0).sum()));c3.metric('Sin volumen disponible',int(df.volume.isna().sum()))
        st.dataframe(df,use_container_width=True,height=300)
        st.download_button('Descargar keywords normalizadas',df.to_csv(index=False).encode('utf-8-sig'),'keywords.csv','text/csv')
        confirmed=st.checkbox(f'Confirmo que mis exportaciones corresponden a {country}')
        if st.button('Investigar con NLP',disabled=not confirmed,type='primary'):
            with st.spinner('Procesando fuentes abiertas...'):
                terms=[topic]+df.keyword.head(5).tolist()
                docs=wikipedia_texts(terms)
                if not docs: st.warning('Wikipedia no devolvió artículos. Prueba otra semilla o comprueba la conexión.')
                else:
                    ents,concepts=analyze(docs)
                    wikidata=lookup(ents['entidad'].head(12).tolist() if not ents.empty else [topic])
                    papers=search([topic,f'cryptocurrency {country}',f'{topic} adoption'])
                    st.session_state.results={'keywords':df,'entities':ents,'concepts':concepts,'wikidata':wikidata,'openalex':papers,'sources':pd.DataFrame([{'titulo':d['titulo'],'url':d['url']} for d in docs]),'topic':topic,'country':country}
    except Exception as e: st.error(f'No se pudo procesar: {e}')
if 'results' in st.session_state:
    r=st.session_state.results
    st.subheader('Resultados')
    st.info('Wikidata: QIDs candidatos, aún no desambiguados. OpenAlex: obras encontradas, no verificadas. Este prototipo no realiza análisis SERP ni arquitectura editorial.')
    tabs=st.tabs(['Entidades','Sintagmas nominales','Wikidata','OpenAlex','Fuentes'])
    for tab,key in zip(tabs,['entities','concepts','wikidata','openalex','sources']):
        with tab: st.dataframe(r[key],use_container_width=True)
    report=f"# Investigación: {r['topic']}\n\nPaís: {r['country']} · idioma: español\n\nFuente de demanda: CSV manual Semrush.\n\n## Keywords\n\n{r['keywords'].head(30).to_markdown(index=False)}\n\n## Entidades NLP\n\n{r['entities'].head(30).to_markdown(index=False) if not r['entities'].empty else 'Sin resultados'}\n\n## Conceptos NLP\n\n{r['concepts'].head(30).to_markdown(index=False) if not r['concepts'].empty else 'Sin resultados'}\n\n## Limitaciones\n\nPrototipo exploratorio: no valida QIDs, no analiza SERP, no asigna URLs ni realiza clustering editorial.\n"
    st.download_button('Descargar informe Markdown',report.encode('utf-8'),'research.md','text/markdown')
    output=io.BytesIO()
    with zipfile.ZipFile(output,'w',zipfile.ZIP_DEFLATED) as z:
        z.writestr('research.md',report)
        for key in ['keywords','entities','concepts','wikidata','openalex','sources']:
            z.writestr(f'{key}.csv',r[key].to_csv(index=False))
    st.download_button('Descargar paquete ZIP',output.getvalue(),'semantic_research.zip','application/zip')
