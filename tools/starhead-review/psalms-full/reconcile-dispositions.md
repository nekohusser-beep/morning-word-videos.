# Psalms 1-150: how every machine word difference was settled (Nov 28 2026)

Audio checked: the finished 8:48:36 master, cut at chapter pauses into 18 pieces, each transcribed twice (Whisper medium.en and large-v3, 36 runs, all finished), word times offset back to the full video. Third opinion on the leftovers: Whisper small, run locally on a window around each spot. About 42,900 spoken words. Raw differences between a machine and the script: 608. Every one is a row in dispositions.csv (time in video, script word, what each machine wrote, 12-word context); 607 rows there plus the 1 script gap below that was fixed in the script.

| Class | Count | What it is | Action |
|---|---|---|---|
| 1 | 172 | spacing only (for ever / forever, loving kindness / lovingkindness) | none |
| 2 | 140 | the second machine (large-v3) heard it exactly as written | none |
| 3 | 166 | spelling variant: the machine writes the modern spelling of the same spoken word (shew/show, honour/honor, favour/favor, brake/break, reins/reigns, stedfast/steadfast) | none, a spelling is not a pronunciation |
| 4 | 67 | machine noise: the same word is heard correctly almost everywhere else. Biggest group: "hast" (written "haste" at 24 of 189 places, "hast" at 165), "ye" written "he" (10 of 123), "Selah" written "salah" | none; two of each are in the spot-listen file so you can confirm by ear |
| 5 | 61 (44 distinct words) | rare words, old verb endings and names where all three machines write a modern or near spelling; software cannot judge pronunciation | in psalms-spot-listen.mp4 (65 clips = these 61 + 2 hast + 2 ye) for a human ear |
| 6 | 1 | Whisper invents "Praise the LORD." every 30.0 s over the ambience-only tail (30846 s onward), where there is no voice (bed only) | confirm by ear on the end clip |
| 0 | 1 | script gap: the narrator says "The Book of Psalms, King James Version" at the start and the script line had left out "The Book of" | fixed in script.txt |

The 44 distinct class-5 words: a bound, abiram, adders, answeredst, baalpeor, calledst, cassia, castedst, caterpillers, conies, contemned, coveredst, deviseth, doest, doeth, driedst, dross, forgat, hagarenes gebal, hateth, higgaion selah, holpen, inditing, kison, lawgiver, leddest, loins, lord's, lovingkindness, mesech, phinehas, plantedst, presents, satest, sirion, spoiling, strengthenedst, trieth, whet, wrest, zalmunna, zebah, zeeb (plus "doest/doeth" families). Spot-index.md gives each clip's time and the two lines of context.

All Whisper models share a modern-spelling bias, so "agreement" among them on these words proves nothing either way. That is why a person listens.
