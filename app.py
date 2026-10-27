import io,zipfile,hashlib,json
import pandas as pd
import streamlit as st
from modules.demanda import load_semrush
from modules.facetas import build
from modules.spacy_nlp import wikipedia_texts,analyze
from modules.wikidata import lookup
from modules.openalex import search
from modules.competidores import read_serp_csv,fetch_competitors
from modules.quality import curate_sources,curate_entities
COUNTRIES=['Perú','Colombia','México','Argentina','Chile','Bolivia','Ecuador','Uruguay','Paraguay','Venezuela','Costa Rica','Panamá','Guatemala','El Salvador','Honduras','Nicaragua','República Dominicana','Cuba']
st.set_page_config(page_title='Semantic SEO Research Studio',page_icon='🔎',layout='wide')
st.title('🔎 Semantic SEO Research Studio')
st.caption('Demanda Semrush → corpus Wikipedia → spaCy → Wikidata → OpenAlex → facetas × demanda')
st.error('ACCESO NO PROTEGIDO. No cargues datos privados: esta versión aún no tiene autenticación de Google.')
with st.sidebar:
    topic=st.text_input('Tema principal','Posicionamiento web')
    country=st.selectbox('País objetivo',COUNTRIES,index=2)
    st.caption('Idioma de investigación: español')
files=st.file_uploader('CSV de Semrush (uno o varios)',type='csv',accept_multiple_files=True)
with st.expander('Opcional: SERP y competidores (NO es requisito del método principal)'):
    serp_file=st.file_uploader('CSV SERP Semrush (opcional)',type='csv')
    use_competitors=st.checkbox('Analizar hasta 5 páginas competidoras',value=False,disabled=serp_file is None)
