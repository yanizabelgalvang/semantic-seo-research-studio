"""Búsqueda y comprobación contextual de candidatos Wikidata; sin QIDs falsamente verificados."""
import time
from functools import lru_cache
import pandas as pd
import requests
from .demanda import norm
API='https://www.wikidata.org/w/api.php'
HEADERS={'User-Agent':'SemanticSEOResearchStudio/0.5 (research; github.com/yanizabelgalvang/semantic-seo-research-studio)'}
COLUMNS=['termino','qid_candidato','etiqueta','descripcion','coincidencia_contexto','estado','motivo']
UNRELATED=('catedral','iglesia','ornitologia','birdlife','apellido','municipio','localidad','ciudad','provincia','rio','pueblo','distrito','futbol')
@lru_cache(maxsize=256)
def _search(term):
    for attempt in range(3):
        try:
            r=requests.get(API,params={'action':'wbsearchentities','search':term,'language':'es','format':'json','limit':5},headers=HEADERS,timeout=15)
            if r.status_code in (429,503):
                retry=r.headers.get('Retry-After','2')
                time.sleep(min(int(retry) if retry.isdigit() else 2**attempt,8));continue
            r.raise_for_status();return r.json().get('search',[]),'ok'
        except (requests.RequestException,ValueError) as exc:
            if attempt==2:return [],'error_red: '+str(exc)[:90]
            time.sleep(2**attempt)
    return [],'limitado_429'

def lookup(terms,topic,max_terms=8):
    rows=[];seen=set();topic_norm=norm(topic);context=set(topic_norm.split())
    seo_context=bool(context & {'seo','posicionamiento','web','buscadores'})
    for term in terms:
        term=str(term).strip();key=norm(term)
        if not key or key in seen:continue
        seen.add(key);items,status=_search(term)
        if status!='ok' or not items:
            rows.append({'termino':term,'qid_candidato':'','etiqueta':'','descripcion':'','coincidencia_contexto':0,'estado':status if status!='ok' else 'sin_resultado','motivo':'sin respuesta verificable'});continue
        for item in items[:4]:
            label=item.get('label','') or '';desc=item.get('description','') or ''
            descriptor=norm(label+' '+desc)
            off_topic=seo_context and any(x in descriptor for x in UNRELATED)
            exact=norm(label)==key or key in [norm(a) for a in item.get('aliases',[]) or []]
            overlap=len(context & set(norm(desc).split()))
            score=int(exact)+overlap
            status='descartado_fuera_contexto' if off_topic else ('candidato_contextual' if exact and overlap else 'candidato_ambiguo')
            rows.append({'termino':term,'qid_candidato':item.get('id',''),'etiqueta':label,'descripcion':desc,
                         'coincidencia_contexto':score,'estado':status,
                         'motivo':'significado incompatible' if off_topic else 'pendiente de validación humana y propiedades P31/P279'})
        if len(seen)>=max_terms:break
        time.sleep(.15)
    return pd.DataFrame(rows,columns=COLUMNS)
