"""개념정의 워드 파일(.docx) 여러 개 → 검색 사이트 데이터(data/*.json).

사용: python3 build_concepts.py OUTDIR manifest.json
  manifest.json = [{"path": "/내려받은/파일.docx", "id": "드라이브 파일 id", "name": "파일 이름", "modifiedTime": "2026-11-15T03:31:45Z"}, ...]
  내려받지 못한 파일은 {"id","name","modifiedTime","skip":"이유"} 로 넣는다(기록만 남김).
규칙
- 파일마다 '### 표제어' 단위로 항목을 나눈다.
- 같은 표제어가 여러 파일에 있으면 표제어가 가장 많은 파일(통합본)의 내용을 쓴다. 표제어 수가 같으면 modifiedTime이 늦은 파일 → 중복 없음.
  (3,215어 통합본과 1,704어+1,511어 나뉜 파일을 대조한 결과 3,196어는 똑같고 19어는 표제어 링크·대괄호만 다름 — 2026-11-18 확인.
   본문 차이는 없음. 링크는 나뉜 파일 쪽이 더 많이 살아 있음(20 대 14).)
- 표제어 표기 오류는 FIX 표대로 바로잡고, 같은 철자가 된 항목은 하나로 합친다(출판사 번역어 줄도 합침).
  build-info.json의 raw_terms = 합치기 전 표제어 수, terms = 합친 뒤 수.
- 표제어는 빠알리 자모 순서(a ā i ī u ū e o ṃ k kh … l ḷ v s h)로 정렬한다.
- 결과: OUTDIR/concepts-index.json, concepts-0.json …, build-info.json
"""
import sys, os, re, json, subprocess, unicodedata, datetime, glob

