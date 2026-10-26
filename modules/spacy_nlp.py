import re,time,unicodedata
from collections import Counter
from functools import lru_cache
from urllib.parse import quote
import pandas as pd
import requests
import spacy
from .demanda import norm
API='https://es.wikipedia.org/w/api.php'
HEADERS={'User-Agent':'SemanticSEOResearchStudio/0.3 (research; https://github.com/yanizabelgalvang/semantic-seo-research-studio)'}
@lru_cache(maxsize=1)
def model():return spacy.load('es_core_news_sm')

def _api(params):
    for i in range(3):
        try:
            r=requests.get(API,params={**params,'format':'json','formatversion':2},headers=HEADERS,timeout=20)
            if r.status_code in (429,503):time.sleep(min(2**i,4));continue
            r.raise_for_status();return r.json(),''
        except (requests.RequestException,ValueError) as e:
            if i==2:return {},str(e)
    return {},'Servicio no disponible'

def wikipedia_texts(topic,max_pages=6):
    """Wikipedia es un corpus complementario; requiere coincidencia temática explícita."""
    search,err=_api({'action':'query','list':'search','srsearch':topic,'srlimit':15,'srnamespace':0})
    if err:return [],[f'Wikipedia: {err}']
    seed=set(norm(topic).split());seed={x for x in seed if len(x)>3 and x not in ('para','sobre','mexico','peru')}
    terms={x for x in seed}
    if 'seo' in norm(topic) or 'posicionamiento web' in norm(topic):terms.update(('buscadores','busqueda','optimizacion','marketing','posicionamiento'))
    results=[];rejected=[]
    for hit in search.get('query',{}).get('search',[]):
        title=hit.get('title','')
        if not title:continue
        title_norm=norm(title)
        if title_norm in ('seo','la seo') or 'desambiguacion' in title_norm:rejected.append((title,'ambiguo'));continue
        data,fetch_err=_api({'action':'query','prop':'extracts|pageprops','explaintext':1,'exintro':1,'redirects':1,'titles':title})
        if fetch_err:rejected.append((title,'error_red'));continue
        for page in data.get('query',{}).get('pages',[]):
            body=page.get('extract','');name=page.get('title','')
            if len(body)<200 or 'disambiguation' in page.get('pageprops',{}):rejected.append((name,'poco_texto_o_desambiguacion'));continue
            context=norm(name+' '+body[:2000]);matched=sum(1 for x in terms if re.search(r'\b'+re.escape(x)+r'\b',context))
            if matched<2:rejected.append((name,'contexto_insuficiente'));continue
            results.append({'titulo':name,'texto':body,'url':'https://es.wikipedia.org/wiki/'+quote(name.replace(' ','_')),'coincidencias':matched,'fuente':'Wikipedia'})
            if len(results)>=max_pages:break
        if len(results)>=max_pages:break
    return results,rejected

def analyze(documents,topic):
    nlp=model();ent=Counter();con=Counter();seed=set(norm(topic).split())
    for source in documents:
        doc=nlp(source['texto'][:80000]);source_text=norm(source['texto'][:2000])
        for e in doc.ents:
            value=e.text.strip(' \t\n.,;:()[]"\'')
            if len(value)<3 or not any(c.isalpha() for c in value):continue
            if value[0].islower() and len(value.split())==1 and e.label_ in ('PER','LOC'):continue
            ent[(value,e.label_)]+=1
        for chunk in doc.noun_chunks:
            parts=[norm(t.lemma_) for t in chunk if t.pos_ in ('NOUN','PROPN','ADJ') and not t.is_stop and not t.is_punct]
            phrase=' '.join(parts).strip()
            if 4<=len(phrase)<=65 and len(parts)<=5:con[phrase]+=1
    ents=pd.DataFrame([{'entidad':k[0],'tipo_spacy':k[1],'frecuencia':v,'estado':'sin_validar'} for k,v in ent.most_common(150)])
    concepts=pd.DataFrame([{'concepto':k,'frecuencia':v} for k,v in con.most_common(200)])
    return ents,concepts
