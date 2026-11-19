"""문단 자료(jsonl) → 조각 파일(gzip JSON) + 낱말 앞 두 글자별 색인
사용: python3 mkshards.py NAME units.jsonl OUTDIR [조각크기MB]
조각: OUTDIR/NAME-s{k}.txt (gzip→base64)  = [[...unit...], ...]
색인: OUTDIR/NAME-i-{n}.txt (gzip→base64, n=prefixes 순번) = {낱말: [조각 번호...]}
요약: OUTDIR/NAME-meta.json
"""
import sys,json,gzip,re,unicodedata,collections,os,base64
name,src,out=sys.argv[1:4]; lim=float(sys.argv[4]) if len(sys.argv)>4 else 2.5
os.makedirs(out,exist_ok=True)
def fold(s):
    s=unicodedata.normalize('NFD',s); s=re.sub(r'[̀-ͯ​-‍]','',s)
    return unicodedata.normalize('NFC',s).lower()
TOK=re.compile('[\u1000-\u103f\u1050-\u109f]+|[^\\W\\d_]+',re.U)
units=[json.loads(l) for l in open(src)]
TXT=[i for i,_ in enumerate(units[0]) if isinstance(units[0][i],str)]
shards=[[]];size=0;idx=collections.defaultdict(set);shard_of=[]
for u in units:
    b=len(json.dumps(u,ensure_ascii=False).encode())
    if size+b>lim*1e6 and shards[-1]: shards.append([]);size=0
    shards[-1].append(u);size+=b
    k=len(shards)-1
    for t in set(TOK.findall(fold(' '.join(x for x in u if isinstance(x,str))))):
        if len(t)>=2: idx[t].add(k)
for k,s in enumerate(shards):
    open(f'{out}/{name}-s{k}.txt','w').write(base64.b64encode(gzip.compress(json.dumps(s,ensure_ascii=False,separators=(',',':')).encode(),9)).decode())
by=collections.defaultdict(dict)
for t,ks in idx.items(): by[t[:2]][t]=sorted(ks)
pre=sorted(by); pmap={}; grp=[{}]; gsz=0
for p_ in pre:
    sz=len(json.dumps(by[p_],ensure_ascii=False))
    if gsz+sz>1_500_000 and grp[-1]: grp.append({}); gsz=0
    grp[-1].update(by[p_]); gsz+=sz; pmap[p_]=len(grp)-1
for g_,d in enumerate(grp):
    open(f'{out}/{name}-i-{g_}.txt','w').write(base64.b64encode(gzip.compress(json.dumps(d,ensure_ascii=False,separators=(',',':')).encode(),9)).decode())
json.dump({'shards':len(shards),'units':len(units),'pmap':pmap,'counts':[len(s) for s in shards]},open(f'{out}/{name}-meta.json','w'),ensure_ascii=False)
print(name,len(units),'units',len(shards),'shards',len(idx),'tokens',len(grp),'index files')
