source: internal + stakeholder-request
date: 2026-09-26

Related: `research/2026-09-26-data-story-chart-variety.md` and `changes/2026-09-26-data-story-chart-variety.md`
(open decision 5, where this was found and deliberately not fixed in place).

--- Internal observation (measured, not user-reported) ---

While applying the `dataviz` skill's palette validator to the Data Story chart work (dark mode, surfaces
`gray-800` and `gray-900`), the product's three role-category accents failed:

  Designer        indigo-500  #6366f1
  Product Manager purple-500  #a855f7
  Engineer        emerald-500 #10b981

  indigo-500 <-> purple-500   CVD separation  ΔE 0.9 under protanopia  (FAIL — effectively the same colour)
                              normal vision   ΔE 11.3                  (FAIL — hard floor is 15)
  emerald-500                 OKLCH lightness 0.696 vs the dark band 0.48–0.67 (FAIL, minor)

These colours are used across the trend chart lines, the Category Share Bar, the year-on-year role-mix
charts, and the admin dashboard's role bars.

--- Stakeholder direction (verbatim, in reply to the options I set out) ---

fix the role pallete with your fix; story 2 camption text, ok for me; other low contrast can be fixed later

--- Notes added when captured (not part of the raw input) ---

- "your fix" referred to the replacement I had recommended (indigo-500 / pink-500 / emerald-600), which had
  been validated against the other two roles only.
- Validating it against the semantic colours as well (a Product Manager line can share a view with a
  "declining" arrow) found pink-500 vs red-600 at ΔE 14.5 normal-vision (floor 15). That would have traded one
  failure for another, so the replacement was re-searched (pink-500, pink-600, fuchsia-500/600, cyan-600,
  sky-600, orange-600, yellow-600, violet-500 tested pairwise against indigo-500, emerald-600, red-600,
  amber-600). Fuchsia-600 #c026d3 is the only candidate with no hard failure against any of them.
- "story 2 caption text, ok" and "other low contrast can be fixed later" answer open decisions 6 and 7 of
  `changes/2026-09-26-data-story-chart-variety.md` — accepted, and deferred, respectively.
