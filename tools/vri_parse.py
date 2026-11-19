"""VRI 6차 결집본(romn XML) → 문단 단위 자료
결과: vri_books.json {books:[{f,b,nik,cat}]}, vri_units.jsonl [book, M쪽, V쪽, §, 소제목, 본문]
- 문단 시작 시점의 미얀마판(M)·VRI판(V) 쪽, 그 문단이 속한 단락 번호(§)
"""
import re,glob,json,os,html,unicodedata
CAT={'mul':'성전','att':'주석서','tik':'복주석서','nrf':'añña'}
TAG=re.compile(r'<[^>]+>')
PB=re.compile(r'<pb ed="(\w)" n="([^"]+)"')
clean=lambda x:re.sub(r'\s+',' ',html.unescape(TAG.sub('',x))).strip()
units=[]; books=[]; bidx={}
def bid(fn,book,nik,cat):
    k=(fn,book)
    if k not in bidx: bidx[k]=len(books); books.append({'f':fn,'b':book,'nik':nik,'cat':cat})
    return bidx[k]
files=sorted(glob.glob('/home/claude/vri/romn/*.xml'))
firstbook={}
for f in files:
    s=open(f,'rb').read().decode('utf-16')
    fn=os.path.basename(f); cat=CAT.get(fn.split('.')[-2],'añña')
    body=s[s.find('<body'):]
    fb=re.search(r'<p rend="nikaya">(.*?)</p>',body) if '.nrf.' in fn else None
    fc=re.search(r'<(?:p|head) rend="chapter"[^>]*>(.*?)</',body)
    fallback=clean((fb or fc).group(1)) if (fb or fc) else fn
    nik=''; book=''; M=V=''; sec=''; PN=''; buf=[]; last=0
    for m in re.finditer(r'<(p|head)\b([^>]*)>(.*?)</\1>',body,re.S):
        tag,attr,inner=m.groups()
        for ed,n in PB.findall(body[last:m.start()]):   # 문단 사이에 있는 쪽 표시
            if ed=='M':M=n
            elif ed=='V':V=n
        last=m.end()
        r=re.search(r'rend="([^"]*)"',attr); rend=r.group(1) if r else ''
        lead=re.match(r'\s*((?:<pb[^>]*/>\s*)+)',inner)
        if lead:
            for ed,n in PB.findall(lead.group(1)):
                if ed=='M':M=n
                elif ed=='V':V=n
        sM,sV=M,V
        for ed,n in PB.findall(inner):
            if ed=='M':M=n
            elif ed=='V':V=n
        text=clean(inner)
        if not text: continue
        if rend=='nikaya': nik=text; continue
        if rend=='book':
            book=text; sec=''
            if fn not in firstbook: firstbook[fn]=book
            for u in buf: u[0]=bid(fn,book,nik,cat)
            buf=[]; continue
        if tag=='head' or rend in('chapter','title','subhead','subsubhead'): sec=text; continue
        pn=re.search(r'\bn="([^"]+)"',attr)
        if pn: PN=pn.group(1)
        u=[None,sM,sV,PN,sec,unicodedata.normalize('NFC',text)]
        if book: u[0]=bid(fn,book,nik,cat)
        else: buf.append(u)
        units.append(u)
    if buf:
        # 책 제목이 없는 파일: 나뉜 파일(s0514a1 등)은 본 파일 제목, 아니면 첫 nikaya/장 제목
        mm=re.match(r'(.+?)\d(\.\w+\.xml)$',fn)
        name=firstbook.get(mm.group(1)+mm.group(2)) if mm else None
        for u in buf: u[0]=bid(fn,name or fallback,nik,cat)
json.dump({'books':books},open('/home/claude/corpus/vri_books.json','w'),ensure_ascii=False)
with open('/home/claude/corpus/vri_units.jsonl','w') as o:
    for u in units: o.write(json.dumps(u,ensure_ascii=False)+'\n')
print(len(books),'books',len(units),'units',sum(len(u[5]) for u in units)//1_000_000,'M chars')
