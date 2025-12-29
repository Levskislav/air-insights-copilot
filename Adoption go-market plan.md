image.png# Go-to-Market Plan (0–90 дни) — Air & Insights Copilot (сняг + места + маршрути)

Този документ е **практически план за реално използване (adoption)**, след като надградиш продукта с:
- **snowfall** (снеговалеж) и **snow depth** (снежна покривка/дълбочина)
- **въвеждане на място по име** (geocoding)
- **време по маршрута A → B** (route weather report)

Фокусът е: **по-малко “функции”**, повече **навик и доверие**.

---

## 0) Какво е успех (90-дневни цели)

### North Star (предложение)
**Weekly Decisions Helped (WDH)**  
= # уникални потребители седмично, които получават “verdict” (OK / Caution / Avoid) за:
- Run safety / outdoor activity
- Snow conditions
- Route safety

### Цели (ориентир)
- **D7 retention ≥ 12–20%** (consumer продукт в ниша)
- **≥ 25–40% activation** (първа успешна заявка + разбираем резултат)
- **≥ 15%** от активираните да “Save” (любимо място/маршрут)
- **p95 latency < 2s** при cached, **< 4s** при cold (с LLM)
- **cache hit rate ≥ 35–60%** (след като има повторни заявки)

> Ако си B2B/Teams-first, целите се променят: “# активни седмични екипи”, “# активни маршрути”, “# спестени инциденти” и т.н.

---

## 1) Readiness gates (преди да започнеш marketing)

Adoption умира, ако продуктът е бавен/неточен/чуплив. Преди първи публичен push:

### 1.1 Продуктови gates
- [ ] Място по име → координати работи стабилно (и кешира)
- [ ] Snowfall + snow depth се показват ясно (и в “verdict”)
- [ ] Route report дава 3–6 checkpoint-а, а не 100 точки
- [ ] “Confidence: high/medium/low” според данните
- [ ] Attribution: **Weather data by Open-Meteo.com** присъства винаги

### 1.2 Reliability gates
- [ ] Retry/backoff + timeouts работят
- [ ] Fallback, ако LLM падне (rule-based guidance)
- [ ] Rate limiting (за да не “изгърмиш” разходи по Maps APIs)
- [ ] Мониторинг: error rate, latency, upstream failures

### 1.3 Trust gates (изключително важни)
- [ ] Показваш ключовите числа + източник + timestamp
- [ ] Disclaimer: “Не е официален бюлетин; проверявай и условията на пътя.”
- [ ] Не даваш “медицински” твърдения, а общи предпазни препоръки

---

## 2) Позициониране и messaging (как да го обясниш за 5 секунди)

### Основно обещание (headline)
**„Провери въздух + сняг + време по маршрута — и вземи решение за 30 секунди.“**

### 3 “булета”, които продават
- **Маршрут A→B:** къде по пътя ще е най-лошо и кога  
- **Сняг:** ще вали ли + колко сняг има/ще натрупа  
- **Въздух:** безопасно ли е за бягане/навън

### Какво НЕ казваш
- “Имаме API”, “имаме LLM”, “агентски поток” — това е важно технически, но не продава на потребителя.

---

## 3) Канали за growth — стратегия по канал

### 3.1 Organic / SEO (най-подходящ за този продукт)
**Защо:** хората търсят конкретни неща: “време по маршрут София Банско”, “снеговалеж Витоша”, “PM2.5 София”.

**Какво правиш:**
- Landing страници за:
  - “Route Weather Report: София → Банско”
  - “Snow conditions: Витоша”
  - “Air quality + run safety: София”
- Блог статии + интерактивен widget “Провери сега”

**Как мериш:**
- organic sessions → activation rate → saved routes

### 3.2 Communities (Facebook групи / форуми / Reddit / Strava)
**Защо:** зимните пътувания и планината имат силни общности.

**Тактики:**
- “Shareable report” линк (route report), който хората да пращат в групи
- “Weekly winter briefing” post (без spam)

**Как мериш:**
- share click-through → activation

### 3.3 Partnerships (локални)
**Варианти:**
- ски училища/тур оператори: “провери условия”
- авто сервизи/гуми/вериги: “route safety”
- медии/сайтове за планина/туризъм

**Как мериш:**
- referral traffic + conversion

### 3.4 Track A: Copilot/Teams (B2B)
**Кога:** след като route report е стабилен и имаш OpenAPI + hosted endpoint.

**Къде влиза:**
- логистика, field service, куриери
- “morning route risk briefing” в Teams

---

## 4) 0–90 дни план по седмици (включва продукт + growth)

