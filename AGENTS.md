# Bettor Index Trends Worker

## Role

This service powers the **Trends** tab on the BettorIndex frontend: a curated feed of **one-liner insights** tied to real player prop bets (line, side, odds, hit streak).

Each card answers: *“What’s notable about this bet on today’s slate?”*

This is **not** the Prop Markets research catalog and **not** a duplicate of `bettorindexpropsignals`. Prop cards answer *“should I bet this?”* Trends answer *“here’s an interesting stat story about this bet.”*

## Pipeline Position

```text
revised_engine/
  → odds_api_props, hit_rate_event_queue

hit_rate_worker/
  → {sport}_hit_rates

bettor_index_prop_summarizer_worker/
  → {sport}_summaries (summary_data JSON)

bettor_index_trends/  (this repo)
  → read upcoming props
  → build PropBet (Pydantic)
  → run InsightsIdentifier (flags + templates)
  → persist {sport}_trends_insights
  → refresh on schedule (e.g. every 15 min)

bettor_index_rest_Api/
  → GET /trends?sport_key=...

fr/BettorIndex/
  → Trends tab (sport toggle, insight cards)
```

## Core Architecture

Two interfaces, one direction of data flow:

```text
TrendGetter (per sport)          InsightsIdentifier (per sport)
        │                                  │
        │  load slate, build PropBet       │  run _check_* flag methods
        └──────────────► PropBet ─────────►│  merge flags → headline
                                           └──────────► TrendInsight
```

### TrendGetter

- **Orchestrator** for one sport’s Trends pipeline.
- Reads from DB (v1: `{sport}_summaries`; alternative: `{sport}_hit_rates`).
- Converts ORM / JSON → **`PropBet`** once at the boundary.
- Calls `InsightsIdentifier.identify_insights(prop_bet)` per prop.
- Ranks, dedupes, returns or persists `TrendInsight` rows.

Implementations: `NbaTrendGetter`, `MlbTrendGetter`, `NflTrendGetter`.

### InsightsIdentifier

- **Evaluator** for a single prop. Does **not** query the DB.
- Runs shared + sport-specific `_check_*` methods (one per flag).
- Merges multiple fired flags into **one headline** (not multiple cards per prop).
- Returns `InsightResult | None` (notable or skip).

Implementations: `MlbInsightsIdentifier`, `NbaInsightsIdentifier`, `NflInsightsIdentifier`.

## PropBet — Domain Contract

`PropBet` is a **Pydantic model** (`schemas/prop_bet.py`). Never pass SQLAlchemy ORM rows into `InsightsIdentifier`.

Convert at the TrendGetter boundary:

```python
# From summary (v1)
prop_bet = PropBet.from_mlb_summary(summary_row)

# From hit_rates (alternative)
prop_bet = PropBet.from_hit_rate_rows(rows)
```

### Minimal fields (first flag: 10G hot)

| Field | Purpose |
|-------|---------|
| `sport_key`, `event_id`, `market_key`, `outcome_description` | Identity |
| `line`, `recommended_side`, `odds`, `bookmaker` | Bet footer on card |
| `rates.ten_game` | Last-10-game hit rate check |
| `commence_time`, `home_team`, `away_team` | Card context |

Optional fields can be added to `PropBet` as new checks are defined.

## Flag System

Additional flags will be defined later. For now, ship one check end-to-end before adding more.

### Last 10 game hit rate is hot

Implemented as `_check_ten_game_hit_rate_is_hot` on the sport `InsightsIdentifier`.

| Rule | Value |
|------|-------|
| Window | `ten_game_hit_rate` (from summary line payload or hit_rates) |
| Threshold | ≥ **0.70** (7 of 10) |
| Side | `recommended_side` on `PropBet` (OVER or UNDER — whichever side the hot rate applies to) |

Example headline:

```text
"{player} has {side_word} {line} {market_label} in {hits} of {possessive} last 10 games."
```

→ *"Aaron Judge has gone over 0.5 home runs in 8 of his last 10 games."*

### How checks become one-liners

Checks do **not** return English sentences directly:

```text
1. CHECK    _check_* methods  →  result + template vars (or None if not notable)
2. RENDER   template          →  headline string
```

When more flags exist later: **one card per prop**, merge into one headline (dedupe key: `event_id`, `market_key`, `outcome_description`).

## First Vertical Slice

1. `_check_ten_game_hit_rate_is_hot`
2. `MlbTrendGetter` loads `mlb_summaries` → `PropBet.from_mlb_summary`
3. `MlbInsightsIdentifier.identify_insights` → headline template
4. Persist to `mlb_trends_insights` (or return from worker)