if files:
    try:
        df=load_semrush(files)
        st.subheader('1. Demanda de búsqueda · Semrush')
        a,b,c=st.columns(3)
        a.metric('Keywords',len(df));b.metric('Con volumen positivo',int(df.volume.gt(0).sum()));c.metric('Sin volumen',int(df.volume.isna().sum()))
        st.dataframe(df.head(200),use_container_width=True,hide_index=True)
        detail,facets=build(df,topic)
        # Preserve raw data, but do not present unrelated terms as recommendations.
        relevant=detail[detail.relevancia_semilla.eq('coincidencia_lexica')].copy()
        excluded=detail[detail.relevancia_semilla.ne('coincidencia_lexica')].copy()
        st.caption(f'{len(relevant)} consultas con relación léxica al tema; {len(excluded)} requieren revisión. La coincidencia léxica no demuestra intención ni pertinencia final.')
        st.subheader('2. Facetas × demanda · hipótesis')
        st.info('Los grupos describen necesidades expresadas; NO son clusters SEO ni recomendaciones automáticas de URLs. El volumen agregado NO es tráfico potencial.')
        st.dataframe(facets,use_container_width=True,hide_index=True)
        with st.expander('Keywords que requieren revisión'):st.dataframe(excluded.head(250),hide_index=True)
        st.download_button('Descargar keywords completas',df.to_csv(index=False).encode('utf-8-sig'),'keywords.csv')
        confirmed=st.checkbox(f'Confirmo que los CSV corresponden a {country}')
        key=hashlib.sha256((topic+country+''.join(f.name+hashlib.sha256(f.getvalue()).hexdigest() for f in files)+(hashlib.sha256(serp_file.getvalue()).hexdigest() if serp_file else '')+str(use_competitors)).encode()).hexdigest()
        if st.button('Ejecutar investigación semántica',disabled=not confirmed,type='primary'):
            with st.spinner('Consultando Wikipedia y procesando con spaCy...'):
                docs,rejected=wikipedia_texts(topic)
                if not docs:st.error('No se obtuvo corpus pertinente. No se inventarán entidades.')
                else:
                    ents,concepts=analyze(docs,topic)
                    ents=curate_entities(ents)
                    sources=curate_sources(pd.DataFrame([{'titulo':d['titulo'],'url':d['url'],'coincidencias':d['coincidencias']} for d in docs]),topic)
                    serp=read_serp_csv(serp_file) if serp_file else pd.DataFrame()
                    competitors=fetch_competitors(serp) if use_competitors and not serp.empty else pd.DataFrame()
                    st.session_state['run']={'key':key,'topic':topic,'country':country,'keywords':df,'facetas':facets,'clasificacion':detail,'relevant':relevant,'sources':sources,'rejected':pd.DataFrame(rejected,columns=['titulo','motivo']),'entities':ents,'concepts':concepts,'serp':serp,'competidores':competitors,'wikidata':pd.DataFrame(),'openalex':pd.DataFrame()}
        r=st.session_state.get('run')
        if r and r['key']==key:
            st.subheader('3. Corpus conceptual y NLP')
            st.dataframe(r['sources'],use_container_width=True,hide_index=True)
            with st.expander('Fuentes excluidas'):st.dataframe(r['rejected'],hide_index=True)
            t1,t2=st.tabs(['Entidades candidatas','Conceptos y sintagmas'])
            with t1:st.dataframe(r['entities'],hide_index=True)
            with t2:st.dataframe(r['concepts'],hide_index=True)
            if st.button('Consultar Wikidata y OpenAlex'):
                with st.spinner('Consultando fuentes abiertas...'):
                    terms=[topic]+r['sources'].titulo.head(3).tolist()
                    r['wikidata']=lookup(terms,topic)
                    r['openalex']=search([topic,f'{topic} motores de búsqueda',f'{topic} marketing digital'],topic)
            if not r['wikidata'].empty:
                st.subheader('4. Wikidata · candidatos')
                st.dataframe(r['wikidata'],hide_index=True)
                st.warning('Un QID recuperado no equivale a entidad verificada. Revisa las descripciones y los estados.')
            if not r['openalex'].empty:
                st.subheader('5. OpenAlex · literatura candidata')
                st.dataframe(r['openalex'].drop(columns=['abstract'],errors='ignore'),hide_index=True)
                st.warning('Metadatos ≠ lectura y validación académica. Solo usar trabajos revisados como evidencia.')
            if not r['serp'].empty:
                st.subheader('Anexo opcional · SERP aportada')
                st.dataframe(r['serp'].drop(columns=['texto'],errors='ignore').head(30),hide_index=True)
                if not r['competidores'].empty:st.dataframe(r['competidores'].drop(columns=['texto'],errors='ignore').head(5),hide_index=True)
            def brief(name,n=12):
                x=r[name]
                return x.head(n).to_markdown(index=False) if not x.empty else '_No disponible o no ejecutado._'
            report=f"""# Investigación semántica: {topic}\n\n**Mercado:** {country} · **Idioma:** español · **Demanda:** CSV Semrush\n\n## Resumen de cobertura\n- Keywords importadas: {len(df)}\n- Keywords relacionadas léxicamente: {len(relevant)} (no validadas por SERP)\n- Fuentes Wikipedia aceptadas: {len(r['sources'])}\n- Entidades NLP candidatas: {len(r['entities'])}\n- Conceptos lingüísticos: {len(r['concepts'])}\n\n## Demanda relevante (muestra)\n{brief('relevant',20)}\n\n## Facetas × demanda (hipótesis)\n{brief('facetas',20)}\n\n## Corpus Wikipedia\n{brief('sources',20)}\n\n## Conceptos NLP\n{brief('concepts',25)}\n\n## Wikidata: candidatos, no verificaciones\n{brief('wikidata',15)}\n\n## OpenAlex: candidatos académicos\n{brief('openalex',15)}\n\n## SERP opcional\n{brief('serp',10)}\n\n## Limitaciones y siguiente etapa\nLa SERP y el análisis de competidores son **opcionales**. Los grupos son hipótesis semánticas, no clusters definitivos ni decisiones de URL. Los QIDs no se consideran verificados automáticamente. OpenAlex aporta candidatos cuya evidencia requiere lectura. El volumen de búsqueda no equivale a tráfico potencial.\n"""
            st.subheader('6. Informe ejecutivo')
            st.markdown('El informe muestra resúmenes; los datos completos se conservan en el ZIP técnico.')
            st.download_button('Descargar informe legible',report.encode(),'semantic_report.md','text/markdown')
            buf=io.BytesIO()
            with zipfile.ZipFile(buf,'w',zipfile.ZIP_DEFLATED) as z:
                z.writestr('semantic_report.md',report)
                for name in ('keywords','facetas','clasificacion','sources','rejected','entities','concepts','serp','competidores','wikidata','openalex'):
                    z.writestr(name+'.csv',r[name].drop(columns=['texto'],errors='ignore').to_csv(index=False))
            st.download_button('Descargar respaldo técnico',buf.getvalue(),'semantic_research.zip','application/zip')
        elif r:st.info('Cambió el tema, el país o los archivos. Ejecuta una investigación nueva.')
    except Exception as e:
        st.error(f'Error de procesamiento: {type(e).__name__}: {e}')
