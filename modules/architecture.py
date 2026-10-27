"""Evidence-aware planning: no invented QIDs, URLs, volumes or academic claims."""
import re, io, gzip, csv, xml.etree.ElementTree as ET
from urllib.parse import urlparse
import pandas as pd
from .demanda import norm

def parse_sitemap(blob, name='sitemap.xml'):
    """Read a sitemap XML/XML.GZ or a URL inventory CSV, without guessing absent pages.

    CSV supports url/loc/address/direccion and optional source/lastmod/changefreq/priority.
    Sitemap index entries are not treated as site pages.
    """
    columns = ['url', 'lastmod', 'origen', 'source', 'changefreq', 'priority']
    empty = pd.DataFrame(columns=columns)
    if not blob:
        return empty
    if len(blob) > 12_000_000:
        raise ValueError('El archivo supera el límite de 12 MB.')
    lower = name.lower()
    if lower.endswith('.csv'):
        decoded = None
        for encoding in ('utf-8-sig', 'utf-16', 'cp1252'):
            try:
                decoded = blob.decode(encoding)
                break
            except UnicodeDecodeError:
                pass
        if decoded is None:
            raise ValueError('No se pudo leer la codificación del CSV.')
        try:
            delimiter = csv.Sniffer().sniff(decoded[:8192], delimiters=',;\t|').delimiter
        except csv.Error:
            delimiter = ';' if decoded.splitlines()[0].count(';') > decoded.splitlines()[0].count(',') else ','
        reader = csv.DictReader(io.StringIO(decoded), delimiter=delimiter)
        if not reader.fieldnames:
            raise ValueError('El CSV no tiene encabezados.')
        aliases = {'url', 'loc', 'address', 'direccion', 'dirección', 'link', 'enlace'}
        normalized = {norm(h).strip(): h for h in reader.fieldnames if h}
        url_key = next((normalized[a] for a in ('url','loc','address','direccion','link','enlace') if a in normalized), None)
        if not url_key:
            raise ValueError('No se encontró columna de URL. Se admite url, loc, Address o Dirección.')
        def get(row, *names):
            for n in names:
                key = normalized.get(n)
                if key is not None:
                    return str(row.get(key) or '').strip()
            return ''
        records=[]
        for row in reader:
            u = str(row.get(url_key) or '').strip()
            parsed = urlparse(u)
            if parsed.scheme not in ('http','https') or not parsed.netloc:
                continue
            records.append({'url':u, 'lastmod':get(row,'lastmod','last modified','last modification'),
                            'origen':'csv_usuario', 'source':get(row,'source','sitemap','origen'),
                            'changefreq':get(row,'changefreq'), 'priority':get(row,'priority')})
        if not records:
            raise ValueError('El CSV no contiene URLs HTTP/HTTPS válidas.')
        return pd.DataFrame(records, columns=columns).drop_duplicates(subset=['url'], keep='first').reset_index(drop=True)
    if lower.endswith('.gz'):
        try:
            blob = gzip.decompress(blob)
        except (OSError, EOFError) as exc:
            raise ValueError('El archivo GZ no se pudo descomprimir.') from exc
    try:
        root = ET.fromstring(blob)
    except ET.ParseError as exc:
        raise ValueError('El XML del sitemap no es válido.') from exc
    typ = root.tag.rsplit('}',1)[-1]
    if typ not in ('urlset','sitemapindex'):
        raise ValueError('Se esperaba sitemap.xml, sitemap index o CSV de URLs.')
    ns={'s':'http://www.sitemaps.org/schemas/sitemap/0.9'}
    if typ == 'sitemapindex':
        raise ValueError('El archivo es un índice de sitemaps, no un inventario de URLs. Exporta el CSV completo o los sitemaps hijos.')
    records=[]
    for node in root.findall('s:url',ns):
        u=node.findtext('s:loc',default='',namespaces=ns).strip()
        parsed=urlparse(u)
        if parsed.scheme in ('http','https') and parsed.netloc:
            records.append({'url':u,'lastmod':node.findtext('s:lastmod',default='',namespaces=ns),
                            'origen':'sitemap_xml','source':name,'changefreq':node.findtext('s:changefreq',default='',namespaces=ns),
                            'priority':node.findtext('s:priority',default='',namespaces=ns)})
    return pd.DataFrame(records,columns=columns).drop_duplicates('url').reset_index(drop=True)

def verify_entities(frame, decisions):
    if frame is None or frame.empty:return pd.DataFrame()
    out=frame.copy()
    out['revision_humana']=out.apply(lambda x: decisions.get(str(x.get('qid_candidato','')),'pendiente'),axis=1)
    out['estado_final']=out.apply(lambda x:'verificado_por_usuario' if x['revision_humana']=='aprobar' and str(x.get('qid_candidato','')).startswith('Q') else 'descartado' if x['revision_humana']=='descartar' else 'pendiente',axis=1)
    return out

def facet_matrix(classification, questions):
    if classification is None or classification.empty:return pd.DataFrame()
    frames=[classification.assign(tipo_consulta='keyword')]
    if questions is not None and not questions.empty:
        from .facetas import build
        q,_=build(questions,'')
        frames.append(q.assign(tipo_consulta='pregunta_observada'))
    df=pd.concat(frames,ignore_index=True)
    rows=[]
    for name,grp in df.groupby('grupo'):
        vol=pd.to_numeric(grp.get('volume'),errors='coerce')
        rows.append({'faceta':name,'keywords':int((grp.tipo_consulta=='keyword').sum()),'preguntas_observadas':int((grp.tipo_consulta=='pregunta_observada').sum()),'con_volumen':int(vol.gt(0).sum()),'suma_volumen_no_trafico':float(vol.fillna(0).sum()),'ejemplos':' | '.join(grp.keyword.head(5).astype(str))})
    return pd.DataFrame(rows).sort_values('keywords',ascending=False)

