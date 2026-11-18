"""Fetch Microsoft's public PBIR schemas and their relative references for local validation."""
from pathlib import Path
import json
from urllib.request import urlopen
from urllib.parse import urljoin, urlparse

ROOT=Path(__file__).resolve().parents[1]
BASE='https://developer.microsoft.com/json-schemas/fabric/item/'
TARGET=ROOT/'powerbi'/'schemas'
INITIAL=[
 'report/definition/visualContainer/2.0.0/schema.json',
 'report/definition/report/3.0.0/schema.json',
 'report/definition/page/2.0.0/schema.json',
 'report/definition/pagesMetadata/1.0.0/schema.json',
 'report/definition/versionMetadata/1.0.0/schema.json',
 'report/definitionProperties/2.0.0/schema.json',
 'semanticModel/definitionProperties/1.0.0/schema.json',
 'report/definition/visualConfiguration/2.0.0/schema-embedded.json',
 'report/definition/visualConfiguration/2.0.0/schema.json',
]

def main():
    done=set(); queue=[BASE+x for x in INITIAL]
    while queue:
        url=queue.pop(0).split('#')[0]
        if url in done or not url.startswith(BASE): continue
        done.add(url)
        path=TARGET/url[len(BASE):]
        try:
            payload=urlopen(url,timeout=30).read()
        except Exception as error:
            print('Skipped',url,error);continue
        path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(payload)
        content=json.loads(payload)
        def walk(value):
            if isinstance(value,dict):
                ref=value.get('$ref','')
                if ref and not ref.startswith('#'):queue.append(urljoin(url,ref))
                for item in value.values():walk(item)
            elif isinstance(value,list):
                for item in value:walk(item)
        walk(content)
        print('Saved',url[len(BASE):])

if __name__=='__main__':main()
