"""미얀마어 삼장사전 → 문단 자료 abd_units.jsonl: [표제어(미얀마), 로마자, 본문, 출처]"""
import sqlite3,re,json,html,sys,collections,unicodedata
sys.path.insert(0,'/home/claude/corpus'); from my2roman import conv
MYD=str.maketrans('၀၁၂၃၄၅၆၇၈၉','0123456789')
t=sqlite3.connect('/home/claude/corpus/abd_src/tipi_mm_abhidhan.db')
s=sqlite3.connect('/home/claude/abidan/app/src/main/assets/databases/tipitaka_abidan.db')
bname={b:n.replace('အတွဲ','').strip().translate(MYD).replace('-အပိုင်း',' 제').replace('  ',' ') for b,n,_,_ in s.execute('select * from books')}
def vol(b): 
    m=re.match(r'(\d+)\s*(?:제\s*(\d+))?',bname[b]); return f"{int(m.group(1))}권"+(f" {m.group(2)}부" if m.group(2) else '')
scan=collections.defaultdict(list)
for w,b,p in s.execute('select word,book_id,page_number from words order by id'):
    r=f"{vol(b)} {p}쪽"
    if r not in scan[w]: scan[w].append(r)
def plain(h):
    ref=re.search(r'<p class="reference">(.*?)</p>',h)
    h=re.sub(r'<p class="reference">.*?</p>','',h)
    h=re.sub(r'<li>','\n',h); h=re.sub(r'</?(p|div|ul)[^>]*>','\n',h)
    h=html.unescape(re.sub(r'<[^>]+>','',h))
    h='\n'.join(x.strip() for x in h.split('\n') if x.strip())
    return h,(ref.group(1).translate(MYD) if ref else '')
units=[];seen=set()
for w,d in t.execute('select word,definition from dictionary order by rowid'):
    w=unicodedata.normalize('NFC',w.strip()); body,ref=plain(d)
    if body.startswith(w):body=body  # 표제어 줄 포함
    r=[]
    m=re.match(r'တိပိ၊(\d+)၊(\d+)',ref) or re.match(r'တိပိ၊\s*(\d+)\s*၊\s*(\d+)',ref)
    if m: r.append(f"삼장사전 텍스트판 {int(m.group(1))}권 {int(m.group(2))}쪽")
    if 'မူရင်း' in body and len(body)<80 and scan.get(w): r.append('스캔본 '+', '.join(scan[w][:4]))
    elif scan.get(w): r.append('스캔본 '+scan[w][0])
    units.append([w,conv(w),body,' · '.join(r)]); seen.add(w)
n2=0
for w,refs in scan.items():
    if w in seen: continue
    units.append([w,conv(w),'(텍스트판에 없는 표제어 — 스캔본을 보세요)','스캔본 '+', '.join(refs[:4])]); n2+=1
with open('/home/claude/corpus/abd_units.jsonl','w') as o:
    for u in units: o.write(json.dumps(u,ensure_ascii=False)+'\n')
print(len(units),'units (scan-only',n2,')')
