from collections import Counter
from functools import lru_cache
import pandas as pd
import requests
import spacy

HEADERS={'User-Agent':'SemanticSEOResearchStudio/0.1 (research prototype)'}
@lru_cache(maxsize=1)
def model():
    try: return spacy.load('es_core_news_sm')
    except OSError as e: raise RuntimeError('Instala el modelo: python -m spacy download es_core_news_sm') from e

def wikipedia_texts(terms):
    results=[]
    for term in list(dict.fromkeys(terms))[:6]:
        try:
            r=requests.get('https://es.wikipedia.org/w/api.php',params={'action':'query','prop':'extracts','explaintext':1,'exintro':1,'redirects':1,'titles':term,'format':'json'},headers=HEADERS,timeout=15)
            r.raise_for_status()
            for p in r.json().get('query',{}).get('pages',{}).values():
                if p.get('extract') and 'missing' not in p: results.append({'titulo':p['title'],'texto':p['extract'],'url':'https://es.wikipedia.org/wiki/'+p['title'].replace(' ','_')})
        except (requests.RequestException,ValueError): pass
    return results

def analyze(documents):
    nlp=model(); ents=Counter(); concepts=Counter()
    for d in documents:
        doc=nlp(d['texto'][:120000])
        for e in doc.ents:
            if len(e.text.strip())>2: ents[(e.text.strip(),e.label_)]+=1
        for chunk in doc.noun_chunks:
            words=[t.lemma_.lower() for t in chunk if not t.is_stop and not t.is_punct]
            phrase=' '.join(words).strip()
            if len(phrase)>3 and len(words)<=6: concepts[phrase]+=1
    return (pd.DataFrame([{'entidad':k[0],'tipo':k[1],'frecuencia':v} for k,v in ents.most_common(150)]),pd.DataFrame([{'concepto':k,'frecuencia':v} for k,v in concepts.most_common(200)]))
