import re,time
from functools import lru_cache
import pandas as pd
import requests
from .demanda import norm
API='https://www.wikidata.org/w/api.php'
HEADERS={'User-Agent':'SemanticSEOResearchStudio/0.3 (research; https://github.com/yanizabelgalvang/semantic-seo-research-studio)'}
@lru_cache(maxsize=256)
def _search(term):
    for i in range(3):
        try:
            r=requests.get(API,params={'action':'wbsearchentities','search':term,'language':'es','format':'json','limit':5},headers=HEADERS,timeout=15)
            if r.status_code==429:
                delay=r.headers.get('Retry-After','2');time.sleep(min(int(delay) if delay.isdigit() else 2,6));continue
            r.raise_for_status();return r.json().get('search',[]),'ok'
        except (requests.RequestException,ValueError) as exc:
            if i==2:return [],'error_red: '+str(exc)[:90]
    return [],'limitado_429'

def lookup(terms,topic,max_terms=8):
    """Candidatos, nunca QIDs verificados automáticamente solo por nombre."""
    rows=[];seen=set()
    for term in terms:
        term=str(term).strip()
        if not term or norm(term) in seen:continue
        seen.add(norm(term));items,status=_search(term)
        if status!='ok' or not items:
            rows.append({'termino':term,'qid_candidato':'','descripcion':'','estado':status if status!='ok' else 'sin_resultado'});continue
        for item in items[:3]:
            rows.append({'termino':term,'qid_candidato':item.get('id',''),'descripcion':item.get('description',''),'estado':'candidato_pendiente_de_revision'})
        if len(seen)>=max_terms:break
        time.sleep(.15)
    return pd.DataFrame(rows,columns=['termino','qid_candidato','descripcion','estado'])
