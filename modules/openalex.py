import pandas as pd
import requests

def search(queries):
    rows=[]
    for query in list(dict.fromkeys(queries))[:3]:
        try:
            r=requests.get('https://api.openalex.org/works',params={'search':query,'per-page':5},headers={'User-Agent':'SemanticSEOResearchStudio/0.1'},timeout=20)
            r.raise_for_status()
            for w in r.json().get('results',[]):
                rows.append({'consulta':query,'titulo':w.get('display_name',''),'año':w.get('publication_year'),'doi':w.get('doi') or '','openalex_id':w.get('id',''),'tema':(w.get('primary_topic') or {}).get('display_name','')})
        except (requests.RequestException,ValueError) as e: rows.append({'consulta':query,'titulo':f'Error: {str(e)[:60]}','año':None,'doi':'','openalex_id':'','tema':''})
    return pd.DataFrame(rows)
