"""Búsqueda bibliográfica con filtro conservador. Nunca llama validado a un artículo sin leerlo."""
import re
import pandas as pd
import requests
from .demanda import norm
HEADERS={'User-Agent':'SemanticSEOResearchStudio/0.5 (research; github.com/yanizabelgalvang/semantic-seo-research-studio)'}
COLUMNS=['consulta','titulo','año','doi','openalex_id','tipo','tema','subcampo','campo','relevancia_metadatos','estado','motivo']
ACADEMIC={'article','review','book','book-chapter','preprint','dissertation','proceedings-article'}
GENERIC={'para','sobre','como','este','esta','entre','mexico','peru','web','internet','search','engine'}
COMMERCIAL=re.compile(r'\b(servicios? de|agencia|agencias|presupuesto|contratar|cotizaci[oó]n|mejor agencia|mallorca|valencia|precio de posicionamiento)\b',re.I)
def _tokens(s):return set(re.findall(r'[a-z]{3,}',norm(s)))-GENERIC

def score_work(work,topic,query):
    title=work.get('display_name') or ''
    primary=work.get('primary_topic') or {};sub=primary.get('subfield') or {};field=primary.get('field') or {}
    meta=' '.join([title,primary.get('display_name') or '',sub.get('display_name') or '',field.get('display_name') or ''])
    tokens=_tokens(topic);hits=len(tokens & _tokens(meta));score=hits/max(1,len(tokens))
    if not title:return 0,'descartado','sin_titulo'
    if COMMERCIAL.search(title):return score,'descartado','titulo_comercial_o_geografico_ajeno'
    if work.get('type') not in ACADEMIC:return score,'descartado','tipo_no_academico'
    if score==0:return score,'descartado','sin_coincidencia_tematica'
    if score<0.5:return score,'baja_pertinencia','coincidencia_parcial'
    return score,'candidato_revisar','metadatos_compatibles; lectura pendiente'

def search(queries,topic,max_works=15):
    rows=[];seen=set()
    for query in list(dict.fromkeys(queries))[:3]:
        try:
            resp=requests.get('https://api.openalex.org/works',params={'search':query,'per-page':max_works},headers=HEADERS,timeout=25)
            resp.raise_for_status()
            for w in resp.json().get('results',[]):
                oid=w.get('id','')
                if not oid or oid in seen:continue
                seen.add(oid);primary=w.get('primary_topic') or {}
                score,status,reason=score_work(w,topic,query)
                rows.append({'consulta':query,'titulo':w.get('display_name',''),'año':w.get('publication_year'),
                             'doi':w.get('doi') or '','openalex_id':oid,'tipo':w.get('type',''),
                             'tema':primary.get('display_name',''),'subcampo':(primary.get('subfield') or {}).get('display_name',''),
                             'campo':(primary.get('field') or {}).get('display_name',''),
                             'relevancia_metadatos':round(score,2),'estado':status,'motivo':reason})
        except (requests.RequestException,ValueError) as exc:
            rows.append({'consulta':query,'titulo':'','año':None,'doi':'','openalex_id':'','tipo':'','tema':'','subcampo':'','campo':'','relevancia_metadatos':0,'estado':'error_red','motivo':str(exc)[:100]})
    return pd.DataFrame(rows,columns=COLUMNS)
