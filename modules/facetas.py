import re,unicodedata
import pandas as pd
FACETS={
 'Fundamentos SEO':['seo','posicionamiento','buscador','search engine','optimización'],
 'SEO técnico':['indexación','rastreo','robots','sitemap','canonical','core web vitals','velocidad'],
 'Contenido y keywords':['contenido','keyword','palabras clave','redacción','semántica','blog'],
 'Enlaces y autoridad':['backlink','enlaces','link building','autoridad'],
 'Servicios y agencias':['agencia','servicio','consultor','precio','cotización','experto'],
 'SEO local':['local','maps','google business','ciudad','méxico','tijuana','monterrey'],
 'Analítica y herramientas':['analytics','search console','semrush','herramienta','medición'],
}
def fold(s):
    s=unicodedata.normalize('NFKD',str(s).lower())
    return ''.join(c for c in s if not unicodedata.combining(c))
def facet_for(s):
    t=fold(s)
    matches=[(f,sum(1 for w in ws if fold(w) in t)) for f,ws in FACETS.items()]
    best=max(matches,key=lambda x:x[1]);
    if any(w in t for w in ('agencia','servicio seo','consultor seo')):return 'Servicios y agencias'
    if any(w in t for w in ('sitemap','robots.txt','canonical','indexacion','rastreo')):return 'SEO técnico'
    return best[0] if best[1] else 'Sin clasificar'
def summarize(df):
    if df.empty:return pd.DataFrame(columns=['faceta','keywords','volumen_medible','sin_datos'])
    d=df.copy();d['faceta']=d.keyword.map(facet_for)
    d['volumen_medible']=pd.to_numeric(d.volume,errors='coerce').fillna(0)
    d['sin_datos']=d.volume.isna().astype(int)
    return d.groupby('faceta',as_index=False).agg(keywords=('keyword','count'),volumen_medible=('volumen_medible','sum'),sin_datos=('sin_datos','sum')).sort_values('keywords',ascending=False)
