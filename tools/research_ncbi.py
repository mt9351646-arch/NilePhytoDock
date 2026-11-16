"""Cache open-access JATS from Europe PMC for NCBI PMC article records.

No database mutation: the reviewed manifest drives a separate import.
"""
import argparse,json,re,hashlib,time,sys
sys.stdout.reconfigure(encoding='utf-8')
from pathlib import Path
import requests
from lxml import etree

ROOT=Path('data/literature');ROOT.mkdir(parents=True,exist_ok=True)
def plain(e):return re.sub(r'\s+',' ',''.join(e.itertext())).strip() if e is not None else ''
def fetch(pmc):
    path=ROOT/(pmc+'.xml')
    if not path.exists():
        response=requests.get(f'https://www.ebi.ac.uk/europepmc/webservices/rest/{pmc}/fullTextXML',timeout=90)
        response.raise_for_status();etree.fromstring(response.content);path.write_bytes(response.content);time.sleep(.4)
    tree=etree.parse(str(path));article=tree.getroot()
    tables=[]
    for t in article.findall('.//table-wrap'):
        rs=[]
        for tr in t.findall('.//tr'):
            rs.append([plain(c) for c in tr if c.tag in ['td','th']])
        tables.append({'id':t.get('id'),'label':plain(t.find('label')),'caption':plain(t.find('caption')),'rows':rs,'footnotes':plain(t.find('table-wrap-foot'))})
    sections=[{'title':plain(s.find('title')),'text':' '.join(plain(p) for p in s.findall('p'))} for s in article.findall('.//body//sec')]
    info={'pmcid':pmc,'title':plain(article.find('.//article-title')),'doi':next((plain(i) for i in article.findall('.//article-id') if i.get('pub-id-type')=='doi'),''),'license':plain(article.find('.//license')),'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'tables':tables,'sections':sections}
    (ROOT/(pmc+'.json')).write_text(json.dumps(info,ensure_ascii=False,indent=2),encoding='utf-8')
    return info
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('pmc',nargs='+');a=p.parse_args()
    for pmc in a.pmc:
        try:
            d=fetch(pmc);print(pmc,d['title'],flush=True)
            for t in d['tables']:print(t['id'],len(t['rows']),t['caption'][:220], '\n',t['rows'][:3],flush=True)
            for s in d['sections']:
                if re.search('plant material|collection|sample|extraction',s['title'],re.I):print('MATERIAL',s['title'],s['text'][:1600],flush=True)
        except Exception as e:print(pmc,'ERROR',repr(e),flush=True)
