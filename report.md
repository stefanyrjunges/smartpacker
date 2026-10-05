# SmartPack — Cloud Application Development Report

## 1. Introduction & Motivation

SmartPack is a web application that helps a traveller build a packing list for a trip. The user creates a trip (destination, dates and luggage type), adds the activities they plan to do, and the application generates a packing list tailored to that trip. The list takes into account how long the trip is, the weather forecast at the destination, the activities chosen, and the type of luggage the user is bringing.

**The problem.** Packing is repetitive and easy to get wrong. People forget weather-appropriate items (a rain jacket, a warm layer), over-pack when they only have carry-on space, or forget activity-specific gear (hiking boots, swimwear). A generic checklist does not adapt to the actual trip.

**Objectives.**

- Let a user register, log in, and manage their own trips securely.
- Provide full create/read/update/delete functionality for trips and packing items.
- Generate a packing list that genuinely reacts to trip length, destination weather, chosen activities, and luggage type.
- Integrate a real external weather service rather than hard-coded data.
- Deploy the application to a public cloud platform with a continuous integration pipeline.

The application is split into a standalone REST backend (Flask) and a standalone single-page frontend (SvelteKit) that talk to each other only through JSON API calls.

## 2. Requirements & Application Design

**Main functional requirements.**

- **Authentication:** register with email and password, log in, stay logged in across page reloads, log out.
- **Trips (full CRUD):** create a trip, view a list of the user's trips, view one trip, edit a trip, delete a trip.
- **Activities:** add one or more activities to a trip, list them, remove one.
- **Weather:** fetch the forecast for the trip destination and dates from an external service.
- **Packing list:** automatically generate a list from the trip data, mark items as packed/unpacked, add a custom item, delete an item, and regenerate the generated items while keeping custom ones.
- **Data isolation:** a logged-in user can only see and modify their own data.

**Architecture.** SmartPack uses a two-tier client/server architecture:

```
[ SvelteKit SPA ]  --- HTTPS / JSON (fetch) --->  [ Flask REST API ]  --->  [ PostgreSQL (Neon) ]
   (browser)              Authorization: Bearer <JWT>                         SQLAlchemy ORM
```

- The **frontend** is a static single-page app. It holds no server-side logic; it renders in the browser and calls the API with `fetch`, attaching a JWT for protected requests.
- The **backend** is a REST API. Each endpoint is a resource with the appropriate HTTP verb. It validates input, enforces authentication/ownership, talks to the database through SQLAlchemy, and calls the external weather service when needed.
- The **database** stores users, trips, activities, packing items, and a weather cache. In production it is PostgreSQL hosted on Neon; locally and in tests it falls back to SQLite.

## 3. Technology Stack & Design Decisions

The brief asks _why this stack_ and _what alternatives were considered_, so each choice is justified below.

**Backend framework — Flask.**
Chosen because it is lightweight and unopinionated, which suited a REST-only API with no server-rendered HTML. The routing-by-decorator style (`@app.post`, `@app.get`) keeps each endpoint short and readable.
_Alternatives considered:_ Django (rejected — it bundles an ORM, admin, templating and auth that would be mostly unused for a pure JSON API, adding weight I did not need); FastAPI (a reasonable modern option with built-in validation, but I was more familiar with Flask and the project did not need async performance).

**Frontend framework — SvelteKit (Svelte 5).**
Chosen because Svelte compiles to small, plain JavaScript and has very little boilerplate, which made it approachable as someone new to the framework. SvelteKit gave me file-based routing (including the dynamic `trips/[id]` route) for free. The app is built as a static SPA using `@sveltejs/adapter-static`.
_Alternatives considered:_ React (far larger ecosystem but more boilerplate and hooks complexity than this project warranted); plain HTML/JS (would have meant hand-writing routing and reactivity).

**ORM — SQLAlchemy (via Flask-SQLAlchemy).**
Chosen so I could define the data model as Python classes and switch databases (SQLite locally, PostgreSQL in production) by changing only a connection string, without rewriting queries.
_Alternatives considered:_ raw SQL with a driver (more control but more boilerplate and higher SQL-injection risk if I built queries by hand).

**Database — PostgreSQL on Neon.**
Chosen because Render's own disks are ephemeral (data would be lost on redeploy/restart), so a managed external database was necessary. Neon offers a free serverless PostgreSQL tier that integrates with Render through a single `DATABASE_URL`.
_Alternatives considered:_ SQLite in production (rejected — not safe on an ephemeral/async host and data would not persist); a paid managed database (unnecessary cost for a student project).

