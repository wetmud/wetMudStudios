# wetMud Studios — Creative Agency Site

New site for Jason Steltman's freelance web design + AI tools business.
Separate from jasonsteltman.com (which stays personal/portfolio).

**Brand:** wetMud Studios
**Owner:** Jason Steltman (GitHub: wetmud)
**Target:** Small and medium businesses — Burlington first, Canada-wide
**Stack:** Vanilla HTML/CSS/JS — single `index.html`, zero build tools, zero dependencies
**Deploy:** GitHub Pages via Cloudflare (same as personal site)

---

## The Brief

jasonsteltman.com reads as a creative portfolio. SMB clients need something different: services-forward, outcome-focused, locally anchored. This site is that thing.

**Core value prop:** Real, capable projects that add value and efficiency.
Not "elevate your brand." More: "I built a tool that does X — here's what it did."

**Tone:** Direct, warm, specific. Like the French Press blog post on the personal site — that personal specificity is the brand voice, just pointed at client problems.

**Tagline options (pick one or riff):**
- `Web Design & AI Tools for Small Business`
- `We build websites and tools that make your business work smarter`
- `Design + technology for businesses that want to move faster`

---

## Site Structure (single-page)

```
1. Hero          — Name, tagline, value prop, CTA ("Email Us" + "See Our Work")
2. Services      — 3 cards: Web Design / AI Integration / Data Tools
3. Work          — 4–5 featured projects with rewritten stories (see below)
4. Process       — How we work (3–4 steps, simple)
5. About         — Brief personal credibility (human behind the studio)
6. Contact       — Single email CTA + optional short form
```

---

## Design DNA (from jasonsteltman.com — take these)

**Palette:**
- Background: `#f5f0e8` (warm beige)
- Text: `#111111` (near-black)
- Muted: `#666666`
- NEW Accent: `#C84B1A` (terracotta — for CTAs and active states)

**Typography:**
- Display/Logo: Cabinet Grotesk (fontshare)
- Section heads: Zodiak (fontshare)
- UI/Body: Outfit (Google Fonts)

**Signatures to carry over:**
- Directional card shadow: `box-shadow: 10px 14px 0px rgba(0,0,0,0.18)`
- Card hover: `transform: translateY(-4px) translateX(-4px)` — shadow stays fixed
- Vertical grid line overlay (CSS repeating-linear-gradient, subtle)
- Scroll reveal: `opacity:0 → 1` + `translateY(32px → 0)` on `.reveal` class
- ASCII dot breaks: `· · · ·` between sections
- Fixed top marquee bar (30px black, white text, scrolling)
- Bebas Neue for marquee/nav labels

**Do NOT carry over:**
- Custom cursor (too personal/quirky for a business site)
- Photo roll (personal site only)
- Letter spin animation on name
- Cursor picker widget

---

## Services (3 offerings)

```
[ Web Design ]
  Clean, fast websites built from scratch.
  No templates. No page builders. Just code that works.
  From concept to live in weeks, not months.

[ AI Integration ]
  Add AI to what you already have.
  Chatbots, email drafting, content tools, automation.
  Built to your workflow, not a generic plugin.

[ Data Tools & Dashboards ]
  Turn messy data into something you can act on.
  Scrapers, live dashboards, internal tools.
  Built for people who need answers, not spreadsheets.
```

---

## Work / Projects (rewritten for SMB audience)

Pull screenshots/thumbs from jasonsteltman.com `images/` folder. Current live lineup (refreshed 2026-05-20):

**01 — Sourcepull** (wide hero card)
- Card: "Find out what ChatGPT, Perplexity, Gemini, and Claude say about your business. AI Engine Optimization audits with scored visibility and a prioritized fix plan. Built alongside an AI CEO agent over 90+ working sessions. Accepted into Innovation Factory."
- Tags: AEO · Agentic · Next.js
- Link: https://sourcepull.ca
- Image: sourcepull1.png

