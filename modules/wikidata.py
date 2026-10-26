import time
from functools import lru_cache
import pandas as pd
import requests
API='https://www.wikidata.org/w/api.php'
HEADERS={'User-Agent':'SemanticSEOResearchStudio/0.2 (research; https://github.com/yanizabelgalvang/semantic-seo-research-studio)','Accept':'application/json'}
@lru_cache(maxsize=128)
def _find(term):
    for attempt in range(3):
        try:
            r=requests.get(API,params={'action':'wbsearchentities','search':term,'language':'es','format':'json','limit':3},headers=HEADERS,timeout=15)
            if r.status_code==429:
                delay=r.headers.get('Retry-After','3');time.sleep(min(int(delay) if delay.isdigit() else 3,8)*(attempt+1));continue
            r.raise_for_status();return r.json().get('search',[]),'ok'
        except (requests.RequestException,ValueError) as exc:
            if attempt==2:return [],f'error_red: {str(exc)[:80]}'
    return [],'limitado_429'

def lookup(terms,max_terms=6):
    rows=[];seen=set()
    for term in terms:
        term=str(term).strip()
        if not term or term.lower() in seen:continue
        seen.add(term.lower())
        matches,status=_find(term)
        if status!='ok':rows.append({'termino':term,'qid_candidato':'','descripcion':'','estado':status});continue
        if not matches:rows.append({'termino':term,'qid_candidato':'','descripcion':'','estado':'sin_resultado'});continue
        for m in matches[:2]:
            rows.append({'termino':term,'qid_candidato':m.get('id',''),'descripcion':m.get('description',''),'estado':'candidato_no_verificado'})
        if len(seen)>=max_terms:break
        time.sleep(0.25)
    return pd.DataFrame(rows,columns=['termino','qid_candidato','descripcion','estado'])
