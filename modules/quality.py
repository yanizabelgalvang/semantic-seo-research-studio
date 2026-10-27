"""Control de fuentes y verificación conservadora: no convierte candidatos en hechos."""
import re
import pandas as pd
from .demanda import norm

UNRELATED={'anillo web','posicionamiento','seo de urgel','la seo','web scraping'}
BAD_ENTITY={'usualmente estan','dando','fueron muy populares','luego de la aprobacion','de alli','competidores','alguno','el objetivo de los anillos web'}

def curate_sources(sources,topic):
    out=sources.copy()
    if out.empty:return out
    topic_tokens={w for w in norm(topic).split() if len(w)>3}
    def state(row):
        title=norm(row.get('titulo',''))
        if title in UNRELATED:return 'excluir_ambiguedad'
        if 'seo' in topic_tokens or 'posicionamiento' in topic_tokens:
            if title in {'posicionamiento en buscadores','optimizacion en motores de busqueda'}:return 'pertinente'
        return 'revisar_contexto'
    out['revision_tematica']=out.apply(state,axis=1)
    return out

def curate_entities(entities):
    if entities.empty:return entities
    out=entities.copy()
    def ok(s):
        n=norm(s)
        return n not in BAD_ENTITY and not re.match(r'^(segun|tambien|dando|usualmente|luego de|el objetivo|la lista|de alli)\b',n) and len(n)>=3
    out['revision_nlp']=out['entidad'].map(lambda x:'candidato' if ok(x) else 'descartar_ruido')
    return out

def cross_facets(facets,competitors):
    """Facetas existentes frente a corpus de competidores: indicio, no validación SERP."""
    out=facets.copy()
    if out.empty:return out
    texts=' '.join(competitors.loc[competitors.estado.eq('contenido_recuperado'),'texto'].fillna('').astype(str)).casefold() if not competitors.empty else ''
    out['competidores_recuperados']=int(competitors.estado.eq('contenido_recuperado').sum()) if not competitors.empty else 0
    out['evidencia_competitiva']='insuficiente' if not texts else 'corpus_disponible_requiere_revision'
    return out

def research_status(serp,competitors,wikidata,openalex):
    return {'serp':'aportada_sin_verificacion_independiente' if not serp.empty else 'no_aportada',
            'competidores':int(competitors.estado.eq('contenido_recuperado').sum()) if not competitors.empty else 0,
            'wikidata':'candidatos_no_verificados' if not wikidata.empty else 'sin_ejecutar',
            'openalex':'metadatos_pendientes_de_lectura' if not openalex.empty else 'sin_ejecutar'}