**02 — Civic Engagement** (narrow)
- Card: "Every elected representative from city councillor to Prime Minister, from a single address. No cookies, no tracking. AI chatbot routes residents to the right city department across 9 Ontario municipalities."
- Tags: Civic Tech · AI · Vanilla JS
- Link: https://civicengagement.ca
- Image: civicengagement1.png
- Note: renamed from CivicConnect; production URL is now civicengagement.ca, not wetmud.github.io/CivicConnect

**03 — OnTonight** (half)
- Card: "One calendar for every event in the GTA — concerts, theatre, comedy, festivals, sports. Density-gradient calendar view, 12-area filtering, save and remind. The most technically complex thing in the studio."
- Tags: React · Supabase · Railway
- Link: https://ontonight-three.vercel.app/
- Image: OnTonight1.png
- Note: replaces EventLineup/eventpulse, which had a dead deploy link

**04 — GrantMatch** (half)
- Card: "Drop in a project description — text, PDF, or screenshot — and get matched to grants you actually qualify for. Companion tracker manages your pipeline with status, deadlines, and next steps."
- Tags: AI · Grants · BYOK
- Link: (none — add when available)
- Image: GrantMatch1.png

**05 — RE:PULSE** (half)
- Card: "GTA real estate intelligence without the Bloomberg terminal price tag. Live scraped data, scatter plots, full sortable listings."
- Tags: Data · Scraper · Dashboard
- Link: https://wetmud.github.io/realestate-scraper-1-/
- Image: RealEstateScraper.png

**06 — Ontario Markets** (half)
- Card: "35 farmers' markets, 6 regions, one calendar. Built because I kept missing market day in my own neighbourhood."
- Tags: Local · Calendar · Ontario
- Link: https://ontario-fresh-finds.lovable.app/
- Image: OFF1.png

---

## Process (4 steps)

```
01 — Discovery
    One conversation. What do you need, who uses it, what does success look like.

02 — Build
    Fast and iterative. You see real progress weekly, not a big reveal at the end.

03 — Ship
    Live on your domain. Tested. Fast. Yours.

04 — Support
    Not abandoned at launch. I stay available for fixes, updates, and next steps.
```

---

## About Section

Jason Steltman is a designer and developer based in Burlington, Ontario.
Art and design graduate. Publishing background. Three years building
web tools and AI integrations — civic tech, event platforms, data dashboards.

wetMud Studios is the working name for client projects.
Personal work lives at jasonsteltman.com.

---

## Contact

- Primary CTA: `mailto:` link (email TBD — add real address before launch)
- Anchor text: "Email us" or "Start a conversation"
- Secondary: Short 3-field form (Name / Email / What do you need?) — wire to Formspree
- Formspree endpoint: (add before launch)

---

## SEO / Meta

```html
<title>wetMud Studios — Web Design & AI Tools | Burlington, ON</title>
<meta name="description" content="Freelance web design and AI tool development
for small businesses. Based in Burlington, Ontario — working Canada-wide.
Clean websites, AI integrations, and data tools that actually work.">
```

LocalBusiness JSON-LD schema:
```json
{
  "@context": "https://schema.org",
  "@type": "LocalBusiness",
  "name": "wetMud Studios",
  "description": "Web design and AI tool development for small businesses",
  "url": "https://wetmudstudios.com",
  "address": {
    "@type": "PostalAddress",
    "addressLocality": "Burlington",
    "addressRegion": "ON",
    "addressCountry": "CA"
  },
  "areaServed": ["Burlington", "Hamilton", "Toronto", "Ontario", "Canada"],
  "priceRange": "$$"
}
```

---

## File Structure

```
index.html        — entire site (single file)
images/           — copy needed images from ../personalsite/images/
```

Images currently in use (copied from `../personalsite/`):
- sourcepull1.png
- civicengagement1.png
- OnTonight1.png
- GrantMatch1.png
- RealEstateScraper.png
- OFF1.png
- Civicconnect3.png, EventSC1.png — legacy, no longer referenced (safe to remove)

---

## Blog