### Седмици 1–2: “Activation first”
**Цел:** потребителят да получи “аха” без усилие.

**Продукт**
- [ ] Place search (autocomplete) + кеш 7 дни
- [ ] Snow variables (snowfall, snow depth) в output
- [ ] Quick actions: “Air & Run”, “Snow”, “Route”
- [ ] Output template: Verdict + 3 bullets + numbers + confidence

**Growth**
- [ ] Landing page + 3 use-case секции
- [ ] “Share report” функционалност (дори да е прост link)
- [ ] Първи 10–20 ръчни user interviews (15 мин) — планинари/шофьори

**Success критерии**
- Activation ≥ 25%  
- Time-to-first-value ≤ 45 сек (в web UI)

---

### Седмици 3–4: “Route Weather Report” v1 + първи публичен push
**Цел:** feature, който хората споделят.

**Продукт**
- [ ] Directions A→B → polyline (route geometry)
- [ ] Sampling: 3–6 checkpoint-а (ключови точки) с ETA
- [ ] Weather along route: temp + snowfall + wind (ако имаш) + precipitation
- [ ] Risk summary (“worst segment”)

**Growth**
- [ ] Публикувай 5 SEO страници за най-търсените маршрути (БГ):
  - София→Банско, София→Боровец, София→Пловдив, Пловдив→Пампорово, Варна→Бургас
- [ ] 10 поста в общности (без линк спам — с примерен screenshot и “ако искате линк, пишете”)

**Success критерии**
- ≥ 10% от активираните правят “Route report”
- ≥ 5% share rate на route report

---

### Седмици 5–6: “Retention engine” v1
**Цел:** хората да се връщат без да ги молиш.

**Продукт**
- [ ] Save place / Save route
- [ ] Morning briefing (email/push/в web като “Today” таб)
- [ ] Alerts: “snowfall > X”, “temp < Y”, “PM2.5 > Z” (simple thresholds)
- [ ] Weekly digest (за тези, които не искат daily)

**Growth**
- [ ] Onboarding: “избери 1 маршрут + 1 място”
- [ ] “Add to Home Screen” (PWA) call-to-action

**Success критерии**
- D7 retention ≥ 12%
- ≥ 15% от активираните имат saved item

---

### Седмици 7–8: “Trust & depth”
**Цел:** доверие + по-добри решения.

**Продукт**
- [ ] Confidence score (high/med/low) базирано на данни + upstream статус
- [ ] Показвай timestamp, timezone, source
- [ ] “Why this advice” (1–2 изречения)
- [ ] Improve caching strategy (route cache 10–30 мин; place cache 7 дни)

**Growth**
- [ ] 2 партньорства (минимум) — пример: ски школа + авто клуб/група
- [ ] 1 guest post/интервю (local media / блог)

**Success критерии**
- по-нисък bounce rate
- по-висок completion rate на route report

---

### Седмици 9–12: “Scale + B2B wedge”
**Цел:** стабилност + първи B2B пилот (ако желаеш).

**Продукт**
- [ ] Rate limits + quotas (за maps APIs)
- [ ] Observability: dashboards + alerts (latency, errors)
- [ ] Export/print route report (PDF/Share link)

**Growth**
- [ ] Copilot Studio (Track A) пилот с 1 организация:
  - логистика/куриер/field service
- [ ] Case study: “спестихме X време/рискове”

**Success критерии**
- ≥ 1 B2B pilot
- стабилен error rate < 1–2%

---

## 5) Growth експерименти (готови за изпълнение)

> Всеки експеримент: **Hypothesis → Setup → Metric → Success → Duration**

### E1: Place-first onboarding
- Hypothesis: Ако започнеш с “въведи място” + предложения, activation се качва.
- Setup: нов начален екран с autocomplete + “Try Sofia” бутон.
- Metric: activation rate, time-to-first-value.
- Success: +20% activation vs baseline.
- Duration: 7 дни.

### E2: Route report share link
- Hypothesis: Share link ще създаде органични referrals.
- Setup: “Share” button → уникален URL (с TTL 24–72h).
- Metric: share rate, referral sessions, activation from referral.
- Success: ≥5% share rate; ≥10% of referral sessions activate.
- Duration: 14 дни.

### E3: “Worst segment” card
- Hypothesis: Показването на най-рисковия сегмент увеличава доверие.
- Setup: UI card “Worst segment: …” + кратък съвет.
- Metric: completion rate, return rate.
- Success: +10% completion.
- Duration: 10 дни.