# 표제어 표기 오류 바로잡기(2026-11-18, 사용자 확인: '분명'한 오류만. '검토 필요'는 그대로 둠)
# 왼쪽 = 원본 파일의 표제어, 오른쪽 = 문헌(VRI·삼장사전) 철자. 같은 철자 항목이 이미 있으면 한 항목으로 합친다.
FIX={
 # 2026-11-18 원문(VRI) 대조로 더함(사용자 확인)
 'pañcas’ upādānakkhandha':'pañca upādānakkhandhā',   # 사용자 요청: 합치고 이 표제어는 없앰
 'pañcas\' upādānakkhandha':'pañca upādānakkhandhā',   # 2026-11-18: 문서 변환에서 따옴표를 바꾸지 않게 된 뒤의 철자
 'Kondanna':'Koṇḍañña',
 'kūtāgārasālā':'kūṭāgārasālā',
 'kabalīkāra-āhāra':'kabaḷīkāra-āhāra',
 'pittivisaya':'petti-visaya',
 'chaindriya':'chaḷindriya',
 'Tālaveli-magga':'Tālaveḷi-magga',
 'Cīragumba':'Ciragumba',
 'paṭisallaṇā':'paṭisallānā',
 'āsavakkhayaabhiñña':'āsavakkhayābhiññā',
 'aupasampadā':'upasampadā',
 'akuppā me celo vimutti':'akuppā me cetovimutti',
 'adhipaññasikkhā':'adhipaññāsikkhā',
 'adhipaññāsikkha':'adhipaññāsikkhā',
 'adhisīlasikkha':'adhisīlasikkhā',
 'anattaa':'anattā',
 'anatta-sañña':'anattasaññā',
 'anāgāmīphala':'anāgāmiphala',
 'anāgāmīmagga':'anāgāmimagga',
 'Anāthapiṇḍīka':'Anāthapiṇḍika',
 'aniccasañña':'aniccasaññā',
 'aniccāsaññā':'aniccasaññā',
 'Appamāṇasubhānā devā':'Appamāṇasubhā devā',
 'Appamāṇābhānā devā':'Appamāṇābhā devā',
 'abhiñña':'abhiññā',
 'abhedabhedūpacara':'abhedabhedūpacāra',
 'Ambabhādaka Mahā Tissa':'Ambakhādaka-mahātissa',
 'ayoniso masikāra':'ayoniso manasikāra',
 'aloka-saññī':'ālokasaññī',
 'Assāsapassā':'assāsapassāsā',
 'atthagama':'atthaṅgama',
 'ākasānañcāyatana':'ākāsānañcāyatana',
 'Ākiñcaññāyata devā':'ākiñcaññāyatanūpagā devā',
 'ādināvanupassanā':'ādīnavānupassanā',
 'ādīnava-sañña':'ādīnavasaññā',
 'Ābhāssarānā devā':'Ābhassarā devā',
 'Ālavaka':'Āḷavaka',
 'Ālavi':'Āḷavī',
 'Ālāra Kālāma':'Āḷāra Kālāma',
 'āsavakkhayañāna':'āsavakkhayañāṇa',
 'uttamadammatha':'uttamadamatha',
 'udayabbayāupassanā':'udayabbayānupassanā',
 'uddhacca-nirvana':'uddhaccanīvaraṇa',
 'uddhambhāgiyāni saṁyojjanāni':'uddhambhāgiyāni saṃyojanāni',
 'orambhāgiyāni saṁyojjanāni':'orambhāgiyāni saṃyojanāni',
 'upadāna':'upādāna',
 'upādisesa nibbāna':'saupādisesa nibbāna',
 'upekha':'upekkhā',
 'otappa':'ottappa',
 'kadalu':'kadalī',
 'kabaliṅkārāhara':'kabaḷīkārāhāra',
 'kammatthāna':'kammaṭṭhāna',
 'karuna-bhāvanā':'karuṇābhāvanā',
 'karunā':'karuṇā',
 'kāmaccahanda':'kāmacchanda',
 'Kāma-tanhā':'kāmataṇhā',
 'khanika-samādhi':'khaṇikasamādhi',
 'Khāṇu Kondañña':'Khāṇukoṇḍañña',
 'gaṇda':'gaṇḍa',
 'Gijjhakūṭapabhata':'Gijjhakūṭapabbata',
 'cakkhuviññāṇaṃ sotaviññāṇaṃ ghānaviññāṇaṃ jivhāviññāṇaṃ kāyaviññā kāyaviññāṇaṃ manoviññāṇaṃ':'cakkhuviññāṇaṃ sotaviññāṇaṃ ghānaviññāṇaṃ jivhāviññāṇaṃ kāyaviññāṇaṃ manoviññāṇaṃ',
 'Catunna satipaṭṭhānāna':'catunnaṃ satipaṭṭhānānaṃ',
 'catusu ariyasaccesu':'catūsu ariyasaccesu',
 'catusu satipaṭṭhānesu':'catūsu satipaṭṭhānesu',
 'cattaro satipaṭṭhānā':'cattāro satipaṭṭhānā',
 'cattāri purisayugāni aṭṭhapurisapugalā':'cattāri purisayugāni aṭṭha purisapuggalā',
 'cāttāro āhārā':'cattāro āhārā',
 'Cetana':'cetanā',
 'cetaso ekodibhava':'cetaso ekodibhāva',
 'cintamaya ñāṇa':'cintāmayañāṇa',
 'citta/umano/viññāna':'citta/mano/viññāṇa',
 'jihvā':'jivhā',
 'jihvāsamphassa':'jivhāsamphassa',
 'jihvāsamphassaviññāṇāyatana':'jivhāsamphassaviññāṇāyatana',
 'ñāṇamattāya patissatimattāya-mattāya':'ñāṇamattāya paṭissatimattāya',
 'ñūna-dassana':'ñāṇadassana',
 'taṇha':'taṇhā',
 'tattha devata':'tattha devatā',
 'tayo sikkhā':'tisso sikkhā',
 'tavatiṁsa':'tāvatiṃsa',
 'tī sikkha':'tisso sikkhā',
 'thinha':'thīna',
 'tripiṭaka, tipiṭaka':'tipiṭaka',
 'Dammarāja':'dhammarāja',
 'damma-nakkhatta':'dhammanakkhatta',
 'disā-pharana':'disāpharaṇa',
 'dukkhanirodhagāminiyā paṭipadāya ñaṇaṁ':'dukkhanirodhagāminiyā paṭipadāya ñāṇaṃ',
 'dukkhanirodhagāminī patipadā':'dukkhanirodhagāminī paṭipadā',
 'dhammavicayasambojjhaṅo':'dhammavicayasambojjhaṅgo',
 'dhammā ādikalyāṇā majjhimakalyāṇā pariyosānakalyāṇā':'dhammā ādikalyāṇā majjhekalyāṇā pariyosānakalyāṇā',
 'dhammānupassnā':'dhammānupassanā',
 'dhammōnu-passananā':'dhammānupassanā',
 'dhātuvavaṭṭhāna':'dhātuvavatthāna',
 'nakulupitā':'Nakulapitā',
 'nātivithāra nātisaṅkhepa naya':'nātivitthāra-nātisaṅkhepa-naya',
 'nāma-nūpa':'nāmarūpa',
 'Nippapam':'nippapañcaṃ',
 'nibbida':'nibbidā',
 'nibbidānupssanāñāṇa':'nibbidānupassanāñāṇa',
 'nirodha-sañña':'nirodhasaññā',
 'nivaraṇa':'nīvaraṇa',
 'nevasaññanāsaññāyatana':'nevasaññānāsaññāyatana',
 'pakāsaniyakammaṁ':'pakāsanīyakammaṃ',
 'pañca upādānakkhandā':'pañca upādānakkhandhā',
 'pañña':'paññā',
 'panna-indriyā':'paññindriya',
 'paṭicca samuppada':'paṭiccasamuppāda',
 'patibhāga-himitta':'paṭibhāganimitta',
 'patisambhidā':'paṭisambhidā',
 'patisalliyituṁ':'paṭisallīyituṃ',
 'pathama jhāna':'paṭhamajjhāna',
 'Panītam':'paṇītaṃ',
 'Pancakkhandhā':'pañcakkhandhā',
 'Parittasubhānā devā':'Parittasubhā devā',
 'Parittābhānā devā':'Parittābhā devā',
 'parīyādāna':'pariyādāna',
 'passadhi':'passaddhi',
 'pāccittya':'pācittiya',
 'Pāññā':'paññā',
 'pārileyyka':'Pālileyyaka',
 'pāsādanīya':'pasādanīya',
 'pubbenivasanussatiñāna':'pubbenivāsānussatiñāṇa',
 'pubbenivasānussati':'pubbenivāsānussati',
 'Pheṇapiṇḍu':'pheṇapiṇḍa',
 'bubbuḷu':'bubbuḷa',
 'Marīcikū':'marīcikā',
 'Brahmavihāra-bhāva-rā':'brahmavihārabhāvanā',
 'bhayatupāṭṭhāna':'bhayatupaṭṭhāna',
 'bhāva-taṇhā':'bhavataṇhā',
 'bhāva-nirodha':'bhavanirodha',
 'bhikhhu':'bhikkhu',
 'Maṇḍuka':'Maṇḍūka',
 'maraṇasannajavanacitta':'maraṇāsannajavanacitta',
 'Mahā Anula':'Mahā-Anuḷa',
 'mahākaruṇa samāpatti':'mahākaruṇāsamāpatti',
 'mahāvira':'mahāvīra',
 'Māgandiya':'Māgaṇḍiya',
 'mārana':'maraṇa',
 'Migāramatu':'Migāramātu',
 'micchāpatipadā':'micchāpaṭipadā',
 'muttamutta':'muttāmutta',
 'musāvāda veramaṇī':'musāvādā veramaṇī',
 'yathābhūtaṁ sammāppaññā':'yathābhūtaṃ sammappaññāya',
 'yathābhūta sammāppaññā':'yathābhūtaṃ sammappaññāya',
 'yathābhūta ñāṇaḍassana':'yathābhūtañāṇadassana',
 'yamaka pātihāriya':'yamakapāṭihāriya',
 'yāni-katā':'yānīkatā',
 'yoniso masikāra':'yoniso manasikāra',
 'Rahula':'Rāhula',
 'lokanirodhagāminiṁ paṭipada':'lokanirodhagāminiṃ paṭipadaṃ',
 'vacisaṁkhāra':'vacīsaṅkhāra',
 'vadanā':'vedanā',
 'vadanānupassanā':'vedanānupassanā',
 'vācīsaṅkhāro':'vacīsaṅkhāro',
 'vicikiccha':'vicikicchā',
 'Vijañana':'vijānana',
 'Viññāna':'viññāṇa',
 'viññānakkhandha':'viññāṇakkhandha',
 'viññāna-sota':'viññāṇasota',
 'Vipāka viññāna':'vipākaviññāṇa',
 'viññeyy':'viññeyya',
 'vittāra naya':'vitthāranaya',
 'vipariṇā':'vipariṇāma',
 'vipallaasā':'vipallāsā',
 'vipassanaa':'vipassanā',
 'Vibhava-tanhā':'vibhavataṇhā',
 'vimaṁsā':'vīmaṃsā',
 'vimittikkhandha':'vimuttikkhandha',
 'vimittiñāṇadassanakkhandha':'vimuttiñāṇadassanakkhandha',
 'vimittiññāṇadassanakkhandha':'vimuttiñāṇadassanakkhandha',
 'vimuttiññanadassanakkhandhaṁ':'vimuttiñāṇadassanakkhandhaṃ',
 'virāga-sañña':'virāgasaññā',
 'viriyam ārabbhati':'vīriyaṃ ārabhati',
 'vishddhi-magga':'Visuddhimagga',
 'Vedañā':'vedanā',
 'vedanānupassnā':'vedanānupassanā',
 'vedāna':'vedanā',
 'vepulla mahattam (…) lābhagga bāhusaca':'vepulla mahattaṃ (…) lābhagga bāhusacca',
 'vepulla mahattam (...) lābhagga bāhusaca':'vepulla mahattaṃ (...) lābhagga bāhusacca',
 'sakadāgāmīphala':'sakadāgāmiphala',
 'sakadāgāmīmagga':'sakadāgāmimagga',
 'sakkāya-ditthi':'sakkāyadiṭṭhi',
 'saṅkharupekkhā ñāṇa':'saṅkhārupekkhāñāṇa',
 'sañjānati':'sañjānāti',
 'saññākkhanda':'saññākkhandha',
 'saṇkhārakkhandha':'saṅkhārakkhandha',
 'Satipatthāna Sutta':'Satipaṭṭhāna Sutta',
 'Satī':'sati',
 'satthari, dhamme, saṅgh, sikkhā, samādhi':'satthari, dhamme, saṅghe, sikkhā, samādhi',
 'saddha pasannā':'saddhā pasannā',
 'Samkhārakkhanaha':'saṅkhārakkhandha',
 'sammasaṅkappa':'sammāsaṅkappa',
 'sammāppadhāna':'sammappadhāna',
 'Sammāsambudha':'sammāsambuddha',
 'samyattanikaṁ viññānaṁ':'saṃvattanikaṃ viññāṇaṃ',
 'salakatto anuttaro':'sallakatto anuttaro',
 'saḷāytana':'saḷāyatana',
 'sankhāra':'saṅkhāra',
 'savatthi':'Sāvatthī',
 'sāmadhi':'samādhi',
 'sāmadhikkhandha':'samādhikkhandha',
 'sāvakasannpāta':'sāvakasannipāta',
 'silabbata-parāmāsa':'sīlabbataparāmāsa',
 'sīlabbatapatāmāsa':'sīlabbataparāmāsa',
 'sīlabhatapatāmāsa':'sīlabbataparāmāsa',
 'sīlavissuddhi':'sīlavisuddhi',
 'Suttas':'sutta',
 'Sumanadevi':'Sumanadevī',
 'sumangala-vilāsinī':'Sumaṅgalavilāsinī',
 'surāmerayamajjapamādaṭṭhān':'surāmerayamajjapamādaṭṭhānā',
 'sotapatti':'sotāpatti',
 'sottāpattiphala':'sotāpattiphala',
 'sottāpattimagga':'sotāpattimagga',
 'Ṣākyamuni':'Sakyamuni',
 '\\]pharusā':'pharusā',
 '\\]sabbasaṅkhāra':'sabbasaṅkhāra',
 'so Bhagavāarahaṁ sammāsambuddho vijjācaraṇasampanno sugato lokavidūanu':'so bhagavā arahaṃ sammāsambuddho vijjācaraṇasampanno sugato lokavidū anuttaro',
 # 2026-11-18 17:41 사용자 결정: 고요한소리 '검토 필요' 20어 가운데 19어를 사용자가 정한 철자로 고침(seṭṭho sañjitā는 그대로 둠)
 'ajjaram':'ajaraṃ',
 'anisaṁso':'ānisaṃso',
 'baḥuli':'bahulī',
 'Catunnaṁ ariyasacca':'catu ariyasacca',
 'dhammassānī':'dhammassāmī',
 'Dukkhanirodhagāminiyā paṭipadāya ariyasacca':'dukkhanirodhagāmini paṭipadā ariyasaccaṃ',
 'Dukkhanirodhassa ariyasacca':'dukkhanirodhaṃ ariyasaccaṃ',
 'dukkhasamudayam ariyasacca':'dukkhasamudayaṃ ariyasaccaṃ',
 'Dukkhasamudayassa ariyasacca':'dukkhasamudayaṃ ariyasaccaṃ',   # 사용자 목록에 따로 없어 위와 같은 철자로 봄(추정)
 'Dukkhassa ariyasacca':'dukkha ariyasacca',
 'Kammabhāra':'kammabhava ?',
 'Kamnā':'karuṇā',
 'Parāyaṇam':'parāyaṇaṃ ? / pārāyanaṃ ?',
 'patissallīni':'paṭisallīna',
 'pañcahi kāmaguṇe':'pañca kāmaguṇa',
 'Samjanana':'sañjānana',
 'sirina':'Sirimā',
 'Sākyamuni':'Sakyamuni',
 'vimokho':'vimokkho',
}

