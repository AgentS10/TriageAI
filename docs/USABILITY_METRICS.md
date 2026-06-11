# TriageAI — Figma Wireframe Usability Metrics

**Purpose:** Define the **measurable usability metrics** tied to each Figma
wireframe / screen, the instruments used to capture them, and the target
thresholds. This formalises usability evaluation so results are quantitative
and reproducible rather than anecdotal.

Companion documents:

- `docs/figma_wireframes.md` — the wireframe specifications
- `docs/sus_questionnaire.md` — the SUS + clinical instrument
- `docs/uat_script.md` — the task scenarios testers perform

---

## 1. Metric framework

Usability is measured across the ISO 9241-11 dimensions —
**effectiveness, efficiency, satisfaction** — plus learnability.

| Metric | Definition | Instrument | Target |
| --- | --- | --- | --- |
| Task Success Rate | % of tasks completed without facilitator help | UAT observation | ≥ 90% |
| Time on Task (TOT) | Median seconds to complete a task | Stopwatch / timestamps | See per-screen table |
| Error Rate | Errors (wrong field, invalid submit) per task | UAT observation | ≤ 1 per task |
| SUS Score | System Usability Scale (0–100) | `sus_questionnaire.md` | ≥ 70 |
| Single Ease Question (SEQ) | 1–7 ease rating per task | Post-task prompt | ≥ 5.5 |
| Learnability | TOT improvement between 1st and 2nd attempt | Repeated trial | ≥ 20% faster |
| Explainability Trust | Clinical item B (SHAP helpfulness) | SUS supplement | ≥ 4 / 5 |

---

## 2. Per-screen metrics (mapped to Figma wireframes)

| Wireframe / Screen | Primary task | Time-on-task target | Key success criterion |
| --- | --- | --- | --- |
| Login | Authenticate | ≤ 15 s | Reaches dashboard on first valid attempt |
| Dashboard / Queue | Identify highest-priority patient | ≤ 10 s | Selects correct ESI-1/2 patient |
| Patient Intake | Enter vitals + chief complaint | ≤ 90 s | All fields valid, no range errors |
| Triage Result | Read ESI + SHAP, decide | ≤ 30 s | Correctly interprets recommendation |
| Override Modal | Override with coded reason | ≤ 25 s | Selects reason code, submits |
| Admin — Audit Log | Locate a specific event | ≤ 20 s | Finds entry via filter |

---

## 3. Data-capture method

1. **Pre-test:** capture tester role and ED experience (confound control).
2. **Per task:** record start/stop timestamps, success/fail, error count,
   and SEQ rating.
3. **Post-test:** administer the 10-item SUS + 5 clinical supplement items.
4. **Analysis:** compute median TOT, success %, mean SEQ, and the SUS score
   per the scoring guide in `sus_questionnaire.md`.

The backend already exposes timing signals that corroborate self-reported
efficiency: `/api/health/detailed` (latency/uptime) and the
`assessed_at` timestamps on assessments.

---

## 4. Reporting template

| Participant | Role | Tasks Passed | Median TOT (s) | Errors | SEQ (avg) | SUS |
| --- | --- | --- | --- | --- | --- | --- |
| P1 | | / 6 | | | | |
| P2 | | / 6 | | | | |
| **Aggregate** | | **% pass** | **median** | **mean** | **mean** | **mean** |

**Acceptance gate:** Aggregate SUS ≥ 70 **and** task success ≥ 90% **and**
mean explainability-trust ≥ 4/5.

---

## 5. Continuous usability signals (post-deployment)

Beyond moderated testing, these production signals act as ongoing usability
proxies:

- **Override rate** (`/api/v1/monitoring/performance`) — a sustained spike
  may indicate the UI is surfacing recommendations unclearly.
- **Time-to-decision** — derived from `assessed_at` vs. resolution time.
- **Repeat-correction rate** — frequency of clinicians re-opening
  assessments, indicating confusion.

---

*ISO 9241-11:2018 Ergonomics of human-system interaction. Brooke, J. (1996).
SUS: A Quick and Dirty Usability Scale. Sauro, J. & Dumas, J. (2009).
Single Ease Question (SEQ).*