## Data Sources

### v1 — Summaries (recommended)

Read `{sport}_summaries` where `commence_time > now`.

Map `summary_data` fields:

| PropBet field | Summary path |
|---------------|--------------|
| `rates.ten_game` | `best_over_line.ten_game_hit_rate` or under side |
| `line` | `best_*_line.outcome_line` for chosen side |
| `odds` | `best_*_price.outcome_price` |
Trends headlines come from **our templates**, not copied `bettorindexpropsignals.reason_text`.

### Alternative — Hit rates only

Read `{sport}_hit_rates`, group by `(event_id, market_key, outcome_description)`, resolve lines via `resolve_prop_signal_inputs` (same as prop summarizer). Use when summaries are missing or for decoupling.

## Refresh Strategy

| What | Cadence |
|------|---------|
| Insight flags + headlines | Every **15–30 min**, or on summary update |
| Odds in card footer | Join `odds_api_props` at **API read time** (optional) |
| Drop started games | Filter `commence_time <= now` on each run |

## Output — TrendInsight

Persist one row per prop per refresh (upsert on dedupe key):

| Field | Notes |
|-------|-------|
| `headline` | One-liner for the card body |
| `primary_flag`, `activated_flags` | Metadata (expand when more flags exist) |
| `side`, `line`, `odds`, `bookmaker` | Bet footer |
| `hit_streak` | `list[bool]` for green/red dots (when available) |
| `score` | Feed ranking |
| `evaluated_at` | Last run timestamp |

## Directory Layout

```text
main.py                      # poll loop, wire dependencies
worker/                      # TrendsWorker.refresh_all()
trend_getters/               # MlbTrendGetter, NbaTrendGetter, NflTrendGetter
insight_identifiers/         # MlbInsightsIdentifier, ...
interfaces/
  trend_getter.py            # TrendGetter ABC
  insights_identifier.py     # InsightsIdentifier ABC
schemas/
  prop_bet.py                # PropBet, PropBetRates, InsightResult, FlagResult
detectors/                   # Shared pure flag logic (add as new flags are defined)
renderers/
  templates.py               # TEMPLATES dict
  headline.py                # render_flag(), merge_to_headline()
repositories/                # summaries read, trends_insights write
db/                          # SQLAlchemy models
tests/                       # pytest; test detectors without DB
```

## Design Rules

- **PropBet at the boundary** — ORM → Pydantic in TrendGetter only.
- **InsightsIdentifier is DB-free** — receives `PropBet`, returns `InsightResult`.
- **Shared detectors, sport config** — extract shared logic when a second flag needs it.
- **One card per prop** — when multiple flags exist, merge into one headline.
- **Numbers from code, prose from templates** — never let LLM compute hit rates.
- **Skip noise** — no flag → no feed row. Empty feed beats spam.

## Sport Keys

| Sport | `sport_key` |
|-------|-------------|
| NBA | `basketball_nba` |
| MLB | `baseball_mlb` |
| NFL | `americanfootball_nfl` |

## Reference Implementations

| Concern | Reference |
|---------|-----------|
| Summary shape / hit-rate fields | `bettor_index_prop_summarizer_worker/summarizers/mlb_summarizer.py` |
| Line/price resolution from hit_rates | `bettor_index_prop_summarizer_worker/services/bettor_index_signal_input_resolver.py` |
| Market selection helpers | `bettor_index_prop_summarizer_worker/summarizers/market_selection.py` |
| Worker poll loop pattern | `bettor_index_prop_summarizer_worker/main.py` |
| Frontend Trends target | `fr/BettorIndex/src/app/(tabs)/` (Trends tab TBD) |
| Prop card summary fields | `fr/BettorIndex/src/services/bettorIndexApi.ts` (`PropMarketSummaryData`) |

## Out of Scope (v1)

- LLM browsing the DB or deciding what’s notable
- Team bet trends (totals/spreads) — props first
- `bettorindexpropsignals` as primary headline source
- Additional insight flags beyond last-10-game hot (TBD)
- REST API routes (wire in `bettor_index_rest_Api` separately)
- Duplicating hit-rate calculation (owned by `hit_rate_worker`)

## Run & Test

```bash
pip install -r requirements.txt
pytest
python main.py   # poll loop
```

## Adding a New Flag (later)

When a new check is defined:

1. Add `_check_*` on the sport identifier (or shared detector if reused across sports).
2. Add a template in `renderers/templates.py`.
3. Wire into `identify_insights` and document the rule in this file.
4. Unit test with a `PropBet` fixture — no DB required.
