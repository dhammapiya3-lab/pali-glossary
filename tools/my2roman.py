"""미얀마 글자로 쓴 빠알리 → 로마자(빠알리 표준 표기). 삼장사전 표제어를 로마자로도 찾게 하려는 용도."""
import re
C={'က':'k','ခ':'kh','ဂ':'g','ဃ':'gh','င':'ṅ','စ':'c','ဆ':'ch','ဇ':'j','ဈ':'jh','ည':'ññ','ဉ':'ñ','ဋ':'ṭ','ဌ':'ṭh','ဍ':'ḍ','ဎ':'ḍh','ဏ':'ṇ',
   'တ':'t','ထ':'th','ဒ':'d','ဓ':'dh','န':'n','ပ':'p','ဖ':'ph','ဗ':'b','ဘ':'bh','မ':'m','ယ':'y','ရ':'r','လ':'l','ဝ':'v','သ':'s','ဟ':'h','ဠ':'ḷ'}
IND={'အ':'a','အာ':'ā','ဣ':'i','ဤ':'ī','ဥ':'u','ဦ':'ū','ဧ':'e','ဩ':'o','ဪ':'o'}
V={'ါ':'ā','ာ':'ā','ိ':'i','ီ':'ī','ု':'u','ူ':'ū','ေ':'e','ော':'o','ေါ':'o','ေါ်':'o'}
VIR='္'; ASAT='်'; ANU='ံ'; MED={'ျ':'y','ြ':'r','ွ':'v','ှ':'h'}
def conv(s):
    s=s.replace('ဿ','သ္သ').replace('ဥ်','ñ').replace('‌','').replace('​','')
    s=s.replace('ဦ','ဦ')
    out=[];i=0;n=len(s)
    while i<n:
        ch=s[i]
        if ch=='အ' or ch in IND:
            if ch=='အ':
                nx=s[i+1:i+3]
                if nx.startswith('ော'): out.append('o');i+=3;continue
                if nx[:1]=='ေ': out.append('e');i+=2;continue
                if nx[:1] in('ါ','ာ'): out.append('ā');i+=2;continue
                if nx[:1]=='ိ': out.append('i');i+=2;continue
                if nx[:1]=='ီ': out.append('ī');i+=2;continue
                if nx[:1]=='ု': out.append('u');i+=2;continue
                if nx[:1]=='ူ': out.append('ū');i+=2;continue
                out.append('a');i+=1;continue
            out.append(IND[ch]);i+=1
            if i<n and s[i]=='ီ' and ch=='ဥ': out[-1]='ū';i+=1
            continue
        if ch in C:
            base=C[ch];i+=1
            while i<n and s[i] in MED: base+=MED[s[i]];i+=1
            if i<n and s[i]==VIR: out.append(base);i+=1;continue      # 겹자음 앞(모음 없음)
            if i<n and s[i]==ASAT: out.append(base);i+=1;continue
            vow='a'
            if i<n and s[i]=='ေ':
                if s[i+1:i+2] in('ာ','ါ'): vow='o';i+=2
                else: vow='e';i+=1
                if i<n and s[i]==ASAT: i+=1
            elif i<n and s[i] in V: vow=V[s[i]];i+=1
            out.append(base+vow)
            if i<n and s[i]==ANU: out.append('ṃ');i+=1
            continue
        if ch==ANU: out.append('ṃ');i+=1;continue
        out.append(ch if not 'က'<=ch<='႟' else '');i+=1
    return ''.join(out)
if __name__=='__main__':
    for w in ['သတိ','အကနိဋ္ဌ','ဓမ္မ','သမ္ပဇည','နိဗ္ဗာန','ဗုဒ္ဓ','သံသာရ','ပဋိစ္စသမုပ္ပါဒ','ဥပေက္ခာ','ဩကာသ','ဧကဂ္ဂတာ','မေတ္တာ','ကော','ဒုက္ခ']:
        print(w,conv(w))