### E4: Alerts opt-in
- Hypothesis: Лесен threshold alert увеличава retention.
- Setup: “Notify me when snowfall > X”.
- Metric: opt-in rate, D7 retention.
- Success: ≥8–12% opt-in от активни users; +3–5pp D7.
- Duration: 2–3 седмици.

### E5: SEO landing pages for top routes
- Hypothesis: “Маршрут + време” keywords ще донесат качествен трафик.
- Setup: 10 landing pages с route report embed.
- Metric: organic sessions, activation.
- Success: 500+ organic sessions/месец в 4–6 седмици, activation ≥ 20%.
- Duration: 6–8 седмици.

---

## 6) Content календар (12 седмици)

Минимум: **2 SEO статии/седмица + 3 кратки поста/седмица**.

### Теми (примерни заглавия)
**Route / Winter**
- “София → Банско: какво време да очакваш по пътя (по часове)”
- “Кога са нужни вериги? (какво казва прогнозата за снеговалеж)”
- “Най-рисковите часове за пътуване към планината (примерни маршрути)”

**Snow conditions**
- “Снежна покривка: как да четеш snow depth и какво означава за пътя”
- “Снеговалеж vs снежна покривка: защо може да вали, но да не натрупа”

**Air & Run**
- “PM2.5: какво означава за тренировка навън (практично)”
- “Комбинация: студ + замърсяване — как да планираш бягане”

### Седмичен ритъм
- Понеделник: “Morning briefing” пост (social)
- Сряда: SEO статия #1 + shareable report
- Петък: SEO статия #2
- Уикенд: “планина/маршрут” кратък пост + линк

---

## 7) Partnerships (партньорства) — списък + как да ги “пичнеш”

### 7.1 Топ 10 партньорски идеи (БГ)
1) Ски училища (Банско, Боровец, Пампорово)  
2) Туроператори/организатори на планински преходи  
3) Авто клубове и групи (FB)  
4) Магазини за зимни гуми/вериги/авто аксесоари  
5) Блогове за планина/туризъм  
6) Страва/бегачески общности  
7) Локални новинарски/пътни бюлетини (guest section)  
8) Компании за доставки (пилот)  
9) Car rental компании (upsell: “route safety check”)  
10) Хотели в курорти (в сайта им: “Check route weather”)

### 7.2 Pitch template (кратък)
- “Ние даваме route weather report + snow conditions, за да намалим изненадите при пътуване.”
- “Можем да embed-нем widget за вашия най-чест маршрут/локация.”
- “В замяна: линк/партньорска страница / промо код.”

---

## 8) KPI dashboard (какво да измерваш и как)

### 8.1 Събития (event instrumentation)
Започни с минимум 12 event-а:

**Acquisition**
- `page_view` (source/medium)
- `share_link_opened` (referrer)

**Activation**
- `place_search` (query_length)
- `place_selected` (place_id)
- `analyze_submitted` (hours)
- `route_submitted` (A, B, depart_time_present)
- `first_value_rendered` (latency_ms)

**Retention**
- `save_place`
- `save_route`
- `alert_opt_in`
- `briefing_opened`

**Quality**
- `api_request` (endpoint, cache_hit, upstream_ok)
- `llm_fallback_used`
- `error` (type, upstream)

### 8.2 Дашборди
**Dashboard A: Adoption funnel**
- visits → first action → first value → saved item → returning user

**Dashboard B: Feature usage**
- % users using:
  - route report
  - snow report
  - air/run report

**Dashboard C: Reliability & performance**
- p50/p95 latency
- cache hit rate
- error rate per upstream (Open-Meteo / Maps / Directions / LLM)

**Dashboard D: Cost control** (ако ползваш Maps)
- geocoding requests/day
- directions requests/day
- cost per active user (ориентировъчно)

### 8.3 Success thresholds (аларми)
- error rate > 2% (5 мин) → alert
- p95 > 5s (10 мин) → alert
- llm_fallback > 20% (1 час) → investigate
- cache hit < 20% (седмично) → optimize caching + UX prompts

---

## 9) Pricing / монетизация (ако решиш по-късно)
За adoption първо дръж безплатно/лесно, но мисли за бъдещо:

**Freemium идеи**
- Free: 3 route reports/ден, 2 saved routes
- Pro: unlimited + alerts + PDF export + multi-stop routes

**B2B**
- per team / per route / per seat (Teams integration)

---

## 10) Следващи артефакти (ако искаш да продължим)
Ако кажеш “да”, мога да генерирам още 3 файла:
1) **Product roadmap** (user stories + приоритизация + acceptance criteria)
2) **UX wireframes описание** (екрани, компоненти, текстове)
3) **KPI spec** (точни event schemas + примерни SQL/PQL заявки за PostHog/GA4)