def plan_pages(topic,country,classification,questions,sitemap,source_data,verified_entities,works):
    """Propose a PAI and facet candidates; no final create/update decisions without content audit."""
    from .facetas import intent_bucket
    q=questions if questions is not None else pd.DataFrame()
    pages=[('PAI',topic,'Tema central')]
    if classification is not None and not classification.empty:
        for facet,grp in classification.groupby('grupo'):
            if facet=='Intención por verificar' or len(grp)<3:continue
            sample=grp.sort_values('volume',ascending=False,na_position='last').iloc[0].keyword
            pages.append(('Clúster',str(sample),facet))
    out=[]
    for kind,seed,facet in pages:
        matched=[]
        if sitemap is not None and not sitemap.empty:
            tokens={t for t in norm(seed).split() if len(t)>3}
            for u in sitemap.url.astype(str):
                slug=norm(urlparse(u).path.strip('/').replace('-',' ').replace('_',' '))
                if tokens and len(tokens & set(slug.split()))>=min(2,len(tokens)):matched.append(u)
        candidates=' | '.join(matched[:4])
        question_rows=[]
        if not q.empty:
            question_rows=q[q.keyword.map(intent_bucket).eq(facet)] if kind!='PAI' else q.head(5)
        qs=' | '.join(question_rows.keyword.head(4).astype(str)) if len(question_rows) else ''
        out.append({'tipo':kind,'faceta':facet,'consulta_semilla':seed,'urls_candidatas_sitemap':candidates,'accion':'AUDITAR URL EXISTENTE' if candidates else 'EVALUAR NUEVA URL','estado':'propuesta_no_validada','preguntas_observadas':qs,'nota':'El sitemap no confirma contenido ni canibalización; revisar página antes de decidir.'})
    return pd.DataFrame(out)

def brief_rows(pages,classification,questions,sources,entities,works):
    """Traceability per heading: provenance must be explicit, never invented."""
    rows=[]
    src=sources if sources is not None else pd.DataFrame()
    work=works if works is not None else pd.DataFrame()
    ent=entities if entities is not None else pd.DataFrame()
    verified=ent[ent.estado_final.eq('verificado_por_usuario')] if not ent.empty and 'estado_final' in ent else pd.DataFrame()
    for _,p in pages.iterrows():
        seed=str(p.consulta_semilla)
        base=classification[classification.grupo.eq(p.faceta)] if not classification.empty and p.tipo!='PAI' else classification
        base=base.sort_values('volume',ascending=False,na_position='last') if not base.empty else base
        k=base.iloc[0] if not base.empty else None
        evidence=f'Semrush keywords: {k.keyword} (vol. {k.volume if pd.notna(k.volume) else "sin dato"}; KD {k.kd if pd.notna(k.kd) else "sin dato"})' if k is not None else 'Sin keyword vinculada'
        rows.append({'pagina':seed,'bloque':'H1','encabezado':seed,'que_desarrolla':'Responder la consulta principal, delimitar el alcance y la intención.','de_donde_sale':evidence,'estado_fuente':'dato_csv' if k is not None else 'pendiente'})
        if not src.empty:
            for _,s in src.head(3).iterrows():
                if str(s.get('revision_tematica','')).startswith('excluir'):continue
                rows.append({'pagina':seed,'bloque':'H2','encabezado':'Explicar: '+str(s.get('titulo','concepto')),'que_desarrolla':'Definición y relaciones conceptuales pertinentes; requiere revisión editorial.','de_donde_sale':'Wikipedia: '+str(s.get('url','')),'estado_fuente':'fuente_contextual_pendiente'})
        if not verified.empty:
            for _,e in verified.head(2).iterrows():
                rows.append({'pagina':seed,'bloque':'H3','encabezado':'Entidad: '+str(e.get('termino','')),'que_desarrolla':'Explicar entidad y su relación con la consulta.','de_donde_sale':'Wikidata: '+str(e.get('qid_candidato','')),'estado_fuente':'qid_aprobado_usuario'})
        if not work.empty:
            for _,w in work[work.get('estado',pd.Series(dtype=str)).eq('candidato_revisar')].head(2).iterrows():
                rows.append({'pagina':seed,'bloque':'H2','encabezado':'Evidencia académica: '+str(w.get('tema','tema')),'que_desarrolla':'Revisar el estudio antes de redactar afirmaciones académicas.','de_donde_sale':'OpenAlex: '+str(w.get('openalex_id','')),'estado_fuente':'lectura_pendiente'})
        qs=str(p.get('preguntas_observadas','')).split(' | ') if p.get('preguntas_observadas','') else []
        for question in qs[:5]:
            rows.append({'pagina':seed,'bloque':'H3','encabezado':question,'que_desarrolla':'Responder la pregunta observada, con fuentes y ejemplos.','de_donde_sale':'Semrush Questions: '+question,'estado_fuente':'dato_csv'})
        rows.append({'pagina':seed,'bloque':'Fuentes citadas','encabezado':'Bibliografía verificable','que_desarrolla':'Citar documentos efectivamente revisados; no citar candidatos como confirmados.','de_donde_sale':'Wikipedia / Wikidata / OpenAlex según estados','estado_fuente':'revisión_requerida'})
        rows.append({'pagina':seed,'bloque':'Firma del autor','encabezado':'Autoría y experiencia','que_desarrolla':'Añadir autor real y experiencia acreditable; no inventar credenciales.','de_donde_sale':'Información editorial aportada por el equipo','estado_fuente':'pendiente'})
    return pd.DataFrame(rows)
