import json, re, pythonbible as pb
def kjv(ref):
    refs=pb.get_references(ref); vids=pb.convert_references_to_verse_ids(refs)
    t=' '.join(pb.get_verse_text(v, version=pb.Version.KING_JAMES).strip() for v in vids)
    return re.sub(r'\s+',' ',re.sub(r'[\[\]]','',t)).strip()
# ('n', text) narration ; ('v', display ref, pythonbible ref, [red key words]) verse ; ('s', tag) section start
S=[
('s','hook'),
('n',"Before you walk out that door today, give me a few minutes. You already know what's out there. The email you've been dreading. The drive. The conversation you keep putting off. And you're about to walk into all of it with nothing between you and the day but a cup of coffee."),
('n',"This psalm is for the person standing at that door. People have prayed it in hospital hallways, before shifts, and on the way to jobs they were scared to lose. Pray it with me, and then go."),
('s','dwell'),
('n',"Here is how it starts. Psalm 91, verses 1 and 2."),
('v',"Psalm 91:1-2","Psalms 91:1-2",["secret place","refuge","fortress","trust"]),
('n',"Look at the word dwelleth. That's somebody who lives there. Not a person who stops by when the car breaks down. This one is for an ordinary Tuesday, when nobody is watching and nothing is on fire. When's the last time you prayed before you left the house, instead of after something went wrong?"),
('n',"And look at what the writer does in verse 2. He says it out loud. I will say of the LORD. Your worry talks all morning long. Faith has to talk back."),
('s','trap'),
('n',"Verses 3 and 4."),
('v',"Psalm 91:3-4","Psalms 91:3-4",["fowler","pestilence","wings","shield"]),
('n',"A fowler is a trapper, and a snare is the trap you never saw coming. The bad deal. The wrong crowd. The text you should not have sent. God sees the trap before you ever step toward it."),
('n',"Then comes the picture I love. Under his wings. A mother bird covers her young with her own body when the weather turns, and whatever is coming has to get through her first."),
('s','hours'),
('n',"Verses 5 through 8."),
('v',"Psalm 91:5-8","Psalms 91:5-8",["not be afraid","night","noon","not come nigh"]),
('n',"Four hours are named in there, the night, the day, the darkness, and noon. There is no hour on the clock that was left uncovered. The fear that hits at three in the morning is on that list, and so is the trouble that shows up in broad daylight."),
('n',"So does that mean nothing bad ever comes near a believer? Read it again. It never says nothing will come at you. It says you do not have to be afraid of it. Jesus said the same thing plainly, in John chapter 16, verse 33."),
('v',"John 16:33","John 16:33",["peace","overcome"]),
('s','refuge'),
('n',"Back to the psalm. Verses 9 and 10."),
('v',"Psalm 91:9-10","Psalms 91:9-10",["habitation","no evil"]),
('n',"Thy habitation. It keeps coming back to where you live. Proverbs chapter 18, verse 10 puts it another way."),
('v',"Proverbs 18:10","Proverbs 18:10",["strong tower","runneth into it","safe"]),
('n',"Runneth into it. So when the fear comes, run. Say his name. You don't need fancy words. Jesus, help me, is a whole prayer."),
('s','angels'),
('n',"Verses 11 through 13."),
('v',"Psalm 91:11-13","Psalms 91:11-13",["angels","keep thee","lion"]),
('n',"You have help you can't see. God gives his angels orders about you. How many close calls have you already walked away from? You have probably been kept from things you will never hear about. The truck that did not cross the line. The night you made it home when you had no business making it."),
('n',"One careful note. The devil set Jesus on the top of the temple, quoted these very verses, and dared him to jump. Jesus said no. This psalm is a shelter for people who walk with God. It was never a permission slip to go looking for danger."),
('s','love'),
('n',"Now listen, because in verse 14 the voice changes. God himself starts to talk. Verses 14 through 16."),
('v',"Psalm 91:14-16","Psalms 91:14-16",["deliver him","with him in trouble","salvation"]),
('n',"Look at the middle of that. I will be with him in trouble. He never said you would not see trouble today. He said you would not be in it alone."),
('n',"And look at the reason. Because he hath set his love upon me. This whole psalm rests on a relationship, not a formula. If you have drifted, this morning is a good morning to walk back."),
('s','pray'),
('n',"So here is the prayer. Pray it out loud if you can."),
('n',"Father, I am stepping out the door, and I am putting this day under your wing. Cover my house while I am gone. Cover the ones I love, wherever they are right now. When a trap is set, show me before I step. When fear comes, remind me where I dwell. Send your angels ahead of me, and let me come home tonight with a thankful heart. I ask it in the name of Jesus Christ. Amen."),
('n',"Type amen, and send this to a friend who needs it. Have a blessed day, and remember the Word for today."),
]
paras=[]; sect={}; i=0; shown=[]
for it in S:
    if it[0]=='s': sect[str(i)]=it[1]; continue
    if it[0]=='n': paras.append({'i':i,'k':'n','t':it[1]})
    else:
        t=kjv(it[2]); paras.append({'i':i,'k':'v','ref':it[1],'t':t,'red':it[3]}); shown.append(t)
    i+=1
json.dump(paras,open('paras.json','w'),indent=1); json.dump(sect,open('sections.json','w'))
# script.txt for gate/proof: narration plain, scripture inside [[ ]]
open('script.txt','w').write('\n'.join(('[['+p['t']+']]') if p['k']=='v' else p['t'] for p in paras)+'\n')
open('kjv_source.txt','w').write('\n'.join(shown)+'\n')
nw=sum(len(p['t'].split()) for p in paras if p['k']=='n'); vw=sum(len(p['t'].split()) for p in paras if p['k']=='v')
print('paras',len(paras),'narration words',nw,'verse words',vw)
for p in paras:
    if p['k']=='v': print(p['ref'],'|',p['t'][:110])
