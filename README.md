<!--
  The figure and every number between live markers are written by
  tools/build.py, which an Action runs each morning. Edit the prose freely;
  leave the markers where they are.
-->

# I build AI support for Discord.

I'm Dani, a solo developer in Romania. I write the bots, the AI platform under them, the dashboards, the billing and the ops, and I run all of it in production.

<a href="https://aiticketbot.com"><picture><source media="(max-width: 540px)" srcset="https://raw.githubusercontent.com/danYb16/danYb16/main/assets/figure-narrow.svg"><img alt="AI Ticket Bot, live: tickets handled, Discord servers, share of tickets resolved by AI and average first reply time." src="https://raw.githubusercontent.com/danYb16/danYb16/main/assets/figure-wide.svg" width="100%"></picture></a>

<sub>Read from <a href="https://aiticketbot.com">AI Ticket Bot</a>'s public stats and redrawn every morning by an <a href="https://github.com/danYb16/danYb16/blob/main/.github/workflows/live.yml">Action in this repo</a>.</sub>

## What I run

### <a href="https://aiticketbot.com"><img src="https://raw.githubusercontent.com/danYb16/danYb16/main/assets/dot-aitb.svg" width="12" height="12" alt=""> AI Ticket Bot</a>

AI support for Discord servers and their websites. Members get an answer in seconds, and staff only see the tickets that need a person. It runs in <!--live:servers-->4,895<!--/live--> servers and has handled <!--live:tickets-->204,639<!--/live--> tickets.

<sub>Python · Discord · web widget · runs on Nexus</sub>

### <a href="https://nexbrain.dev"><img src="https://raw.githubusercontent.com/danYb16/danYb16/main/assets/dot-nexus.svg" width="12" height="12" alt=""> Nexus</a>

The AI platform I built to power AI Ticket Bot. It gives every customer their own memory, training and usage metering.

<sub>Python · FastAPI · Postgres · Claude</sub>

### <a href="https://micoapp.io"><img src="https://raw.githubusercontent.com/danYb16/danYb16/main/assets/dot-mico.svg" width="12" height="12" alt=""> Mico</a>

AI screening for Discord applications. It scores every answer and flags the ones written by AI, so staff can accept or deny from one dashboard.

<sub>TypeScript · Next.js · OpenAI</sub>

### <a href="https://www.deboxperformance.ro"><img src="https://raw.githubusercontent.com/danYb16/danYb16/main/assets/dot-debox.svg" width="12" height="12" alt=""> Debox Performance</a>

Client work: the website for a car tuning workshop in Romania.

<sub>PHP · MariaDB</sub>

## How I work

<!--live:contributions-->3,241<!--/live--> contributions in the last year, on <!--live:active_days-->267<!--/live--> of its days. Nearly all of it is in private repositories, which is why this page links to products instead of code.

- Claude and OpenAI both run in production for paying users.
- Every user-facing surface is localized into 37 languages.
- I have used Claude Code daily on production code for over a year.

## Contact

**beeandaniel@gmail.com**

The products are live, so the fastest demo is opening one.
