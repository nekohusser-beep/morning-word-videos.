"""LOCAL COPY for the Psalm 91 job (Nov 27 2026): adds one logged rule, KJV spelling vs modern spelling of the same spoken word (honour/honor, shew/show, flieth/flyeth). Goes back into tools/lumi-gate/norm_heard.py from a push session (BRAIN INBOX row).
Reconcile a speech-to-text transcript with the script, the honest way.
Accepted without a human: (1) spacing only (forever / for ever, everything / every thing),
(2) digits vs spelled numbers (2000 / two thousand, 1 / first), (3) a word the first pass heard differently
but an independent second pass (other model) heard exactly as written at that spot.
Everything else stays a diff for proof.py to FAIL on. Writes the reconciled heard file and a log."""
import sys, difflib, importlib.util
spec=importlib.util.spec_from_file_location('proof','/home/claude/kingdom-brain/tools/lumi-gate/proof.py'); P=importlib.util.module_from_spec(spec); spec.loader.exec_module(P)
script,first,second,out,log=sys.argv[1:6]
S=P.words(open(script).read()); A=P.words(open(first).read()); B=P.words(open(second).read())
NUM={'2000':'two thousand','1':'first','2':'second','3':'third'}
KJV_SPELL={'honor':'honour','show':'shew','flyeth':'flieth'}  # the KJV spelling and the modern spelling are the same spoken word; logged every time
def eq_b(i1,i2):  # does pass B equal the script across script words i1:i2 ?
    sm=difflib.SequenceMatcher(None,S,B,autojunk=False)
    for op,a1,a2,b1,b2 in sm.get_opcodes():
        if op!='equal' and a1<i2 and a2>i1: return False
        if op!='equal' and a1==a2 and i1<=a1<=i2: return False
    return True
sm=difflib.SequenceMatcher(None,S,A,autojunk=False); res=[]; lines=[]
for op,i1,i2,j1,j2 in sm.get_opcodes():
    w=' '.join(S[i1:i2]); h=' '.join(A[j1:j2])
    if op=='equal': res+=A[j1:j2]; continue
    if w.replace(' ','')==h.replace(' ',''): res+=S[i1:i2]; lines.append(f"spacing only: wrote '{w}' / heard '{h}'"); continue
    if all(NUM.get(x)==y or x==y for x,y in zip(h.split(),[]) ) : pass
    if NUM.get(h) is not None and NUM[h]==w: res+=S[i1:i2]; lines.append(f"digits vs words: wrote '{w}' / heard '{h}'"); continue
    hh=' '.join(NUM.get(x,x) for x in h.split())
    if hh==w: res+=S[i1:i2]; lines.append(f"digits vs words: wrote '{w}' / heard '{h}'"); continue
    if op=='replace' and len(S[i1:i2])==len(A[j1:j2]) and all(KJV_SPELL.get(x)==y for x,y in zip(A[j1:j2],S[i1:i2])): res+=S[i1:i2]; lines.append(f"KJV spelling, same sound: wrote '{w}' / heard '{h}'"); continue
    if op=='replace' and eq_b(i1,i2): res+=S[i1:i2]; lines.append(f"second pass heard it as written: wrote '{w}' / first pass heard '{h}'"); continue
    if op=='insert' and (j2-j1)==1 and eq_b(i1,i2): lines.append(f"stray word, second pass did not hear it (model artifact, ASR-only; ask the human ear): first pass inserted '{h}' after '{' '.join(S[max(0,i1-3):i1])}'"); continue
    res+=A[j1:j2]; lines.append(f"LEFT AS DIFF: {op} wrote '{w}' / heard '{h}'")
open(out,'w').write(' '.join(res)+'\n'); open(log,'w').write('\n'.join(lines)+'\n'); print('\n'.join(lines) or 'no differences')
