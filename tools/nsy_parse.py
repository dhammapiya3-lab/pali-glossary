"""닛사야 텍스트 DB(OCR) → 문단 자료 nsy_units.jsonl: [닛사야 이름(DB 표기), 책 약호, 문단, 본문(빠알리 = 풀이), 로마자 빠알리]"""
import sqlite3,json,sys,unicodedata,re
sys.path.insert(0,'/home/claude/corpus'); from my2roman import conv
c=sqlite3.connect('/home/claude/corpus/nsy_src/epitaka_my_nissaya (1).db')
nm={i:(n or '').strip() for i,n,info in c.execute('select * from books')}
info={i:info for i,n,info in c.execute('select * from books')}
def label(i):
    n=nm[i]; m=re.search(r'by (?:the |an )?(?:Venerable |Bhaddanta )?(.*?)(?: Sayadaw)?(?:\.|,| tradition| one of)',info[i] or '')
    return f"{n}" if re.search(r'[က-႟]',n) else (m.group(1) if m else f'닛사야 {i}')
out=open('/home/claude/corpus/nsy_units.jsonl','w');n=0;cur=None;lines=[]
def flush():
    global n
    if not cur or not lines: return
    txt=" / ".join((f"{p} = {m}" if p else m) for p,m in lines)
    rom=' '.join(conv(p) for p,_ in lines)
    out.write(json.dumps([label(cur[0]),cur[1],str(cur[2]),unicodedata.normalize('NFC',txt),rom],ensure_ascii=False)+'\n'); n+=1
for nid,bid,pid,lid,content in c.execute('select nissaya_id,book_id,para_id,line_id,content from sentences order by nissaya_id,book_id,para_id,line_id'):
    k=(nid,bid,pid)
    if k!=cur: flush(); cur=k; lines=[]
    try: arr=json.loads(content)
    except Exception: continue
    if isinstance(arr,str): lines.append(('',arr.strip())); continue
    for x in arr:
        if isinstance(x,dict): lines.append(((x.get('pali') or '').strip(),(x.get('meaning') or '').strip()))
        elif isinstance(x,str): lines.append(('',x.strip()))
flush(); out.close(); print(n,'units')
print({i:label(i) for i in nm})
