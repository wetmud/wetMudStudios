# Whimsy Audit — wetMud Studios
*Conducted: 2026-03-26*

The site is tight and confident — right for SMB trust-building. These are targeted spots
where personality can breathe without breaking professionalism. None of these are required
for launch. Implement when the mood strikes.

---

## 1. The Dot — Nav Logo Hover
**Element:** `.nav-logo` — the `wetMud.` period
**Idea:** The period is already doing something. A subtle CSS animation on hover — a
tiny drip or wobble on the `<span>` dot only. One element, one moment.
**Effort:** Low (CSS only)
**Risk:** Zero — it's a single punctuation mark

---

## 2. ASCII Section Breaks — Animated Separators
**Element:** `.sep-line` — the `· · · ·` breaks between sections
**Idea:** On hover or on scroll-into-view, animate the dots: cycle through terracotta,
or shift them like `· · · → · · ·`. They're already whimsical — give them a pulse.
**Effort:** Low (CSS animation or brief JS)
**Risk:** Low — decorative only, `aria-hidden` already set

---

## 3. Screenshot Placeholders — Less Sterile
**Element:** `.work-img-placeholder` — "SCREENSHOT COMING" on GrantMatch + Ontario Markets
**Idea:** Replace the flat grey with a terracotta-tinted box and CSS diagonal hatching
pattern, or a dashed border treatment. Something that looks intentional, not forgotten.
**Effort:** Low (CSS only)
**Risk:** Zero

---

## 4. 404 Page — Full Whimsy Budget
**Element:** `404.html` — doesn't exist yet
**Idea:** "You dug too deep. Nothing here but mud." — full wetMud aesthetic, big type,
terracotta, a link back home. This is the one page where personality has no constraint.
**Effort:** Medium (new file, same design system)
**Risk:** Zero — nobody lands here on purpose

---

## 5. Blog Modal Close — Warmer Exit
**Element:** `.modal-close` button — currently "Close ✕"
**Idea:** Change to "← Back" or style the hover so it slides left slightly — feels
more like returning somewhere than dismissing something.
**Effort:** Trivial (copy + CSS tweak)
**Risk:** Zero

---

## 6. Footer Easter Egg — Hidden Personality
**Element:** `.footer-logo` — the `wetMud.` in the footer
**Idea:** Triple-click triggers a one-liner in the console or a subtle page reaction.
Something honest and specific — a real line, not a generic "you found me."
Example console message: `// hi. yeah this is all one file. ~1200 lines. no frameworks. i'm fine.`
**Effort:** Low (5 lines of JS)
**Risk:** Zero — invisible unless discovered

---

## Priority Order for Implementation

| # | Item | Effort | Vibe payoff |
|---|------|--------|-------------|
| 1 | 404 page | Medium | Highest |
| 2 | Footer Easter egg | Low | High |
| 3 | The Dot hover | Low | Medium |
| 4 | Screenshot placeholders | Low | Medium |
| 5 | Modal close copy | Trivial | Low |
| 6 | ASCII separator animation | Low | Medium |

---

*Whimsy principle: one unexpected thing per page. Don't decorate — punctuate.*