**Hosting / PaaS — Render.**
Chosen because it deploys straight from a GitHub repository, offers a free tier, runs the Flask app under gunicorn, serves the static frontend, and supports auto-deploy on push (the "CD" part of the pipeline).
_Alternatives considered:_ [I don't have the answer for which other PaaS options you weighed (e.g. Heroku, Vercel, Fly.io). Complete this section with the alternatives you actually considered and why you rejected them.]

**Authentication — JWT (flask-jwt-extended).**
Chosen because the frontend is a stateless SPA on a different origin from the API, so a token the browser stores and sends on each request fits better than server-side sessions/cookies. Passwords are hashed with Werkzeug's `generate_password_hash`.
_Alternatives considered:_ server-side sessions (awkward across separate frontend/backend origins and not stateless).

**Weather data — Open-Meteo.**
Chosen because it is free, requires no API key, and provides both a geocoding endpoint (city name → coordinates) and a daily forecast endpoint, which is exactly what the packing logic needs.
_Alternatives considered:_ OpenWeatherMap and similar (rejected — they require an API key and have stricter free-tier limits; a keyless API also simplified deployment because there was no secret to manage for weather).

## 4. Frontend Implementation

The frontend is a SvelteKit single-page application. `src/routes/+layout.js` sets `export const ssr = false;` so the whole app runs in the browser, which is appropriate because it relies on `localStorage` and `fetch`.

**Pages / routes.**

| Route                                                            | Purpose                                          |
| ---------------------------------------------------------------- | ------------------------------------------------ |
| `/login` (`routes/login/+page.svelte`)                           | Email/password sign-in form                      |
| `/register` (`routes/register/+page.svelte`)                     | Account creation form                            |
| `/` (`routes/+page.svelte`)                                      | List of the user's trips + "new trip" form       |
| `/trips/[id]` (`routes/trips/[id]/+page.svelte`)                 | View/edit one trip: details, activities, weather |
| `/trips/[id]/packing` (`routes/trips/[id]/packing/+page.svelte`) | The generated packing list for that trip         |

**Shared pieces.**

- `src/routes/+layout.svelte` renders the top navigation (app name, logged-in email, log-out button) and runs an `$effect` that redirects to `/login` on any route if there is no token, so protected pages cannot be viewed logged-out.
- `src/lib/auth.js` holds the auth state in a small Svelte store (`token`, `userEmail`) and persists it to `localStorage`, so a page reload keeps the user logged in.
- `src/lib/api.js` is a thin `apiFetch` wrapper that prepends the API base URL, adds the `Authorization: Bearer <token>` header, and on a `401` clears the stored token and sends the user back to `/login`.
- `src/app.css` holds a small shared style system (`.card`, `.btn-primary/secondary/danger`, `.error`, form layout) reused across pages.

**Forms and interaction.** The create-trip form, login, register, add-activity and add-item forms all use normal two-way binding (`bind:value`) and submit handlers. The trip page has a view mode and an edit mode driven by a `?mode=` query parameter. The packing list groups items by category and shows a "packed / total" counter, with checkboxes toggling the packed state.

**Validation and error feedback.** Each form keeps a local `error`/`submitting` state. On a failed request the message returned by the API (`data.message` / `data.error`) is shown to the user, and buttons are disabled while a request is in flight ("Signing in…", "Creating…", etc.). The trip-edit save and the activity-remove actions check the response and show an error message if the backend rejects the change, so edits do not fail silently.

**API communication.** The API base URL comes from the `PUBLIC_API_URL` environment variable via `$env/dynamic/public` (`API_URL = env.PUBLIC_API_URL || ''` in `src/lib/api.js`). Locally this is set in `frontend/.env` to `http://localhost:5000`; in production it is set in Render to the deployed API URL. No API URL is hard-coded in the components.

**Screenshots.** [I don't have the answer for the frontend screenshots — add screenshots of the login page, trips list, trip edit view, weather panel, and generated packing list here. Complete this section.]

## 5. Backend & Database

The backend (`backend/flask_app.py`) is a REST API. Every data endpoint except register/login is protected with `@jwt_required()` and resolves the current user from the token.

**Endpoint table.**

| Method | Path                                   | Purpose                                                         | CRUD  |
| ------ | -------------------------------------- | --------------------------------------------------------------- | ----- |
| POST   | `/auth/register`                       | Create account, return JWT                                      | —     |
| POST   | `/auth/login`                          | Authenticate, return JWT                                        | —     |
| POST   | `/trips`                               | Create a trip                                                   | **C** |
| GET    | `/trips`                               | List the user's trips                                           | **R** |
| GET    | `/trips/<id>`                          | Get one trip                                                    | **R** |
| PUT    | `/trips/<id>`                          | Update a trip                                                   | **U** |
| DELETE | `/trips/<id>`                          | Delete a trip (+ its activities, items, weather)                | **D** |
| GET    | `/trips/<id>/activities`               | List activities                                                 | **R** |
| POST   | `/trips/<id>/activities`               | Add activities                                                  | **C** |
| DELETE | `/trips/<id>/activities/<activity_id>` | Delete an activity                                              | **D** |
| GET    | `/trips/<id>/weather`                  | Get weather (cached or fetched); `?refresh=true` forces refetch | **R** |
| GET    | `/trips/<id>/packing-list`             | Get or generate the packing list                                | **R** |
| POST   | `/trips/<id>/packing-list`             | Add a custom item                                               | **C** |
| PATCH  | `/trips/<id>/packing-list/<item_id>`   | Update an item (packed state)                                   | **U** |
| DELETE | `/trips/<id>/packing-list/<item_id>`   | Delete one item                                                 | **D** |
| DELETE | `/trips/<id>/packing-list`             | Delete the whole list                                           | **D** |
| POST   | `/trips/<id>/packing-list/regenerate`  | Regenerate generated items, keep custom                         | —     |

This gives complete CRUD: Create, Read, Update and Delete are all demonstrated on trips, and Create/Read/Update/Delete on packing items.

**SQLAlchemy models** (`backend/database/models.py`): `User`, `Trip`, `Activity`, `PackingItem`, `WeatherCache`. Relationships are expressed with foreign keys — `Trip.user_id → User.id`, and `Activity`, `PackingItem`, `WeatherCache` each hold a `trip_id → Trip.id`. Queries use `db.session.get(...)` for primary-key lookups and `.filter_by(...).all()/.first()` elsewhere.

**Production database (Neon) with a local/test fallback.** The connection string is read from `DATABASE_URL`, defaulting to a local SQLite file if it is unset. Render/Neon supply URLs beginning with `postgres://`, which SQLAlchemy needs as `postgresql://`, so the code rewrites that prefix. For PostgreSQL connections it also sets `pool_pre_ping=True` and `pool_recycle=300` so dropped idle connections are detected and replaced (see Challenges). Tests set `DATABASE_URL=sqlite:///:memory:` before the app is imported, so they never touch Neon.

**Validation.**

- `trip_functions.validate_data` — all fields required, dates must be `YYYY-MM-DD`, end date not before start date, and luggage type must be one of `checked` / `carry-on` / `backpack` (normalised to lowercase). Used by both create and update.
- `trip_functions.validate_activities` — must be a non-empty list of non-blank strings.
- `register` — email and password required, password at least 6 characters, duplicate email rejected with 409.
- `add_packing_item` — item name required, quantity must be a positive integer.
- All write endpoints read JSON with `get_json(silent=True)` and reject anything that is not a JSON object with a 400.

**Authentication, authorization and data isolation.** Passwords are stored only as hashes. Protected endpoints get the user id from the JWT, never from the request body. Every trip-scoped endpoint checks `trip.user_id == current_user` and returns 404 if not, and sub-resources (activities, items) additionally confirm they belong to that trip. This means one authenticated user cannot read or modify another user's trips or items — a behaviour that is also covered by an automated test.

## 6. Meaningful Functionality / Library

The functionality that goes beyond basic CRUD is the **packing-list generation engine** combined with the **weather integration and caching**. This is the application's core value and is deliberately kept in separate, self-contained modules so it is easy to point to and explain.

**Packing-list generation** (`backend/packing_functions.py`). `generate_packing_list(trip, activities, weather)` is a pure function (no database, no Flask) that builds the list from four inputs:

1. **Trip duration** — `(end_date - start_date).days + 1`. Basic clothing quantities (underwear, socks, t-shirts) scale with the number of days.
2. **Weather** — rules add items based on the forecast: rain expected → rain jacket + umbrella; minimum temperature below 10°C → warm jacket + scarf; below 5°C → gloves; maximum temperature 20°C or above → sunscreen + sunglasses.
3. **Activities** — each activity name is looked up (case-insensitively) in an `ACTIVITY_ITEMS` table of about two dozen activities (hiking, swimming, skiing, business, etc.), and the matching gear is added. Duplicate items from two activities are only added once.
4. **Luggage type** — for `carry-on` or `backpack`, the basic clothing quantities are capped at 5 so the user does not over-pack for limited space.

Each generated item carries a short `reason` (e.g. "Rain expected", "Added for hiking") so the user understands why it is on the list.

**Weather integration** (`backend/weather_functions.py`). `get_weather` calls Open-Meteo twice: first the geocoding endpoint to turn the destination name into coordinates, then the forecast endpoint for the trip's date range. It summarises the daily data into min/max temperature, total precipitation and a `rain_expected` flag. It handles the realistic failure cases explicitly and returns a friendly `error` message for each: network/timeout errors, an unknown destination, and dates with no available forecast (Open-Meteo only forecasts ~16 days ahead). This result is what feeds the weather rules above, so the integration genuinely drives the application rather than just demonstrating an API call.

**Weather caching** (`get_or_fetch_weather` in `flask_app.py`, backed by the `WeatherCache` table). The first time weather is needed for a trip, the result is fetched and stored in the database. Subsequent requests reuse the stored row instead of calling Open-Meteo again. A cached row is only replaced when the user explicitly refreshes (`?refresh=true`, which deletes the row then refetches), and it is removed when the trip is deleted. Storing the cache in the database (rather than in memory) was a deliberate decision so it survives Render restarts and the free-tier instance sleeping (see Challenges).

## 7. Testing

**Approach.** Tests are automated with **pytest** and run from `pytest.ini` (`testpaths = backend/tests`). They run against an **isolated in-memory SQLite database**: `backend/tests/conftest.py` sets `DATABASE_URL=sqlite:///:memory:` before the app is imported, and the `client` fixture creates and drops all tables around each test, so the production Neon database is never touched. A second fixture registers a user and returns an `Authorization` header for the protected-route tests.

**Types of tests and representative cases.**

- **Unit tests** of the pure logic:
  - `test_packing_functions.py` tests `generate_packing_list` with lightweight fake trip/activity objects — e.g. duration setting clothing quantity, rain adding rain items, cold adding warm items + gloves, activity gear being added, duplicates not being added twice, unknown activities being ignored, and the carry-on/backpack quantity cap.
  - `test_trip_functions.py` tests the validators directly — valid data, missing fields, blank destination, invalid date format, end-before-start, invalid luggage type, and luggage normalisation to lowercase.
- **Functional / API (integration) tests** (`test_api.py`) drive the real Flask app through its HTTP routes, JWT auth and the database together — e.g. register returns a token, short password rejected, duplicate email rejected, login success/failure, protected route returns 401 without a token, create-then-read a trip, update a trip, invalid luggage/date rejected on write, delete a trip and confirm it is gone, add/list/delete activities, add/toggle/delete a packing item, and that one user cannot see or open another user's trip (data isolation).
- **External-service failure and caching** are covered by using pytest's built-in `monkeypatch` to replace the weather call with a fake, so the tests verify that a weather failure returns an error response, and that a cache miss fetches once and then reuses the stored result without calling the service again — all without making a real network request.

**Number of automated tests.** There are **45** automated tests in total (12 packing unit tests, 13 trip/validator unit tests, and 20 API/integration tests). [If you quote a number in the video, re-run `pytest` first and use the live count in case the suite has grown.]

**pytest screenshot.** [I don't have the answer for the pytest screenshot — add a screenshot of the full `pytest` run passing. Complete this section.]

**Manual testing (SmartPack manual test).** [I don't have the answer for exactly what your "SmartPack manual test" document/checklist contains or its results. Complete this section with your manual test checklist and outcomes. A suggested checklist you can base it on, performed against the deployed URL: register, log in, authentication redirect when logged out, create a trip, view a trip, edit a trip, delete a trip, add/remove activities, get weather, confirm weather is cached (second load is instant / refresh forces a refetch), generate the packing list, add a custom item, toggle packed/unpacked, delete an item, confirm a second user cannot see the first user's trips, and that logging out then back in keeps the data.]

## 8. CI/CD & Cloud Deployment

**Continuous Integration — GitHub Actions** (`.github/workflows/ci.yml`). The workflow triggers on every **push to `main`** and on **pull requests targeting `main`**. It runs two independent jobs:

- **Backend tests:** checks out the repo, sets up Python 3.12, installs `requirements.txt`, and runs `python -m pytest`.
- **Frontend build:** checks out the repo, sets up Node 22, runs `npm ci` and `npm run build` in `frontend/`.

Because each job fails if its command returns a non-zero exit code, a failing test or a broken frontend build fails the workflow, so problems are caught before deployment.

**Continuous Delivery / Deployment — Render.** Render is connected to the GitHub repository with auto-deploy on `main`, so a push that passes is redeployed automatically. The backend runs under gunicorn; the frontend is served as a static site built by `npm run build`.

**Production architecture and environment variables.**

```
GitHub (push to main) → GitHub Actions (tests + build) → Render auto-deploy
   Render: Flask API (gunicorn)  +  Static SvelteKit site
   Neon: managed PostgreSQL
```

Environment variables used in production: `DATABASE_URL` (Neon connection string), `JWT_SECRET_KEY` (signing key for tokens), and `PUBLIC_API_URL` (the deployed API URL, used by the frontend build). None of these are stored in the repository.

**Deployed application URL.** [I don't have the answer for your live Render URL(s). Add the deployed frontend and API URLs here.]

**Render configuration details.** [I don't have the answer for your exact Render dashboard settings. Complete this section with: the backend build command and start command (e.g. `gunicorn flask_app:app`), the backend root/working directory, the frontend build command and publish directory, and confirmation that auto-deploy is enabled for `main`.]

**Screenshots.** [I don't have the answer for these screenshots — add a screenshot of a successful GitHub Actions run and a screenshot of the deployed application, plus (recommended) the Render deploy/event history showing a deploy triggered by a GitHub commit as evidence of CD. Complete this section.]

## 9. Challenges & Solutions

**Local SQLite to production PostgreSQL.** Developing against a local SQLite file but deploying to PostgreSQL meant the app had to work with both. _Solution:_ the database URL is read from `DATABASE_URL` with a SQLite fallback, so no code changes are needed between environments — only the environment variable differs.

**PostgreSQL URL prefix.** Render/Neon provide connection strings beginning with `postgres://`, but SQLAlchemy requires `postgresql://`. _Solution:_ the app rewrites the prefix at startup before configuring the database. (The PostgreSQL driver itself is provided by `psycopg[binary]` in `requirements.txt`.) [If the driver specifically caused a deployment error you remember, add that detail and the exact fix here — the brief rewards reporting the workaround.]

**Stale / dead database connections.** Neon closes idle connections, which left dead connections in SQLAlchemy's pool and caused intermittent errors on the first request after the app had been idle. _Solution:_ enable `pool_pre_ping=True` (test a connection before using it, replacing it if dead) and `pool_recycle=300` (retire connections after five minutes) for PostgreSQL.

**Open-Meteo rate limiting.** On the hosted environment the weather API could be called too often (e.g. every time the packing list or trip page loaded), risking hitting the free-tier limit. _Solution:_ the weather caching described in Section 6 — fetch once per trip and store the result in the `WeatherCache` table, only re-fetching on an explicit refresh.

**Weather caching on an ephemeral host.** An in-memory cache would be wiped whenever the free Render instance restarts or sleeps, so it would barely help. _Solution:_ store the cache in the database so it persists across restarts and sleeps. _Known trade-off (for honesty in the report):_ the cache has no automatic time-based expiry, so if a user changes a trip's dates or destination the cached weather stays until they refresh.

**Environment-specific frontend API URL.** The frontend needed to call `localhost` during development but the deployed API in production, without hard-coding either. _Solution:_ read the base URL from the `PUBLIC_API_URL` environment variable (`frontend/.env` locally, Render setting in production), used by the single `apiFetch` wrapper.

**Most difficult part.** [I don't have the answer for which of these you personally found hardest. The brief asks you to name the most difficult part and how you solved it — pick one of the above (the stale-connection or caching issue tends to make the strongest story) and write a short first-person account. Complete this section.]

## 10. Conclusion

**What was achieved.** SmartPack is a complete, deployed two-tier cloud application: a standalone SvelteKit frontend talking to a standalone Flask REST API over JSON, backed by managed PostgreSQL on Neon. It provides secure per-user authentication with JWT, full CRUD on trips and packing items, real external weather integration with database-backed caching, and a packing-list generator that reacts to trip duration, weather, activities and luggage type. It is covered by 45 automated pytest tests spanning unit and API/integration levels (including validation, authorization/data isolation, and external-service failure handling) against an isolated test database, with a GitHub Actions CI pipeline and Render auto-deploy.

**Limitations.**

- The weather cache has no time-based expiry (only manual refresh), so cached data can become stale after a trip is edited.
- Packing items can only have their packed state edited, not their name or quantity, after creation.
- CORS is left open to all origins, which is acceptable for a student demo but would be tightened for real use.
- [Add any other limitations you want to acknowledge.]

**Possible future improvements.**

- Add a timestamp to the weather cache and expire it automatically (and re-fetch when a trip's dates/destination change).
- Allow editing an item's name and quantity.
- Add a few more activities and smarter quantity rules.
- [Add any further improvements you would highlight in the video.]
