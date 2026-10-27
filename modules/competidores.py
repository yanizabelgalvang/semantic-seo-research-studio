"""SERP aportada por usuario y corpus de competidores con trazabilidad."""
import io
from urllib.parse import urlparse
import pandas as pd
import requests
from bs4 import BeautifulSoup

COLUMNS=['consulta','posicion','url','titulo','fuente','estado','texto','error']

def read_serp_csv(upload):
    raw=upload.getvalue() if hasattr(upload,'getvalue') else upload
    if isinstance(raw,bytes):
        for encoding in ('utf-8-sig','utf-16','cp1252'):
            try: txt=raw.decode(encoding);break
            except UnicodeError:continue
        else:raise ValueError('Codificación de SERP no reconocida')
    else:txt=raw
    sep='\t' if '\t' in txt.splitlines()[0] else (';' if ';' in txt.splitlines()[0] else ',')
    df=pd.read_csv(io.StringIO(txt),sep=sep,dtype=str).fillna('')
    aliases={'url':['url','link','enlace'],'posicion':['posicion','position','rank','ranking'],'titulo':['titulo','title'],'consulta':['consulta','query','keyword']}
    rename={c:k for c in df.columns for k,ls in aliases.items() if c.strip().casefold() in ls}
    df=df.rename(columns=rename)
    if 'url' not in df:raise ValueError('La exportación SERP necesita una columna URL')
    if 'posicion' not in df:df['posicion']=list(range(1,len(df)+1))
    if 'titulo' not in df:df['titulo']=''
    if 'consulta' not in df:df['consulta']=''
    df=df[df.url.map(lambda u:urlparse(u).scheme in ('https','http') and bool(urlparse(u).netloc))].copy()
    df=df.drop_duplicates('url').head(20)
    df['fuente']='csv_usuario';df['estado']='serp_aportada_no_verificada';df['texto']='';df['error']=''
    return df[COLUMNS]

def fetch_competitors(serp,max_pages=5,max_chars=18000):
    rows=[]
    for _,r in serp.head(max_pages).iterrows():
        row=r.to_dict()
        try:
            resp=requests.get(row['url'],timeout=12,headers={'User-Agent':'Mozilla/5.0 (compatible; SemanticSEOResearchStudio/1.0)'},allow_redirects=True)
            resp.raise_for_status()
            if 'text/html' not in resp.headers.get('content-type',''):raise ValueError('Contenido no HTML')
            soup=BeautifulSoup(resp.text,'html.parser')
            for tag in soup(['script','style','nav','footer','header','aside','form']):tag.decompose()
            text=' '.join(soup.stripped_strings)
            if len(text)<400:raise ValueError('Texto insuficiente o bloqueo')
            row['texto']=text[:max_chars];row['estado']='contenido_recuperado'
        except (requests.RequestException,ValueError) as exc:
            row['estado']='no_recuperado';row['error']=str(exc)[:180]
        rows.append(row)
    return pd.DataFrame(rows,columns=COLUMNS)
