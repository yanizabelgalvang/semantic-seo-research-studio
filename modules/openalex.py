import pandas as pd
import requests
HEADERS={'User-Agent':'SemanticSEOResearchStudio/0.2 (research; https://github.com/yanizabelgalvang/semantic-seo-research-studio)'}
def search(queries,max_works=6):
    rows=[];seen=set()
    for q in list(dict.fromkeys(queries))[:2]:
        try:
            r=requests.get('https://api.openalex.org/works',params={'search':q,'per-page':max_works},headers=HEADERS,timeout=20)
            r.raise_for_status()
            for w in r.json().get('results',[]):
                oid=w.get('id','')
                if oid in seen:continue
                seen.add(oid)
                topic=w.get('primary_topic') or {}
                rows.append({'consulta':q,'titulo':w.get('display_name',''),'año':w.get('publication_year'),'doi':w.get('doi') or '', 'openalex_id':oid,'tema':topic.get('display_name',''),'pertinencia':'por_revisar','estado':'metadatos_obtenidos'})
        except (requests.RequestException,ValueError) as exc:
            rows.append({'consulta':q,'titulo':'','año':None,'doi':'','openalex_id':'','tema':'','pertinencia':'','estado':f'error: {str(exc)[:80]}'})
    return pd.DataFrame(rows,columns=['consulta','titulo','año','doi','openalex_id','tema','pertinencia','estado'])
