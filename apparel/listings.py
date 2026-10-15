import json
# id: (product, title, verse_text, ref, extra_tags)
P = {'tee_m': ('Bella+Canvas 3001 Unisex Jersey Tee', 'T-Shirt', 27.99),
     'tee_w': ('Comfort Colors 1717 Garment-Dyed Tee', 'Comfort Colors Tee', 31.99),
     'sw': ('Gildan 18000 Crewneck Sweatshirt', 'Sweatshirt', 39.99),
     'hd': ('Gildan 18500 Hooded Sweatshirt', 'Hoodie', 46.99)}
L = [
 ('M1','tee_m','I Am The Way The Truth And The Life Shirt, John 14:6 KJV Christian Tee for Men, Bold Bible Verse Shirt, Jesus Shirt','I am the way, the truth, and the life','John 14:6',['john 14 6 shirt','way truth life','jesus shirt men','christian man gift']),
 ('M2','tee_m','Be Strong And Of A Good Courage Shirt, Joshua 1:9 KJV Christian Shirt for Men, Bible Verse Tee, Gift for Him','Be strong and of a good courage... for the LORD thy God is with thee whithersoever thou goest','Joshua 1:9',['joshua 1 9 shirt','be strong courage','christian dad gift','men faith tee']),
 ('M3','tee_m','Iron Sharpeneth Iron Shirt, Proverbs 27:17 KJV Christian Shirt for Men, Mens Bible Study Gift, Brotherhood Faith Tee','Iron sharpeneth iron; so a man sharpeneth the countenance of his friend','Proverbs 27:17',['iron sharpens iron','proverbs 27 17','mens ministry gift','christian brother']),
 ('M4','tee_m','No Weapon Formed Against Thee Shall Prosper Shirt, Isaiah 54:17 KJV Christian Tee for Men, Spiritual Warfare Shirt','No weapon that is formed against thee shall prosper','Isaiah 54:17',['no weapon formed','isaiah 54 17','spiritual warfare','christian man gift']),
 ('M5','tee_m','Not Ashamed Of The Gospel Shirt, Romans 1:16 KJV Christian Shirt for Men, Bold Faith Tee, Evangelism Shirt','For I am not ashamed of the gospel of Christ','Romans 1:16',['not ashamed shirt','romans 1 16','gospel shirt','evangelism gift']),
 ('W1','tee_w','It Is Well With My Soul Shirt, Comfort Colors Christian Tee for Women, Hymn Shirt, Faith Gift for Her','It is well with my soul (from the 1873 hymn)','Hymn',['it is well shirt','hymn shirt','comfort colors tee','christian women tee']),
 ('W2','tee_w','Jeremiah 29:11 KJV Shirt, For I Know The Thoughts That I Think Toward You, Comfort Colors Christian Tee for Women','For I know the thoughts that I think toward you, saith the LORD, thoughts of peace, and not of evil, to give you an expected end','Jeremiah 29:11',['jeremiah 29 11','bible verse tee','comfort colors tee','christian women tee']),
 ('W3','tee_w','Pray Without Ceasing Shirt, 1 Thessalonians 5:17 KJV, Comfort Colors Christian Tee for Women, Prayer Warrior Shirt','Pray without ceasing','1 Thessalonians 5:17',['pray without ceasing','prayer warrior','comfort colors tee','christian women tee']),
 ('W4','tee_w','Strength And Honour Are Her Clothing Shirt, Proverbs 31:25 KJV, Proverbs 31 Woman Comfort Colors Christian Tee','Strength and honour are her clothing; and she shall rejoice in time to come','Proverbs 31:25',['proverbs 31 woman','proverbs 31 25','comfort colors tee','gift for wife']),
 ('W5','tee_w','The Lord Is My Shepherd Shirt, Psalm 23 KJV Comfort Colors Christian Tee for Women, Bible Verse Shirt, Faith Gift','The LORD is my shepherd; I shall not want','Psalm 23:1',['psalm 23 shirt','lord is my shepherd','comfort colors tee','christian women tee']),
 ('MS1','sw','King Of Kings Lord Of Lords Sweatshirt, Revelation 19:16 KJV Christian Sweatshirt for Men, Jesus Is King Crewneck','KING OF KINGS, AND LORD OF LORDS','Revelation 19:16',['king of kings','jesus is king','christian sweatshirt','mens crewneck']),
 ('MS2','sw','O Man Of God Sweatshirt, 1 Timothy 6:11 KJV Christian Sweatshirt for Men, Godly Man Crewneck, Gift for Husband','But thou, O man of God, flee these things; and follow after righteousness, godliness, faith, love, patience, meekness','1 Timothy 6:11',['man of god','godly man gift','christian sweatshirt','gift for husband']),
 ('MS3','sw','Put On The Whole Armour Of God Sweatshirt, Ephesians 6:11 KJV Christian Sweatshirt for Men, Armor Of God Crewneck','Put on the whole armour of God','Ephesians 6:11',['armor of god','ephesians 6 11','christian sweatshirt','mens crewneck']),
 ('MS4','sw','Stand Fast In The Faith Sweatshirt, 1 Corinthians 16:13 KJV Quit You Like Men, Christian Sweatshirt for Men','Watch ye, stand fast in the faith, quit you like men, be strong','1 Corinthians 16:13',['stand fast faith','1 corinthians 16 13','christian sweatshirt','mens ministry']),
 ('MS5','sw','For Unto You Is Born A Saviour Christmas Sweatshirt, Luke 2:11 KJV Christian Christmas Crewneck, Nativity Star Sweatshirt','For unto you is born this day in the city of David a Saviour, which is Christ the Lord','Luke 2:11',['christian christmas','luke 2 11','jesus christmas','nativity sweatshirt']),
 ('WS1','sw','O Give Thanks Unto The Lord Sweatshirt, Psalm 107:1 KJV Fall Christian Sweatshirt for Women, Thanksgiving Wheat Crewneck','O give thanks unto the LORD, for he is good','Psalm 107:1',['thanksgiving shirt','fall christian','give thanks','fall sweatshirt']),
 ('WS2','sw','Seedtime And Harvest Sweatshirt, Genesis 8:22 KJV Fall Christian Sweatshirt for Women, Autumn Harvest Crewneck','While the earth remaineth, seedtime and harvest... shall not cease','Genesis 8:22',['harvest sweatshirt','fall christian','autumn crewneck','genesis 8 22']),
 ('WS3','sw','In Every Thing Give Thanks Sweatshirt, 1 Thessalonians 5:18 KJV, Thanksgiving Christian Sweatshirt for Women, Fall Crewneck','In every thing give thanks','1 Thessalonians 5:18',['give thanks shirt','thanksgiving shirt','fall christian','grateful sweatshirt']),
 ('WS4','sw','O Come Let Us Adore Him Sweatshirt, Christian Christmas Sweatshirt for Women, Christ The Lord Nativity Crewneck','O come, let us adore Him, Christ the Lord (classic Christmas hymn)','Hymn',['o come let us adore','christian christmas','jesus christmas','nativity sweatshirt']),
 ('WS5','sw','Behold I Make All Things New Sweatshirt, Revelation 21:5 KJV, New Year Christian Sweatshirt for Women, Fresh Start Crewneck','Behold, I make all things new','Revelation 21:5',['all things new','new year christian','fresh start shirt','revelation 21 5']),
 ('MH1','hd',"The Battle Is The Lord's Hoodie, 1 Samuel 17:47 KJV Christian Hoodie for Men, David and Goliath Faith Hoodie",'for the battle is the LORD\'s','1 Samuel 17:47',['battle is the lords','christian hoodie','mens faith hoodie','spiritual warfare']),
 ('MH2','hd','I Am That I Am Hoodie, Exodus 3:14 KJV Christian Hoodie for Men, Name Of God Hoodie, Minimal Faith Sweatshirt','I AM THAT I AM','Exodus 3:14',['i am that i am','exodus 3 14','christian hoodie','name of god']),
 ('MH3','hd','More Than Conquerors Hoodie, Romans 8:37 KJV Christian Hoodie for Men, Bold Bible Verse Hoodie, Gym Faith Hoodie','we are more than conquerors through him that loved us','Romans 8:37',['more than conquerors','romans 8 37','christian hoodie','christian gym']),
 ('MH4','hd','The Lion Of The Tribe Of Juda Hoodie, Revelation 5:5 KJV Christian Hoodie for Men, Lion Of Judah Faith Hoodie','the Lion of the tribe of Juda... hath prevailed','Revelation 5:5',['lion of judah','revelation 5 5','christian hoodie','mens faith hoodie']),
 ('MH5','hd','Wonderful Counsellor Prince Of Peace Hoodie, Isaiah 9:6 KJV Christmas Christian Hoodie for Men, Names Of Jesus','Wonderful, Counsellor, The mighty God, The everlasting Father, The Prince of Peace','Isaiah 9:6',['prince of peace','isaiah 9 6','christian christmas','names of jesus']),
 ('WH1','hd','Let Your Light So Shine Hoodie, Matthew 5:16 KJV Christian Hoodie for Women, Be The Light Faith Hoodie','Let your light so shine before men','Matthew 5:16',['let your light shine','matthew 5 16','christian hoodie','womens faith hoodie']),
 ('WH2','hd','Be Still And Know That I Am God Hoodie, Psalm 46:10 KJV Christian Hoodie for Women, Cozy Bible Verse Hoodie','Be still, and know that I am God','Psalm 46:10',['be still and know','psalm 46 10','christian hoodie','womens faith hoodie']),
 ('WH3','hd','We Love Him Because He First Loved Us Hoodie, 1 John 4:19 KJV Christian Hoodie for Women, Valentine Faith Hoodie','We love him, because he first loved us','1 John 4:19',['he first loved us','1 john 4 19','christian hoodie','womens faith hoodie']),
 ('WH4','hd','The Joy Of The Lord Is Your Strength Hoodie, Nehemiah 8:10 KJV Christian Hoodie for Women, Joyful Faith Hoodie','for the joy of the LORD is your strength','Nehemiah 8:10',['joy of the lord','nehemiah 8 10','christian hoodie','womens faith hoodie']),
 ('WH5','hd','Joy To The World The Lord Is Come Hoodie, Christian Christmas Hoodie for Women, Snowflake Hymn Hoodie, Holiday Gift','Joy to the world, the Lord is come (classic Christmas hymn)','Hymn',['joy to the world','christian christmas','christmas hoodie','womens faith hoodie']),
]
COMMON = ['kjv bible verse', 'christian apparel', 'faith gift', 'church outfit', 'scripture clothing', 'religious gift', 'jesus lover gift', 'bible study gift', 'christian gift']

