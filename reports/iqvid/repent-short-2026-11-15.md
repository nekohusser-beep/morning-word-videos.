# IQ Vid: REPENT rapture Short (Txu7G6DgpkM), Nov 15 2026 3:41 PM ET
Blessed Prayers Short, 1:27, public since 3:11 PM ET. Full IQ Vid run, free. vidIQ not used.

## Set in Studio (verified in Studio and on the public page)
- Title: Will You Be Left Behind in the Rapture? He Was Warned  (53 chars, IQ Vid title score 92)
- Was: 4 Minutes Before the Rapture, a Preacher Warned Him  (IQ Vid 85)
- Spare title: What If the Rapture Happened Today? He Was Warned First  (91)
- Description: search phrase in line 1, 1 Thessalonians 4:17 KJV (checked word for word against aruljohn/Bible-kjv), link to the long video, 5 hashtags (#rapture #leftbehind #repent #jesusiscoming #christianshortfilm). Humanize gate PASS.
- Tags: 20 (375/500).
- Related video: REPENT & BE SAVED | The 3 Steps to Eternal Life (UPAnmFk5aiE).
- Old title, description and tags: reports/yt-push/rollback/Txu7G6DgpkM-2026-11-15.json

## Keywords (runner kw runs 43757809964 + 43757817406, Google Trends YouTube search in the pane, merge.py)
```
score | keyword | est. searches/mo | volume | 30-day growth | demand | competition
   64 | rapture                            |   ~139840 |  77 |    -4% | very high | 55 medium
   62 | repent                             |    ~45590 |  70 |    -8% | high      | 49 medium
   61 | rapture 2026                       |    ~32570 |  67 |   -20% | high      | 48 medium
   60 | jesus is coming soon               |    ~32290 |  67 |   -46% | high      | 51 medium
   58 | rapture movie                      |    ~17640 |  63 |   +50% | medium    | 49 medium
   57 | christian short film               |    ~24330 |  65 |   +25% | medium    | 54 medium
   56 | rapture dream                      |     ~8400 |  58 |  +362% | low       | 46 medium
   55 | left behind rapture                |     ~3050 |  52 |    new | very low  | 41 medium
   52 | rapture short film                 |     ~1450 |  47 |    new | very low  | 40 medium
   29 | repent or perish                   |      ~500 |   0 |    new | very low  | 27 low
score = 60% volume + 40% low competition (vidIQ's own formula). est. searches are rough (about 3x either way).
```
Rising: sinners prayer +609%, rapture dream +362%, prayer of repentance +259%, rapture story +190%, how to repent +175%, rapture video +61%, rapture movie +50%, christian short film +25%, what is the rapture +50 to 70%.
Hot now: 'rapture 2026' has 106.5K views a day landing on its top 10 (not used: the video sets no date).
Open phrases: 'who will be left behind in the rapture' competition 35, 0% of top titles use it; 'how rapture will happen / look like' 720K-1M top-10 median, 0% of titles use the phrase.
Namesakes to ignore: Blondie, Anita Baker, IIO, Bioshock (rapture); Shaggy, Slayer, Binding of Isaac (repent). Country scores point at Angola/Malta/Liberia on tiny samples: not an audience call.

## Shorts outliers (Studio Research hub, Shorts filter, 175-189 rows per search)
- Chris and Jasmin (1.5M subs): 'THE RAPTURE WHEN MILLIONS VANISHED... AND THE WORLD WAS NEVER THE SAME' 6.7M in 7 days (62x); 'THE RAPTURE HAPPENED... AND THEY WERE LEFT BEHIND!' 708K in 11 days (13x); 'THEY DISAPPEARED AT 30,000 FEET... THE RAPTURE' 798K in 2 days. Same format as ours: acted rapture short film.
- Small-channel wins: 'Will You Be Left Behind In The Rapture' 75x (25.8K subs); 'Two deceptions that will cut you off from the Rapture' 100x (14.2K subs, 1 month); 'Is the Rapture Coming Soon?' 37x (20.7K); 'Is the Rapture Only for Christ's Spotless Bride? | Are You Ready?' 15x (27.3K, 1 month); 'How Will the Rapture Happen' 12x (38.5K).
- Tiny channels, last 2 weeks: 'What if Jesus Returned Today?' 1.2M (3.9K subs); 'Jesus is coming. Are you ready?' 1.5M (11.6K subs); 'Before The Rapture - Only 2 Final Warnings Remain!' 216K (1.4K subs); 'Rapture ready?' 133K (88 subs).
- Title patterns that win: (1) THE RAPTURE HAPPENED + who was left behind; (2) a question to the viewer (Will you be left behind? Are you ready?); (3) a place the vanishing happened; (4) a last warning.

## Not done / follow-up
- Pinned comment (the pane was hidden, the watch page comments would not load).
- 48-hour search rank: iqvid rank "Txu7G6DgpkM|left behind in the rapture|will you be left behind|rapture short film" on Nov 17.

## What IQ Vid learned this run (to write into kingdom-brain workflows/iq-vid.md and studio.js)
- Studio Research 'Search for topics' box is a TEXTAREA. Setting its value with the native setter + an input event + Enter runs the search; no real typing needed.
- When the pane is hidden the tab's viewport is 0x0: find/read_page return nothing and the topic box is not rendered. Fix: resize_window 1366x900 on the tab, reload, then find/form_input/click by ref all work.
- 'Analyze title patterns' (Ask Studio) answered "I can't help with that" for rapture Shorts. Read the patterns from the hub rows instead.
- popcheck --offline scores story Shorts SKIP (its bank is verses and prayers only). It needs a way to take IQ Vid's measured demand.
- Shorts outliers: the runner's 'out' mode is long-video only; the Studio hub with the Shorts filter covers Shorts.
