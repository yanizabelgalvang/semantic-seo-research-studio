import pandas as pd
import requests

def lookup(terms):
    rows=[]
    for term in list(dict.fromkeys(terms))[:12]:
        try:
            r=requests.get('https://www.wikidata.org/w/api.php',params={'action':'wbsearchentities','search':term,'language':'es','format':'json','limit':3},headers={'User-Agent':'SemanticSEOResearchStudio/0.1'},timeout=15)
            r.raise_for_status(); matches=r.json().get('search',[])
            top=matches[0] if matches else {}
            rows.append({'termino':term,'qid_candidato':top.get('id',''),'descripcion':top.get('description',''),'estado':'pendiente_verificacion' if top else 'sin_resultado'})
        except (requests.RequestException,ValueError) as e: rows.append({'termino':term,'qid_candidato':'','descripcion':'','estado':f'error: {str(e)[:50]}'})
    return pd.DataFrame(rows)
