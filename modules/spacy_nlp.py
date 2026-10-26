from collections import Counter
from functools import lru_cache
import re, time
import pandas as pd
import requests
import spacy

API='https://es.wikipedia.org/w/api.php'
HEADERS={'User-Agent':'SemanticSEOResearchStudio/0.2 (educational research; contact: https://github.com/yanizabelgalvang/semantic-seo-research-studio)','Accept':'application/json'}
SEO_WORDS={'seo','posicionamiento web','posicionamiento en buscadores','optimización de motores de búsqueda','marketing digital','search engine optimization'}
SEO_BAD={'catedral','zaragoza','seo de urgel','ornitología','birdlife','apellido','aragon','aragón','cataluña','lerida','lérida','la seo'}
@lru_cache(maxsize=1)
def model():
    try: return spacy.load('es_core_news_sm')
    except OSError as exc: raise RuntimeError('Falta el modelo es_core_news_sm. Revisa requirements.txt y los logs de instalación.') from exc

def _request(params):
    for attempt in range(3):
        try:
            r=requests.get(API,params={**params,'format':'json','formatversion':2},headers=HEADERS,timeout=18)
            if r.status_code in (429,500,502,503):
                time.sleep(min(int(r.headers.get('Retry-After','2')) if r.headers.get('Retry-After','2').isdigit() else 2,5)*(attempt+1));continue
            r.raise_for_status();return r.json()
        except (requests.RequestException,ValueError):
            if attempt==2:return {}
    return {}

def wikipedia_texts(topic, max_pages=5):
    """Búsqueda contextual: nunca usar SEO aislado como página enciclopédica."""
    t=topic.strip().lower()
    is_seo=any(x in t for x in ('seo','posicionamiento web','posicionamiento en buscadores'))
    queries=(["intitle:Posicionamiento en buscadores",'"optimización en motores de búsqueda"', '"marketing en buscadores"'] if is_seo else [topic, f'"{topic}"'])
    candidates=['Posicionamiento en buscadores','Mercadotecnia en motores de búsqueda','Mercadotecnia digital'] if is_seo else []
    for q in queries:
        data=_request({'action':'query','list':'search','srsearch':q,'srlimit':5,'srnamespace':0})
        candidates.extend(x.get('title','') for x in data.get('query',{}).get('search',[]))
    results=[];seen=set()
    for title in candidates:
        if not title or title.lower() in seen:continue
        seen.add(title.lower())
        if is_seo and (any(b in title.lower() for b in SEO_BAD) or title.strip().lower()=='seo'):continue
        data=_request({'action':'query','prop':'extracts|pageprops','explaintext':1,'exintro':1,'redirects':1,'titles':title})
        for p in data.get('query',{}).get('pages',[]):
            body=p.get('extract','');name=p.get('title','')
            if p.get('missing') or 'disambiguation' in p.get('pageprops',{}) or len(body)<180:continue
            if is_seo:
                context=(name+' '+body[:2000]).lower()
                if any(b in name.lower() for b in SEO_BAD):continue
                if not any(x in context for x in ('buscador','motores de búsqueda','optimización','marketing digital','search engine')):continue
            results.append({'titulo':name,'texto':body,'url':'https://es.wikipedia.org/wiki/'+name.replace(' ','_'),'fuente':'Wikipedia (selección contextual)'})
            if len(results)>=max_pages:return results
    return results

def analyze(documents):
    nlp=model();entities=Counter();concepts=Counter()
    for d in documents:
        doc=nlp(d['texto'][:100000])
        for ent in doc.ents:
            value=re.sub(r'\s+',' ',ent.text).strip()
            if len(value)<3 or any(b in value.lower() for b in SEO_BAD):continue
            if value.lower()=='seo' and ent.label_=='LOC':continue
            entities[(value,ent.label_)]+=1
        for ch in doc.noun_chunks:
            words=[w.lemma_.lower() for w in ch if not w.is_stop and not w.is_punct and w.pos_ in ('NOUN','PROPN','ADJ')]
            val=' '.join(words).strip()
            if len(val)<4 or len(words)>6 or any(b in val for b in SEO_BAD):continue
            concepts[val]+=1
    return (pd.DataFrame([{'entidad':k[0],'tipo':k[1],'frecuencia':v} for k,v in entities.most_common(150)],columns=['entidad','tipo','frecuencia']),pd.DataFrame([{'concepto':k,'frecuencia':v} for k,v in concepts.most_common(200)],columns=['concepto','frecuencia']))
