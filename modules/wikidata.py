"""Candidatos Wikidata con evidencia contextual; no se certifican QIDs por coincidencia léxica."""
import time
from functools import lru_cache
import pandas as pd
import requests
from .demanda import norm
API='https://www.wikidata.org/w/api.php'
HEADERS={'User-Agent':'SemanticSEOResearchStudio/0.4 (educational research; github.com/yanizabelgalvang/semantic-seo-research-studio)'}
@lru_cache(maxsize=256)
def _search(term):
    for attempt in range(4):
        try:
            r=requests.get(API,params={'action':'wbsearchentities','search':term,'language':'es','format':'json','limit':5},headers=HEADERS,timeout=20)
            if r.status_code in (429,503):
                retry=r.headers.get('Retry-After','2')
                time.sleep(min(int(retry) if retry.isdigit() else 2**attempt,12));continue
            r.raise_for_status();return r.json().get('search',[]),'ok'
        except (requests.RequestException,ValueError) as exc:
            if attempt==3:return [],'error_red: '+str(exc)[:100]
            time.sleep(min(2**attempt,5))
    return [],'limitado_429'

def lookup(terms,topic,max_terms=8):
    rows=[];seen=set()
    context=set(norm(topic).split())
    for term in terms:
        term=str(term).strip()
        if not term or norm(term) in seen:continue
        seen.add(norm(term));items,status=_search(term)
        if status!='ok' or not items:
            rows.append({'termino':term,'qid_candidato':'','descripcion':'','coincidencia_contexto':0,'estado':status if status!='ok' else 'sin_resultado'});continue
        for item in items[:4]:
            desc=item.get('description','') or ''
            label=item.get('label','') or ''
            label_match=int(norm(label)==norm(term))
            overlap=len(context & set(norm(desc).split()))
            # Es solo una ayuda para revisión, nunca validación automática.
            score=label_match+overlap
            rows.append({'termino':term,'qid_candidato':item.get('id',''),'descripcion':desc,
                         'coincidencia_contexto':score,'estado':'candidato_contextual' if score>=2 else 'candidato_ambiguo'})
        if len(seen)>=max_terms:break
        time.sleep(.25)
    return pd.DataFrame(rows,columns=['termino','qid_candidato','descripcion','coincidencia_contexto','estado'])