AL=['a','ā','i','ī','u','ū','e','o','ṃ','k','kh','g','gh','ṅ','c','ch','j','jh','ñ','ṭ','ṭh','ḍ','ḍh','ṇ','t','th','d','dh','n','p','ph','b','bh','m','y','r','l','ḷ','v','s','h']
RK={c:i for i,c in enumerate(AL)}
def pkey(w):
    w=unicodedata.normalize('NFC',w.lower()).replace('ṁ','ṃ')
    w=re.sub(r'[^a-zāīūṅñṭḍṇḷṃ]','',w)
    out=[];i=0
    while i<len(w):
        two=w[i:i+2]
        if len(two)==2 and two in RK: out.append(RK[two]);i+=2
        else: out.append(RK.get(w[i],99));i+=1
    return out

def to_md(path):
    if path.endswith('.md'): return open(path,encoding='utf-8').read()
    import tempfile, zipfile as zf
    d=tempfile.mkdtemp()
    subprocess.run(['unzip','-q','-o',path,'-d',d],check=True)
    dx=os.path.join(d,'word','document.xml')
    if os.path.getsize(dx)<30_000_000:   # 보통 크기: 그대로 변환
        return subprocess.run(['pandoc',path,'-t','gfm','--wrap=none'],capture_output=True,text=True,check=True).stdout
    # 큰 파일(예: 3,215어 통합본, document.xml 79MB)은 pandoc이 메모리 부족으로 죽으므로
    # 표제어(Heading3) 경계에서 여러 조각으로 나눠 변환한 뒤 이어 붙인다
    doc=open(dx,encoding='utf-8').read()
    bs=doc.index('<w:body>')+len('<w:body>'); be=doc.rindex('<w:sectPr')
    head,body,tail=doc[:bs],doc[bs:be],doc[be:]
    h3=[m.start() for m in re.finditer(r'<w:p[ >](?:(?!</w:p>).){0,400}?w:pStyle w:val="Heading3"',body)]
    n=max(2,len(doc)//20_000_000+1)
    cuts=[0]+sorted(set(min(h3,key=lambda x:abs(x-len(body)*i//n)) for i in range(1,n)))+[len(body)]
    files=[os.path.relpath(os.path.join(r,f),d) for r,_,fs in os.walk(d) for f in fs]
    out=[]
    for i in range(len(cuts)-1):
        p=os.path.join(d,f'part{i}.docx')
        with zf.ZipFile(p,'w',zf.ZIP_DEFLATED) as z:
            for f in sorted(files,key=lambda f:f!='[Content_Types].xml'):
                if f.startswith('part'): continue
                if f=='word/document.xml': z.writestr(f,head+body[cuts[i]:cuts[i+1]]+tail)
                else: z.write(os.path.join(d,f),f)
        out.append(subprocess.run(['pandoc',p,'-t','gfm','--wrap=none'],capture_output=True,text=True,check=True).stdout)
    return '\n'.join(out)

out=sys.argv[1]; man=json.load(open(sys.argv[2]))
skipped=[m for m in man if m.get('skip')]          # 10MB가 넘어 내려받지 못한 파일 등: 기록만 남김
man=[m for m in man if not m.get('skip')]
for m in man: m['_md']=unicodedata.normalize('NFC',to_md(m['path'])); m['_n']=len(re.findall(r'^### ',m['_md'],re.M))
man.sort(key=lambda m:(m['_n'],m.get('modifiedTime','')))   # 작은 파일 → 통합본 (뒤가 이김)
os.makedirs(out,exist_ok=True)
entries={}; intros={}; srcinfo=[]
for m in man:
    md=m['_md']
    t=re.search(r'^# (빠알리 용어 개념정의.*)$',md,re.M) or re.search(r'^# (?!차례)(.*)$',md,re.M)
    title=t.group(1).strip() if t else m.get('name','')
    g=re.search(r'^## 일러두기\s*\n(.*?)(?=^## )',md,re.M|re.S)
    intros[title]=g.group(1).strip() if g else ''
    n=0
    for p in re.split(r'^### ',md,flags=re.M)[1:]:
        head,_,body=p.partition('\n')
        body=re.split(r'^## ',body,flags=re.M)[0].strip()
        term=head.strip()
        if not term: continue
        entries[term]={'t':term,'md':body,'src':title}; n+=1
    srcinfo.append({'id':m.get('id'),'name':m.get('name',os.path.basename(m['path'])),'modifiedTime':m.get('modifiedTime'),'title':title,'terms':n})

# 다른 판본·VRI 철자(ALTV: 확인된 다른 표기) / 문헌 철자로 보이는 형태(ALTG: '검토 필요', 추정) — 표제어 아래에 보이고 검색된다
ALTV={
"avyākata": ["abyākata"],
"avyāpajjha": ["abyāpajjha","abyāpajja","abyābajjha"],
"avyāpāra": ["abyāpāra"],
"vyāpāra": ["byāpāra"],
"vigatavyāpādo": ["vigatabyāpādo"],
"vyārosanā": ["byārosanā"],
"lokavyūhadevā": ["lokabyūhā devā"],
"vyāpāda": ["byāpāda"],
"supaṭipanno": ["suppaṭipanno"],
"supaṭipanno saṅgho": ["suppaṭipanno saṅgho"],
"uju-paṭipanno": ["ujuppaṭipanno"],
"ñāya-paṭipanno": ["ñāyappaṭipanno"],
"samīci-paṭipanno": ["sāmīcippaṭipanno"],
"pāṭimokkha": ["pātimokkha"],
"ānāpānasatisamādhi": ["ānāpānassatisamādhi"],
"viññāṇūpādānakkhandho": ["viññāṇupādānakkhandho"],
"vedanūpādānakkhandho": ["vedanupādānakkhandho"],
"saññūpādānakkhandho": ["saññupādānakkhandho"],
"saṁkhārūpādānakkhandho": ["saṅkhārupādānakkhandho"],
"maggasiddhajhāna": ["maggasiddhajjhāna"],
"pādakajhāna": ["pādakajjhāna"],
"upapattisiddhajhāna": ["upapattisiddhajjhāna"],
"diṭṭhinijjhānakhanti": ["diṭṭhinijjhānakkhanti"],
"cātummahārājikā devā": ["cātumahārājikā devā"],
"upekhāsambojjhaṅga": ["upekkhāsambojjhaṅga"],
"sīvathikā": ["sivathikā"],
"siriṁsapā": ["sarīsapā","sarīsapa"],
"Kāraḷiyagiri": ["Karuḷiyagiri"],
"sukaṭakamma": ["sukatakamma"],
"paṭikkūla": ["paṭikūla"],
"parittā paṭhavisaññā": ["parittā pathavīsaññā"],
"paṭhavī āpo tejo vāyo": ["pathavī āpo tejo vāyo"],
"Illīsa": ["Illisa"],
"vimokha": ["vimokkha"],
"Saṅkicca sāmaṇera": ["Saṃkicca sāmaṇera"],
"ghāṇaviññāṇadhātu": ["ghānaviññāṇadhātu"],
"viriya": ["vīriya"],
"vīriya": ["viriya"],
"Anula": ["Anuḷa","Anuḷā"],
"arūpa-jhāna": ["arūpajjhāna"],
"Uccāvālika": ["uccavālika"],
"Kaṭakandhakāra": ["kaṭaandhakāra"],
"Mahāvaṭṭani": ["Mahāvattani"],
"adhipateyya": ["ādhipateyya"],
"anusāsani pāṭihāriya": ["anusāsanīpāṭihāriya"],
"upaṭṭhitakāyasati": ["upaṭṭhitakāyassati"],
"kāyagatā-sati": ["kāyagatāsati"],
"muñcitukamyatā ñāṇa": ["muccitukamyatāñāṇa"],
"saññama": ["saṃyama"],
"saṅkhittaṃ cittaṃ": ["saṃkhittaṃ cittaṃ"],
"saṅkilesa": ["saṃkilesa"],
"cakkavattin": ["cakkavattī"],
"Mahā Rohaṇagutta": ["Mahārohanagutta"],
"sekhā": ["sekkhā"],
"sobhana": ["sobhaṇa"],
"pariyuṭṭhānakilesa": ["kilesapariyuṭṭhāna"],
"avyāpāda": ["abyāpāda"],
"iddhividhāñāṇa": ["iddhividhañāṇa"],
"cetaso upakkilese dubbalīkaraṇe": ["cetaso upakkilese paññāya dubbalīkaraṇe"],
"seṭṭho sañjitā": ["seṭṭho sajitā"],
"jānati": ["jānāti"],
"Māyūpamañca": ["māyūpamaṃ ca"]
}
# 2026-11-18 17:41: 고요한소리 '검토 필요' 19어는 사용자가 철자를 정해 FIX로 옮김 → ALTG에서 뺌
ALTG={
"Anula": ["Anuḷa","Anuḷā"],
"ākiṁcaññāyatana": ["ākiñcaññāyatana"],
"kabaliṅkārāhāra": ["kabaḷīkārāhāra"],
"kabaliṅkāro āhāro oḷāriko sukhumo": ["kabaḷīkāro āhāro oḷāriko sukhumo"],
"gambhīratta": ["gambhīrattha"],
"gāhagāha": ["gāhagāhaka"],
"gāhamutta": ["gāhamuttaka"],
"muttagāha": ["muttagāhaka"],
"dukkhanirodhaariyasaccāni": ["dukkhanirodhaṃ ariyasaccaṃ"],
"dukkhasamudayaariyasaccāni": ["dukkhasamudayaṃ ariyasaccaṃ"],
"natthivāda": ["natthikavāda"],
"parikappacita attha": ["parikappasiddha attha"],
"sabhāvacita attha": ["sabhāvasiddha attha"],
"punapuna": ["punappunaṃ"],
"viramana, veramaṇī, virati": ["viramaṇa"],
"saddhāvimutti": ["saddhāvimutta"],
"samadhikā cetovimutti": ["sāmayikā cetovimutti","sāmāyikā cetovimutti"]
}
# --- 표기 오류 바로잡기와 합치기 ---
raw_n=len(entries)
# 사이트에서 빼는 표제어(원본 표제어 철자 기준). 사용자 결정.
#  (2026-11-18) jānati·Māyūpamañca는 원문에 실제로 있는 형태(jānati 게송 5회, māyūpamañca 4회)라 FIX에서 빼고 다른 표기(ALTV)로 둠. samadhikā cetovimutti는 sāmayikā·sāmāyikā 둘 다 병기(VRI: sāmayika- 51회, sāmāyika- 33회).
#  vipallaasā: 고요한소리 번역어(관/위빠싸나)가 vipallāsa(전도)와 맞지 않아 잘못된 표제어로 봄 (2026-11-18)
EXCLUDE={'vipallaasā'}
excluded=[t for t in entries if t in EXCLUDE]
for t in excluded: del entries[t]
fixed_from=[t for t in entries if t in FIX]
PUB=['초기불전연구원','한국빠알리성전협회','불방일','고요한소리']
TRRE=re.compile(r'^\*\*출판사 번역어\*\*\s*—\s*(.*)$',re.M)
def trparse(md):
    m=TRRE.search(md); d={}
    if not m: return d
    parts=re.split(r'(?:^| · )('+'|'.join(PUB)+r'): ',m.group(1))
    for i in range(1,len(parts)-1,2): d[parts[i]]=parts[i+1].strip()
    return d
groups={}
for term in list(entries):
    groups.setdefault(FIX.get(term,term),[]).append(term)
new={}
for fixed,olds in groups.items():
    if len(olds)==1 and olds[0]==fixed: new[fixed]=entries[fixed]; continue
    olds.sort(key=lambda t:(t!=fixed,))           # 원래 바른 철자 항목이 있으면 그것을 앞에
    base=dict(entries[olds[0]]); base['t']=fixed
    if len(olds)>1:
        trs={p:[] for p in PUB}
        for t in olds:
            for p,v in trparse(entries[t]['md']).items():
                for x in v.split(' / '):
                    if x!='미수록' and x not in trs[p]: trs[p].append(x)
        line='**출판사 번역어** — '+' · '.join(f"{p}: {' / '.join(trs[p]) if trs[p] else '미수록'}" for p in PUB)
        body=TRRE.sub(lambda m:line,base['md'],count=1) if TRRE.search(base['md']) else line+'\n\n'+base['md']
        for t in olds[1:]:
            body+='\n\n#### 같은 낱말의 다른 항목에서 옮긴 내용\n\n'+TRRE.sub('',entries[t]['md'],count=1).strip()
        base['md']=body
    new[fixed]=base
# 한글 음역 교정(2026-11-18 사용자 요청: Bhaddanta 바단따→밧단따, -vaṃsa 비왐사→비왕사). 출판사 번역어 줄은 고치지 않는다.
TRANSLIT=[('바단따','밧단따'),('비왐사','비왕사')]
def translit(md):
    out=[]
    for l in md.split('\n'):
        if not l.startswith('**출판사 번역어**'):
            for a,b in TRANSLIT: l=l.replace(a,b)
        out.append(l)
    return '\n'.join(out)
for e in new.values(): e['md']=translit(e['md'])
for e in new.values():                                   # 본문 링크도 바른 철자로
    e['md']=re.sub(r'\]\(#p\d+_','](#',e['md'])   # 통합본의 #p3_낱말 꼴 링크 → #낱말
    for o,f in FIX.items():
        if '](#'+o+')' in e['md']: e['md']=e['md'].replace('](#'+o+')','](#'+f+')')
entries=new
for m in skipped: srcinfo.append({'id':m.get('id'),'name':m.get('name'),'modifiedTime':m.get('modifiedTime'),'title':m.get('name'),'terms':0,'skipped':m.get('skip')})

# --- 같은 낱말인데 표제어가 따로 있는 경우: 서로의 출판사 번역어를 함께 보이기(2026-11-18 사용자 요청) ---
SAME=[('pañca upādānakkhandhā','pañcupādānakkhandhā')]   # 사용자가 직접 짝지은 것
def _key(t):
    t=t.lower().replace('ṁ','ṃ').replace('â','ā').replace('ê','e').replace('ô','o')
    return re.sub(r"[\s\-’'‘.,/()]",'',t)
_par={}
def _f(x):
    while _par.get(x,x)!=x: x=_par[x]
    return x
def _u(a,b):
    if a in entries and b in entries and a!=b: _par[_f(a)]=_f(b)
_bykey={}
for t in entries: _bykey.setdefault(_key(t),[]).append(t)
for v in _bykey.values():
    for t in v[1:]: _u(v[0],t)                       # 띄어쓰기·하이픈·ṁ/ṃ·â만 다른 표제어
for t,alts in ALTV.items():
    for a in alts: _u(t,a)                            # 다른 판본 표기가 따로 표제어로 있는 경우
for a,b in SAME: _u(a,b)
_low={t.lower():t for t in entries}
_P=r"[A-Za-zāīūṅñṭḍṇḷṃṁâ’\-]+(?: [A-Za-zāīūṅñṭḍṇḷṃṁ’\-]+){0,3}"
_R=[re.compile(r"(?:“|”|‘|’|\*\*)?("+_P+r")(?:”|’|\*\*)?(?: 항목)?(?:\([^)]*\))?\s*(?:와|과)\s*같은 낱말"),
    re.compile(r"같은 낱말의 다른 표기[^.\n]{0,12}?(?:→\s*)?(?:\*\*)?("+_P+r")")]
for t,e in entries.items():                          # 본문이 "X와 같은 낱말"이라고 밝힌 경우
    for l in e['md'].split('\n')[:16]:
        for R in _R:
            for m in R.finditer(l):
                w=m.group(1).strip().lower()
                if w in _low and _low[w]!=t: _u(t,_low[w])
_grp={}
for t in entries: _grp.setdefault(_f(t),[]).append(t)
nsame=0
for g in _grp.values():
    if len(g)<2: continue
    for t in g:
        others=[o for o in sorted(g,key=lambda x:(pkey(x),x)) if o!=t]
        parts=[]
        for o in others:
            d=trparse(entries[o]['md']); tr=' · '.join(f'{p}: {v}' for p,v in d.items() if v and v!='미수록')
            parts.append(f'[{o}](<#{o}>)'+(f' ({tr})' if tr else ' (출판사 번역어 없음)'))
        line='**같은 낱말의 다른 표제어** — '+' / '.join(parts)
        md=entries[t]['md']; m=TRRE.search(md)
        entries[t]['md']=md[:m.end()]+'\n\n'+line+md[m.end():] if m else line+'\n\n'+md
        nsame+=1
order=sorted(entries,key=lambda k:(pkey(k),k))
idx=[];chunks=[[]];size=0
for i,k in enumerate(order):
    e=entries[k]
    tr=re.search(r'\*\*출판사 번역어\*\*\s*—\s*(.*)',e['md'])
    if size>3_000_000: chunks.append([]); size=0
    chunks[-1].append([i,e['md']]); size+=len(e['md'].encode())
    x={'t':e['t'],'tr':tr.group(1).strip() if tr else '','c':len(chunks)-1}
    if ALTV.get(k): x['av']=ALTV[k]
    if ALTG.get(k): x['ag']=ALTG[k]
    idx.append(x)
for f in glob.glob(f'{out}/concepts-*.json'): os.remove(f)
for j,c in enumerate(chunks):
    json.dump(c,open(f'{out}/concepts-{j}.json','w'),ensure_ascii=False,separators=(',',':'))
upd=datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=9))).strftime('%Y-%m-%d')
# 실제로 항목을 내준 파일(통합본 우선)과 그 일러두기
import collections
contrib=collections.Counter(entries[k]['src'] for k in order)
used=[t for t,_ in contrib.most_common()]
# 사이트에서 원본과 달라진 점을 일러두기 맨 앞에 싣는다(숫자는 만들 때마다 새로 계산)
nfix=sum(1 for t in fixed_from); nexc=len(excluded); nmerge=raw_n-nexc-len(idx)
nv=sum(1 for x in idx if x.get('av')); ng=sum(1 for x in idx if x.get('ag'))
site_note=f"""원본 개념정의 파일의 표제어는 **{raw_n:,}어**이지만, 이 사이트에는 **{len(idx):,}어**가 실려 있다(합쳐서 {nmerge}어, 빼서 {nexc}어 줄어듦). 원본 파일은 고치지 않았고, 사이트에 올릴 때만 아래처럼 바꾸었다.

- **표제어 표기 오류 바로잡기**: 출판사 색인에서 옮긴 표제어 가운데 철자가 6차 결집본(VRI)·미얀마어 삼장사전에 없고 바른 철자가 분명한 **{nfix}어**는 문헌의 철자로 고쳐 실었다(예: aupasampadā → upasampadā, bhikhhu → bhikkhu, karunā → karuṇā). 잘못된 철자의 표제어는 따로 남기지 않았다. 바른 철자를 하나로 정하기 어려웠던 고요한소리 표제어 가운데 19어는 용어집 편집자가 정한 철자로 고쳤다(예: Kamnā → karuṇā, sirina → Sirimā). 고친 철자 끝의 “?”는 확정하지 못한 후보라는 뜻이다.
- **표제어가 줄어든 까닭**: 고친 철자가 이미 있는 표제어와 같아지면(예: karunā → karuṇā), 또는 서로 다른 오기가 같은 철자로 고쳐지면(예: vedāna·Vedañā·vadanā → vedanā) 두 항목을 하나로 합쳤다. 그래서 표제어가 **{nmerge}어** 줄었다. 합친 항목의 출판사 번역어 줄에는 두 항목의 번역어를 모두 모았고, 옮겨 온 본문은 “같은 낱말의 다른 항목에서 옮긴 내용” 아래에 그대로 두었다. 각 항목 본문의 철자 설명(“…의 오기로 보인다” 등)은 원본 그대로이다.
"""+(f"- **뺀 표제어**: 출판사 번역어와 낱말이 맞지 않아 잘못 옮겨진 것으로 보이는 표제어 {nexc}어({', '.join(excluded)})는 사이트에서 뺐다.\n" if nexc else '')+f"""- **그대로 둔 표제어**: 오기로 보이지만 바른 철자를 하나로 정하기 어려운 **{ng}어**는 표제어를 그대로 두고, 문헌 철자로 보이는 형태를 표제어 아래에 “문헌 철자로 보이는 형태(추정)”로 함께 보였다.
- **다른 판본 표기**: 판본에 따라 달리 적는 낱말(예: avyākata/abyākata, seṭṭho sañjitā/sajitā)은 오류로 보지 않고 그대로 두었으며, 다른 판본 표기를 표제어 아래에 함께 보였다({nv}어). 이 표기들로 검색해도 해당 표제어가 나온다.
- **같은 낱말의 다른 표제어**: 띄어쓰기·하이픈·연음·판본 표기만 다를 뿐 같은 낱말인 표제어가 따로 있을 때({nsame}어)는 표제어를 그대로 두고, 출판사 번역어 줄 아래에 “같은 낱말의 다른 표제어”와 그 출판사 번역어를 함께 적어 양쪽에서 확인할 수 있게 했다.
- **한글 음역 교정**: 닛사야 저자 이름 등에서 Bhaddanta는 “밧단따”, -vaṃsa는 “-왕사”(예: 자나까비왕사, 난다왕사)로 적었다.
- **출판사 번역어**는 출판사 표기 그대로이다. 다만 원자료 입력 과정에서 생긴 흔적(짝 없는 괄호, “(,)”)은 정리했고, 번역어 뒤에 붙은 번호(예: 음식2)는 개념정의에서는 뺐다(출판사별 용어집·번역어 대조표에는 그대로 있다)."""
intro_list=[{'title':'이 검색 사이트에 실린 개념정의','md':site_note}]+[{'title':t,'md':intros.get(t,'')} for t in used if intros.get(t)]
json.dump({'updated':upd,'n':len(idx),'chunks':len(chunks),
           'intro':intro_list,
           'sources':[{'title':t,'n':contrib[t]} for t in used],
           'terms':idx},open(f'{out}/concepts-index.json','w'),ensure_ascii=False,separators=(',',':'))
json.dump({'updated':upd,'terms':len(idx),'raw_terms':raw_n,'fixed':len([1 for k in FIX]),'chunks':len(chunks),'sources':srcinfo},open(f'{out}/build-info.json','w'),ensure_ascii=False,indent=1)
print(raw_n,'raw terms →',len(idx),'terms',len(chunks),'chunks'); print(json.dumps(srcinfo,ensure_ascii=False))