Add a blog section to the site. Lift the blog implementation directly from `../personalsite/index.html` — the POSTS array, card renderer, modal system, and tag filter all carry over. Rewrite the posts for an SMB/studio audience over time, but launch with adapted versions of the personal site posts where relevant.

**Blog section placement:** after Work, before Process — it's social proof + thought leadership.

**Initial post topics to write (after launch):**
- "What AI actually does for a small business" — targets consulting angle + SEO
- "I built a grant-matching tool. Here's what it taught me about what SMBs need."
- "How I find clients who need a new website" — honest, process-forward

---

## Market Positioning (Phase 0 Research — 2026-03-26)

### The Gap

Local Burlington/GTA web design market is dominated by:
- **Template-pushers** (Squarespace freelancers, $500–2K, no differentiation)
- **Small agencies** (Hamilton/Oakville, $5K–15K+, slow, too expensive for sole proprietors)
- **National platforms** (impersonal, offshore competition)

**What no one in this market is doing:**
- Shipping their own tools (wetMud has 3 live apps — huge credibility signal)
- Offering AI integration as a real deliverable (not just "I use AI to write copy")
- Building in public / showing process
- Demonstrating civic/public-good work

### Niche Targeting (Priority Order)

| Niche | Fit | Proof |
|-------|-----|-------|
| Local service businesses (trades, restaurants, salons) | High — low bar to impress, recurring update work | Burlington context |
| Non-profits + civic orgs | High — underfunded, underserved, need grant help | CivicConnect + GrantMatch |
| Real estate agents / small brokerages | Medium — high motivation to look legit | RE:PULSE |
| Farmers markets / artisan producers | Medium — Ontario Markets shows domain knowledge | Ontario Markets app |
| Event organizers | Medium — EventLineup shows problem understanding | EventLineup |

### Pricing Signals

| Offer | Price |
|-------|-------|
| Starter site (5 pages, fast) | $1,500–2,500 |
| AI consultation (1 hour, recorded) | $150–250 |
| Site + AI tool bundle | $3,500–6,000 |
| Monthly retainer (updates + support) | $200–400/mo |
| GrantMatch white-label setup for non-profits | $500 + setup |

### Acquisition Channels (in order)

1. Warm network first — Burlington/Hamilton business community, referrals
2. Local business Facebook groups / BNI chapters
3. Blog → SEO → inbound (slow burn, compounding — start writing now)
4. Scrape + outreach pipeline (build after 2 case studies exist)
5. Google My Business listing for wetMud Studios (free, immediate win)

### The Scraping/Outreach Pipeline (build later)

Scrape Google Maps / local business directories for Burlington + GTA. Filter for: no website, or sites with obvious issues (mobile fail, no SSL, Wix template with stock photos). Send personalized outreach: "I looked at your site and noticed X — I fixed that exact problem for [similar business]." This is the AI tools edge applied to our own biz dev — dogfooding.

### Brand Positioning Notes

- Lead with tools, not design: "I built a tool that saved a non-profit 40 hours of grant research" beats any portfolio grid.
- Don't hide the personal brand. "wetMud Studios is Jason Steltman" — founder-led trust beats faceless agencies.
- Don't compete on price. The tools angle justifies a premium. Hold it.
- Don't over-promise AI. Show the tool, explain the outcome, skip the buzzwords.

**Hero sub-copy recommendation:**
> "I build websites and tools that actually work for your business — not templates, not jargon. Burlington-based, Canada-wide."

---

## Notes

- No build steps. No npm. No frameworks.
- Keep it under 1200 lines of HTML if possible (blog adds some length) — single file is the goal.
- The personal site's CLAUDE.md has font loading patterns, scroll reveal JS, and
  the marquee implementation — reference it for copy-paste foundations.
- Lift blog JS/CSS wholesale from `../personalsite/index.html`.
- Don't add the custom cursor. Don't add the cursor picker. Don't add the photo roll.
- DO add the grid line overlay, directional shadows, and reveal animations.
- Wire Formspree before going live. CSP header will need `formspree.io` in connect-src.
