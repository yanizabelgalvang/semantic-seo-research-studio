"""Facetas temáticas genéricas derivadas de keywords, no categorías SEO fijas."""
import re
from collections import Counter
import pandas as pd
from .demanda import norm
STOP=set('a al algo ante bajo con contra como de del desde donde el ella en entre es esta este hay la las lo los mas mi mis o para por que se ser sin sobre su sus tu un una uno y ya mexico peru colombia argentina chile'.split())

def tokens(s):return [t for t in re.findall(r'[a-z0-9]+',norm(s)) if len(t)>2 and t not in STOP]

def build(df,topic):
    if df.empty:return pd.DataFrame(),pd.DataFrame()
    seed=set(tokens(topic));counts=Counter()
    for kw in df.keyword:counts.update(set(tokens(kw))-seed)
    generic=set(['web','seo','google','search','engine']) if 'seo' in seed or 'posicionamiento' in seed else set()
    candidates=[w for w,n in counts.most_common(18) if n>=2 and w not in generic]
    # Se derivan etiquetas de los términos observados, sin diccionario sectorial prefijado.
    def assign(kw):
        t=set(tokens(kw))
        hits=[w for w in candidates if w in t]
        if not hits:return 'Tema central / sin subfaceta'
        return 'Subtema: '+hits[0]
    detail=df.copy();detail['faceta_provisional']=detail.keyword.map(assign)
    detail['relevancia_semilla']=detail.keyword.map(lambda k:'directa' if seed & set(tokens(k)) else 'revisar')
    summary=detail.groupby('faceta_provisional',as_index=False).agg(keywords=('keyword','count'),keywords_con_volumen=('volume',lambda x:int(x.gt(0).sum())),volumen_descriptivo=('volume','sum'))
    summary=summary.sort_values('keywords',ascending=False)
    return detail,summary
