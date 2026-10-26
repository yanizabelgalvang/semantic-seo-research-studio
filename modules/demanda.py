import io, unicodedata
import pandas as pd

def clean(x):
    s=unicodedata.normalize('NFKD',str(x).lower())
    return ''.join(c for c in s if not unicodedata.combining(c)).strip()

def parse_number(v):
    s=str(v).strip().replace(' ','').replace('%','').replace('$','')
    if not s or s.lower() in ('nan','n/a','-','none') or s.startswith('<'): return float('nan')
    if ',' in s and '.' in s:
        s=s.replace('.','').replace(',','.') if s.rfind(',')>s.rfind('.') else s.replace(',','')
    elif ',' in s: s=s.replace(',','.') if len(s.split(',')[-1])!=3 else s.replace(',','')
    elif '.' in s and len(s.split('.')[-1])==3: s=s.replace('.','')
    try: return float(s)
    except ValueError: return float('nan')

def load_semrush(files):
    aliases={'keyword':['keyword','palabra clave'],'volume':['volume','volumen','search volume'],'kd':['keyword difficulty','kd %','kd','dificultad'],'intent':['intent','intencion'],'cpc':['cpc','cpc (usd)']}
    frames=[]
    for file in files:
        df=None
        for enc in ('utf-8-sig','utf-16','cp1252'):
            try: txt=file.getvalue().decode(enc)
            except UnicodeError: continue
            for sep in (None,';',',','\t'):
                try:
                    tmp=pd.read_csv(io.StringIO(txt),sep=sep,engine='python',on_bad_lines='skip')
                    if any(clean(c) in aliases['keyword'] for c in tmp.columns): df=tmp; break
                except Exception: pass
            if df is not None: break
        if df is None: raise ValueError(f'{file.name}: no se detecta la columna Keyword / Palabra clave')
        mapping={}
        for col in df.columns:
            for target,options in aliases.items():
                if clean(col) in options: mapping[col]=target;break
        df=df.rename(columns=mapping)
        df['keyword']=df.keyword.astype(str).str.strip()
        df=df[~df.keyword.isin(['','nan'])].copy()
        for c in ('volume','kd','cpc'):
            df[c]=df[c].map(parse_number) if c in df else float('nan')
        if 'intent' not in df: df['intent']=''
        df['source_file']=file.name
        frames.append(df[['keyword','volume','kd','intent','cpc','source_file']])
    if not frames: return pd.DataFrame()
    out=pd.concat(frames,ignore_index=True)
    out['key']=out.keyword.str.lower().str.replace(r'\s+',' ',regex=True).str.strip()
    return out.sort_values('volume',ascending=False,na_position='last').drop_duplicates('key').drop(columns='key').reset_index(drop=True)
