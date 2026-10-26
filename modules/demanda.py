import io, re, unicodedata
import pandas as pd

def norm(s):
    return ''.join(c for c in unicodedata.normalize('NFKD',str(s).casefold()) if not unicodedata.combining(c)).strip()

def number(v):
    if pd.isna(v): return float('nan')
    s=str(v).strip().replace('\u00a0','').replace(' ','').replace('%','').replace('$','')
    if s.lower() in ('','nan','none','n/a','-','nd'):return float('nan')
    if s.startswith('<') or re.match(r'^\d+\s*-\s*\d+$',s):return float('nan')
    if ',' in s and '.' in s: s=s.replace('.','').replace(',','.') if s.rfind(',')>s.rfind('.') else s.replace(',','')
    elif ',' in s: s=s.replace(',','') if re.fullmatch(r'\d{1,3}(,\d{3})+',s) else s.replace(',','.')
    elif '.' in s and re.fullmatch(r'\d{1,3}(\.\d{3})+',s):s=s.replace('.','')
    try:return float(s)
    except ValueError:return float('nan')

ALIASES={'keyword':['keyword','palabra clave'],'volume':['volume','volumen','search volume','volumen de busqueda'],'kd':['keyword difficulty','kd %','kd','dificultad de la palabra clave','dificultad'],'intent':['intent','intencion','intencion de busqueda'],'cpc':['cpc','cpc (usd)','cpc (us$)']}

def load_semrush(files):
    frames=[];warnings=[]
    for file in files:
        raw=file.getvalue();found=None
        for encoding in ('utf-8-sig','utf-16','cp1252'):
            try: txt=raw.decode(encoding)
            except UnicodeError:continue
            for sep in (',',';','\t'):
                try:
                    df=pd.read_csv(io.StringIO(txt),sep=sep,dtype=str,keep_default_na=False)
                    mapping={c:k for c in df.columns for k,vals in ALIASES.items() if norm(c) in vals}
                    if 'keyword' in mapping.values():found=df.rename(columns=mapping);break
                except (pd.errors.ParserError,ValueError):continue
            if found is not None:break
        if found is None:raise ValueError(f'{file.name}: no se encontró una columna Keyword/Palabra clave válida.')
        if 'volume' not in found:raise ValueError(f'{file.name}: no se encontró Volumen/Volume. Exporta Keyword Magic Tool con métricas.')
        found['keyword']=found.keyword.astype(str).str.strip()
        found=found[found.keyword.ne('')].copy()
        for k in ('volume','kd','cpc'):
            found[k]=found[k].map(number) if k in found else float('nan')
        if 'intent' not in found:found['intent']=''
        found['source_file']=file.name
        frames.append(found[['keyword','volume','kd','intent','cpc','source_file']])
    if not frames:return pd.DataFrame(columns=['keyword','volume','kd','intent','cpc','source_file','estado_volumen'])
    df=pd.concat(frames,ignore_index=True)
    df['_norm']=df.keyword.map(norm).str.replace(r'\s+',' ',regex=True)
    df=df.sort_values('volume',ascending=False,na_position='last').drop_duplicates('_norm').drop(columns='_norm')
    df['estado_volumen']=df.volume.map(lambda v:'sin_datos' if pd.isna(v) else 'volumen_0' if v==0 else 'medido')
    return df.reset_index(drop=True)
