# TriageAI — Figma Wireframe Specification

**Project:** TriageAI Clinical Decision Support System  
**Author:** M.S.M.Sajidh (CL/BSCSD/34/01)  
**Tool:** Figma (recommended)  
**Grid:** 8px baseline, 12-column (desktop), 4-column (mobile)  
**Palette:** Primary `#0d47a1`, Secondary `#00838f`, Background `#f0f2f5`, Surface `#ffffff`

---

## Navigation Flow

```
[Login] ──→ [Dashboard]
              │
              ├──→ [New Assessment / Intake] ──→ [Triage Result] ──→ [Patient Detail]
              ├──→ [Patient Queue]
              ├──→ [Admin Panel]
              │         ├──→ [Audit Log]
              │         ├──→ [User Management]
              │         ├──→ [Analytics]
              │         └──→ [Patient History]
              ├──→ [Clinician Profile]
              ├──→ [Shift Handover]
              └──→ [System Settings] (admin only)
```

---

## 1. Login Page

### Desktop (1440×900)
**Layout:** Split-panel, 50/50
- **Left panel** (bg: `#0d47a1` gradient)
  - Centered content, max-width 480px
  - Logo: 48×48 icon + "TriageAI" title (32px, weight 800, white)
  - Subtitle: "Clinical Decision Support" (14px, white 65%)
  - Feature bullets with icons:
    - "AI-Powered Triage" — brain icon
    - "Explainable SHAP Results" — chart icon
    - "Immutable Audit Log" — lock icon
  - Footer: "© 2025 Cardiff Met"

- **Right panel** (bg: `#f0f2f5`)
  - Centered card, width 400px, padding 40px
  - Card: white surface, radius 16, shadow `0 4px 12px rgba(0,0,0,0.04)`
  - **Fields:**
    - "Username" — outlined input, height 48px
    - "Password" — outlined input with show/hide toggle icon
  - **Actions:**
    - Primary button: "Sign In" — full width, height 48px, primary color
    - Text link: "Forgot password?" — below button, 14px, secondary color
  - **Error state:** Red alert bar above button, shake animation on card

### Mobile (375×812)
- Full-screen gradient background
- Floating card with 16px margin
- Stacked layout, same elements

---

## 2. Dashboard Page

### Desktop (1440×900)
**Layout:** Top navbar (56px) + advisory banner (32px) + content grid
**Content:**
- **Header row**
  - Greeting: "Good evening, Dr. Kemal" (24px, weight 700)
  - Date/time badge (14px, secondary)

- **Quick Actions** (4 cards in a row, gap 16px)
  - Each card: 1fr width, padding 20px, white surface
  - Icon circle (48px, gradient bg) + label (16px, weight 600) + description (14px, secondary)
  - Cards: "New Assessment", "Patient Queue", "Shift Handover", "System Settings"

- **Statistics row** (admin only)
  - 4 stat cards in a row
  - Each: large number (32px, weight 700) + label (14px, secondary) + trend chip
  - Stats: Total Assessments, Critical (ESI-1), Overrides, Queue Length
  - Critical count: red text + pulse-critical animation badge

- **System Status card** (bottom)
  - Model version, contract hash, last training date
  - Green/yellow status indicator dot

---

## 3. Patient Intake (New Assessment)

### Desktop (1440×900)
**Layout:** Centered single column, max-width 800px
**Stepper:** Horizontal 3-step (Patient Info → Vitals → Review)
- Active step: primary color circle + label
- Completed: checkmark icon + muted label
- Future: grey circle + muted label

**Step 1 — Patient Info**
- Section header with icon + "Patient Information"
- Two-column grid:
  - Age (number input) | Sex (dropdown: Male/Female/Other)
  - Chief Complaint (autocomplete with 50 ICD-10 codes)
  - Pain Score (0–10 slider with color gradient: green→red)
- Auto-save indicator: "Draft saved" text bottom-right, 12px grey

**Step 2 — Vitals**
- Section header: "Vital Signs"
- Three-column grid (responsive: 2-col tablet, 1-col mobile):
  - Heart Rate (bpm)
  - Systolic BP (mmHg)
  - Diastolic BP (mmHg)
  - Respiratory Rate (/min)
  - SpO2 (%)
  - Temperature (°C)
  - GCS (3–15)
- Each field: outlined input + helper text with normal range
- Invalid fields: red border + helper text turns red

**Step 3 — Review & Submit**
- Summary card listing all entered values
- "Ctrl+Enter to submit" hint text
- Primary button: "Run AI Triage Assessment"
- Loading state: CircularProgress + "Analysing..."

---

## 4. Triage Result

### Desktop (1440×900)
**Layout:** Two-column, 40/60 split, gap 24px

**Left column — AI Recommendation**
- Large ESI badge (120×120 circle)
  - ESI-1: `#c62828` with pulse-critical animation
  - ESI-2: `#ef6c00` with pulse-emergent animation
  - ESI-3/4/5: appropriate colors, no pulse
- ESI level text (48px, weight 800, centered)
- Confidence score bar (0–100%, gradient fill)
- Timestamp + "TriageAI Recommendation" label

