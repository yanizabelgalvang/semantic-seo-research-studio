import re
import pandas as pd
import requests
from .demanda import norm
HEADERS={'User-Agent':'SemanticSEOResearchStudio/0.3 (research; https://github.com/yanizabelgalvang/semantic-seo-research-studio)'}
def search(queries,topic,max_works=15):
    rows=[];seen=set();topic_tokens={x for x in norm(topic).split() if len(x)>3}
    for query in list(dict.fromkeys(queries))[:3]:
        try:
            resp=requests.get('https://api.openalex.org/works',params={'search':query,'per-page':max_works},headers=HEADERS,timeout=20)
            resp.raise_for_status()
            for w in resp.json().get('results',[]):
                oid=w.get('id','');title=w.get('display_name','');primary=w.get('primary_topic') or {}
                if not oid or oid in seen:continue
                seen.add(oid)
                title_tokens=set(norm(title).split());topic_label=norm(primary.get('display_name',''))
                overlap=len(topic_tokens & title_tokens)
                score=overlap/max(len(topic_tokens),1)
                # No es una validación científica, solo un filtro de pertinencia de metadatos.
                rows.append({'consulta':query,'titulo':title,'año':w.get('publication_year'),'doi':w.get('doi') or '', 'openalex_id':oid,'tema':primary.get('display_name',''),'relevancia_metadatos':round(score,2),'estado':'candidato_revisar' if score>=.5 else 'baja_coincidencia'})
        except (requests.RequestException,ValueError) as exc:
            rows.append({'consulta':query,'titulo':'','año':None,'doi':'','openalex_id':'','tema':'','relevancia_metadatos':0,'estado':'error_red: '+str(exc)[:90]})
    return pd.DataFrame(rows,columns=['consulta','titulo','año','doi','openalex_id','tema','relevancia_metadatos','estado'])