def desc(i, prod, verse, ref):
    blank, kind, price = P[prod]
    vline = f'"{verse}" ({ref}, KJV)' if ref != 'Hymn' else f'"{verse}"'
    return f"""{vline}

Wear the Word. This {kind.lower()} carries scripture straight from the King James Version, word for word, with the reference printed right on it so people can look it up. Designed by Kingdom Impact Shop and printed when you order.

WHY PEOPLE PICK THIS ONE
- Exact KJV wording. We don't paraphrase scripture.
- Clean, readable lettering that holds up from across the room
- Printed on a {blank}, soft and made to be worn often
- A gift that points people back to Christ

SIZING
Unisex fit. Women who like a relaxed fit usually take their normal size; for a fitted look, size down one. Check the size chart photo before ordering.

CARE
Wash inside out in cold water, tumble dry low or hang dry. Do not iron directly on the print.

SHIPPING
Made to order by our print partner and shipped within a few business days. Need it by a date? Message us before you order.

Kingdom Impact Shop: faith books, audiobooks and apparel that plant a seed.
"""

out = []
for i, prod, title, verse, ref, tags in L:
    t = (tags + [x for x in COMMON if x not in tags])[:13]
    assert all(len(x) <= 20 for x in t), (i, [x for x in t if len(x) > 20])
    assert len(title) <= 140, (i, len(title))
    out.append(dict(id=i, product=prod, blank=P[prod][0], price=P[prod][2], title=title, tags=t, description=desc(i, prod, verse, ref)))
json.dump(out, open('listings.json', 'w'), indent=1)
print(len(out), 'ok')