**Right column — Details**
- **SHAP Explanation panel**
  - Card with "Top Contributing Factors" header
  - Bar chart of top 3 features (horizontal bars, color by impact direction)
  - Feature names + impact values
- **Action buttons** (stacked, full width)
  - Primary: "Confirm Recommendation"
  - Secondary: "Override" — opens reason dialog
- **Print button** (top-right, icon button)

**Override Dialog**
- Modal, width 400px, centered
- "Select Override Reason" header
- Radio group: 7 coded reasons
- Optional notes textarea
- "Submit Override" primary button

---

## 5. Patient Queue

### Desktop (1440×900)
**Layout:** Full-width table card

**Toolbar**
- Title: "Active Patient Queue" (20px, weight 700)
- Refresh button (icon)
- Sort dropdown: "Sort by: Priority | Arrival Time | Wait Time"
- Filter chips: "All", "ESI-1", "ESI-2", "ESI-3", "ESI-4", "ESI-5"

**Table**
- Headers: ID | Name | ESI | Complaint | Wait Time | Status | Actions
- Row styling:
  - Left border 4px colored by ESI
  - ESI-1/2 rows: light red/pink background tint
- Wait time column:
  - <5 min: green text
  - 5–30 min: orange text
  - >30 min: red text
- Actions: "View" icon button

---

## 6. Admin Panel

### Desktop (1440×900)
**Layout:** Tabs below header

**Tabs:** Audit Log | User Management | Analytics | Patient History

**Audit Log Tab**
- Full-width table: Timestamp | User | Action | Entity | Details
- Pagination controls bottom
- Filter by user dropdown

**User Management Tab**
- "Create User" primary button top-right
- User table: Username | Role | Status | Created | Actions
- Actions per row: Edit, Reset Password, Toggle Active, Delete
- All actions trigger confirmation dialogs

**Analytics Tab**
- **Charts row** (2 columns)
  - BarChart: ESI Distribution (5 bars, color-coded)
  - PieChart: Override Reasons (7 segments)
- **Line chart** (full width)
  - Daily Assessment Volume (last 14 days)
- **Table** (bottom)
  - Clinician Performance: Name | Assessments | Overrides | Accuracy

**Patient History Tab**
- Search bar: "Search by ID or Chief Complaint"
- Results table with encrypted complaint display

---

## 7. Clinician Profile

### Desktop (1440×900)
**Layout:** Centered card, max-width 700px

**User Info Section**
- Avatar (64px, gradient bg) + Username + Role badge
- "Member since" date

**Stats Cards** (3 in a row)
- Total Assessments | Overrides | Today's Count
- Each: number + label, white card, padding 16px

**Recent Activity**
- Table: Time | Patient ID | ESI | Action (Confirmed/Overridden)
- Max 10 rows, scrollable

**Change Password**
- Card with 3 fields: Current, New, Confirm
- Validation: min 8 chars, 1 uppercase, 1 number
- "Update Password" button

---

## 8. Shift Handover

### Desktop (1440×900)
**Layout:** Centered, max-width 900px

**Summary Cards** (4 in a row)
- Total Assessments Today | ESI-1/2 Count | Override Rate | Avg Wait Time

**Priority Distribution**
- Horizontal bar chart (5 segments, ESI colors)
- Percentage labels on each segment

**Recent Assessments Table**
- Same columns as Patient Queue
- Filter: "Today only" toggle

---

## 9. System Settings

### Desktop (1440×900)
**Layout:** Centered card, max-width 600px

**Form Fields**
- Session Timeout (minutes): number input, default 15
- Login Rate Limit (attempts): number input, default 5
- Default Locale: English (EN)
- Auto-save Draft: toggle switch
- Print Header: text input

**Footer**
- "Save Changes" primary button
- "Reset to Defaults" text button

---

## 10. Not Found (404)

**Layout:** Centered, full viewport
- Large "404" (96px, weight 800, primary color)
- "Page not found" (24px)
- "Return to Dashboard" primary button
- Subtle fade-slide-up animation on load

---

## Component Library (Reusable)

| Component | Spec |
|-----------|------|
| Primary Button | Height 48px, radius 10px, bg `#0d47a1`, white text, weight 600, shadow `0 2px 8px rgba(13,71,161,0.25)` |
| Secondary Button | Same height, transparent bg, primary border |
| Text Field | Height 48px, radius 10px, outlined variant |
| Card | Radius 16px, shadow `0 1px 3px rgba(0,0,0,0.08), 0 4px 12px rgba(0,0,0,0.04)`, border `1px solid rgba(0,0,0,0.06)` |
| Table Header | 14px, weight 700, uppercase, letter-spacing 0.5px, color `#555770` |
| ESI Badge | 28px height, radius 8px, color-coded bg, white text, weight 700 |
| Toast Snackbar | Radius 12px, auto-hide 4s, top-right position |

---

## Responsive Breakpoints

| Breakpoint | Width | Layout Changes |
|------------|-------|----------------|
| Desktop | ≥1280px | Full layout as described |
| Tablet | 768–1279px | 2-column grids → single column, sidebar collapses |
| Mobile | <768px | Single column, floating action buttons, hamburger nav |

---

*This document serves as the design specification for Figma wireframe creation.*
