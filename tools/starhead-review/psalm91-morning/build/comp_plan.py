# Psalm 91 composite plan: Neko (Flow avatar) opening + prayer close around the narrated teaching.
# (name, src_start a, src_end b, sentences, gap_before) ; a/b taken from spans.json (onset - 0.06 pre-roll, end + ~0.25 tail)
import json
CL='/home/claude/ps91/clips'; SRC='/home/claude/ps91/src'; VC='/home/claude/ps91/vc'
SPANS=json.load(open('/home/claude/ps91/spans.json'))
SEAM1=35.4525; SEAM2=406.2405; ENDCARD=6.0
def n(x): return 'ps91-'+x
OPEN=[
 ('before-you-walk-out-that-door',0.22,7.05,["Before you walk out that door today, give me a few minutes.","You already know what's out there."],0.0),
 ('the-email-youve-been-dreading-the',0.61,7.05,["The email you've been dreading.","The drive.","The conversation you keep putting off."],0.18),
 ('and-youre-about-to-walk-into',0.65,7.25,["And you're about to walk into all of it with nothing between you and the day but a cup of coffee."],0.18),
 ('this-psalm-is-for-the-person',0.41,7.92,["This psalm is for the person standing at that door.","People have prayed it in hospital hallways, before shifts,"],0.18),
 ('and-on-the-way-to-jobs',0.00,None,["and on the way to jobs they were scared to lose.","Pray it with me, and then go."],0.18),
]
CLOSE=[
 ('so-here-is-the-prayer-pray',2.45,6.85,["So here is the prayer.","Pray it out loud if you can."],0.0),
 ('father-i-am-stepping-out-the',0.23,7.50,["Father, I am stepping out the door, and I am putting this day under Your wing."],0.20),
 ('cover-my-house-while-i-am',0.31,7.42,["Cover my house while I am gone.","Cover the ones I love, wherever they are, right now."],0.20),
 ('when-a-trap-is-set-show',0.32,7.58,["When a trap is set, show me before I step.","When fear comes, remind me where I dwell."],0.20),
 ('send-your-angels-ahead-of-me',0.35,7.50,["Send your angels ahead of me, and let me come home tonight with a thankful heart."],0.20),
 ('i-ask-it-in-the-name',2.50,6.50,["I ask it in the name of Jesus Christ, Amen."],0.30),
 ('type-amen-and-send-this-to',0.19,6.95,["Type, amen, and send this to a friend who needs it.","Have a blessed day and remember the word for today."],0.50),
]
def place(seq,t0,fill_to=None):
    t=t0; out=[]
    for i,(nm,a,b,s,g) in enumerate(seq):
        t+=g
        if b is None: b=a+(fill_to-t)
        out.append(dict(name=nm,key=n(nm),a=a,b=b,t=t,sent=s)); t+=b-a
    return out,t
OPENP,OPEN_END=place(OPEN,0.0,fill_to=SEAM1)
CLOSEP,CLOSE_END=place(CLOSE,0.0)
CLOSE_LEN=CLOSE_END+ENDCARD          # card follows the last clip
TOTAL_NEW=SEAM2+CLOSE_LEN
if __name__=='__main__':
    print('open end',round(OPEN_END,3),'seam',SEAM1)
    for x in OPENP: print(x['name'][:28].ljust(28),round(x['t'],2),round(x['t']+x['b']-x['a'],2),'a',x['a'],'b',round(x['b'],2))
    print('close end',round(CLOSE_END,2),'+card',ENDCARD,'=',round(CLOSE_LEN,2),'TOTAL_NEW',round(TOTAL_NEW,2))
    for x in CLOSEP: print(x['name'][:28].ljust(28),round(x['t'],2),round(x['t']+x['b']-x['a'],2))
