# 2026-05-20 — Where we're at

Short session, two things shipped and one big plan written.

## What got done

**1. Work section refresh — live now.**

The Work grid on the site was running outdated copy and a broken EventLineup deploy link. Pulled the current project lineup from personalsite/ and rebuilt the section around it:

- **Sourcepull** is the new lead — wide hero card. AEO platform, sourcepull.ca, Innovation Factory acceptance. This is the strongest single signal we've got that wetMud does real AI work, not "I use ChatGPT to write copy." Putting it first.
- **CivicConnect → Civic Engagement.** Renamed to match the production URL (civicengagement.ca), updated the blurb to mention the 9-municipality AI chatbot. The old wetmud.github.io/CivicConnect link wasn't wrong, but civicengagement.ca is the real brand now.
- **EventLineup dropped, OnTonight in.** eventpulse is Phase 2-stalled per the root CLAUDE.md, and the link on the site was dead. OnTonight is the live successor — React + Supabase + Railway, ontonight-three.vercel.app. Broken sales links are worse than fewer projects.
- **GrantMatch + Ontario Markets** now have real images instead of "SCREENSHOT COMING" placeholders.

Six cards total, same wide/narrow/half grid system. Two commits, pushed to main. GH Pages should be live by now.

**2. CLAUDE.md synced.**

The project's CLAUDE.md still listed the old 5-project lineup. Updated to match what's actually on the site, with notes on the rename + replacement so future-me (or future-Claude) knows why things changed instead of just what they are.

**3. Admin dashboard plan written.**

Saved to `docs/admin-dashboard-plan.md`. The short version:

- Don't add FastAPI. Don't add Supabase yet. The `leadgen-crm/` Express server already has 80% of what an admin backend needs — Express, better-sqlite3, bearer auth, Anthropic SDK, static UI scaffolding. Extend that.
- New `content.db` (separate from `leads.db`) holds editable content: services, projects, posts, site settings, media.
- Admin UI is a new `admin.html` in `leadgen-crm/public/` with tabs for Site / Services / Projects / Blog / Media.
- The killer move: a "Publish" button writes `data/site.json` and git-pushes it. GH Pages serves the static snapshot, so the live site doesn't depend on the admin server being up. Best of both worlds.
- Phase 4 is the client portal — port the SteltmanDesign architecture (token-gated pages, magic-link auth) when we have a real client to need it. Heavyweight, but the patterns are proven.

Recommended kickoff is a 30-min spike: prove the static-publish JSON flow on the Projects section alone before committing to the full build.

## What we didn't do

- Didn't touch the actual admin build yet — just the plan.
- Didn't update the legacy images (Civicconnect3.png, EventSC1.png are still in the repo but unreferenced; flagged as safe to remove).
- Didn't refresh blog content (those posts are still adapted from personalsite — fine for launch, rewrite later).

## Where the project is overall

The brochure site is in good shape. Six current projects, real images on all of them, no dead links, copy that leads with capability rather than aesthetics. The Phase 0 market positioning research is still solid — niche order is local service businesses → non-profits → real estate → markets → events.

What's missing before this is a real sales tool:

1. **Real contact wiring.** mailto: works, but the Formspree form is unwired. Email address on the site is still TBD per the SEO meta.
2. **First case study.** Five projects shown is good. Zero "here's what I built for a client" is the gap. Until that exists, the site is a portfolio of personal projects with a business name on top.
3. **Admin dashboard.** Plan is written, build is not started. Once it ships, blog cadence goes from "edit HTML by hand" to "draft + publish in 5 minutes" — which is the unlock for the SEO/content strategy in the positioning doc.

## What I'd do next session

In order of leverage:

1. Wire the real email + Formspree endpoint (15 min, removes the biggest "this isn't real yet" signal)
2. Spike Phase 1 of the admin dashboard — Projects-only, prove the publish flow (~1 session)
3. Then full Phase 1 build — Site + Services + Projects + Blog (~1–2 sessions)
4. First blog post: "What AI actually does for a small business." Front-loads the SEO play.

That's the state of things. Site looks better than it did this morning. Plan exists for the next real build. Onwards.
