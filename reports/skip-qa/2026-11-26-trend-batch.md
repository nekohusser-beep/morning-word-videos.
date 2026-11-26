# Skip QA: Nov 26 trend batch (independent reviewer, frames every 0.25 s)

VERDICT: FAIL (all five). 64 defects. Most need new art, not a re-cut. Not posted.

Voice gate (voice_gate.py, bars skip 0.85 / dre 0.78 / nia 0.85): 10 of 29 lines FAIL.
- Black Friday: u005 Dre 0.750
- Leftovers: u002 Skip 0.630, u003 Nia 0.848, u004 Skip 0.771
- Two Weeks: u002 Skip 0.736
- One Thing: u002 Nia 0.763, u005 Skip 0.761
- Not Now: u001 Skip 0.764, u002 Skip 0.802, u003 Skip 0.800

## Black Friday (14)
- Punchline (16.8-18.4) spoken with Dre's mouth closed; mouth opens later in silence.
- Shot 2: Skip's mouth flaps on Dre's line. Shot 4: Skip cropped out while he speaks; Dre's mouth moves.
- Shot 3 spin: Dre and the box melt (blob on forehead, box turns into a flat screen, $299 smears, jeans + brown shoes).
- Different store, different Dre outfit, different beard in almost every shot; 3 AM snow jumps to sunset.
- The "TV" is a different box in every shot. Hook card sits on the in-picture BLACK FRIDAY sign.

## Leftovers (14)
- Skip's "You waited two hours?" plays over Nia's close-up: looks like she says it.
- Punchline "You just never read" with Nia's mouth closed.
- Nia is two different women (neither on-model); Skip is four different drawings; five different fridges.
- Plate changes shot to shot; clock numerals mirrored; "I SEE YOU SKIP" note not where the script puts it.
- Hook card 3 gives away the punchline. 1.3-1.8 s frozen frames in shots 3 and 5.

## Two Weeks (14)
- Shot 2: Dre has a full cap of black hair and a thick beard (he is bald with a fade + goatee). Red tie appears mid-shot.
- Shot 1: Dre has a handlebar moustache and no fade. Resignation letter floats with a loose hand.
- Final line with Dre's mouth closed. Lip-sync wrong through shot 1.
- Three different offices; captions cover the email that carries the joke.

## One Thing (11)
- "Where's the milk?" and "retention pond" look like Skip says them (Nia tiny in the background).
- Keys melt, blank eyes, three framings in 0.4 s, punchline line lands before he lifts the milk.
- Midday jumps to sunset; duck morphs; mouth flaps in silence under the end card.

## Not Now (11)
- Shot 2 is a different art style (flat, blank background).
- Lines spoken with a closed mouth; clocks contradict the time labels (hands read 4:00).
- Garbled signs ("TOOTIST"), real magazine title, two toothbrushes, shoes change, hoodie turns into a cape.

Also: all five run 14.8-21.7 s; the batch rule was 25-35 s.

Root causes: one voice take per line with no gate; a new still generated per shot from a text prompt (no locked
character sheet, no shared background), so every shot re-invented the people and the room; image-to-video asked to
"talk" with no control of whose mouth moves; no reviewer before Neko.
