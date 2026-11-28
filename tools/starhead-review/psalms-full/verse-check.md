# Psalms 1-150: every KJV verse against the script (Nov 28 2026)

Method: kjv_source.txt / kjv_refs.txt hold the KJV Psalms, one verse per line, 2,461 verses (the book has 2,461). Each verse was lower-cased, punctuation removed, spaces collapsed, then searched for as an unbroken string inside its own psalm in script.txt, and checked to appear in verse order.

Result:
- 2,461 of 2,461 verses found word for word in their own psalm. 0 missing.
- 0 verses out of order.
- Each of the 150 psalms in the script has exactly 2 words more than its verses: the spoken lead-in "Psalm N." (the word "Psalm" and the number). Nothing else is added. Selah and the superscriptions are part of the KJV verses and are in the script where the KJV has them.
- Line 1 of the script is the spoken title, "The Book of Psalms, King James Version" (the narrator says it, the title card shows "The Book of Psalms").

So script = KJV + "Psalm N." + the title, and the speech-to-text on the finished audio matches the script (proof.md check 8, similarity 1.000 after the word-difference reconciliation in reconcile-dispositions.md).
