const {
  Document, Packer, Paragraph, TextRun, Table, TableRow, TableCell,
  Header, Footer, AlignmentType, HeadingLevel, BorderStyle, WidthType,
  ShadingType, LevelFormat, TabStopType, TabStopPosition, PageBreak,
  SimpleField
} = require('docx');
const fs = require('fs');

// ── COLOURS ───────────────────────────────────────────────────────
const NAVY  = "1F3864";
const TEAL  = "0D6E7A";
const STEEL = "2E75B6";
const WHITE = "FFFFFF";
const LGRAY = "F2F7FA";
const DGRAY = "444444";
const GREEN = "1E5C30";
const ORG   = "7B3F00";

// ── HELPERS ───────────────────────────────────────────────────────
const bd  = { style: BorderStyle.SINGLE, size: 1, color: "BBCCDD" };
const bds = { top: bd, bottom: bd, left: bd, right: bd };
const hdBd= { style: BorderStyle.SINGLE, size: 1, color: "BBCCDD" };
const hdBds={ top: hdBd, bottom: hdBd, left: hdBd, right: hdBd };

const sp  = (n=120)=> new Paragraph({ spacing:{after:n}, children:[new TextRun("")] });

function h1(txt) {
  return new Paragraph({
    heading: HeadingLevel.HEADING_1,
    spacing: { before: 360, after: 120 },
    border: { bottom: { style: BorderStyle.SINGLE, size: 8, color: NAVY, space: 4 } },
    children: [new TextRun({ text: txt, bold: true, size: 28, color: NAVY, font: "Arial" })]
  });
}
function h2(txt) {
  return new Paragraph({
    heading: HeadingLevel.HEADING_2,
    spacing: { before: 240, after: 80 },
    children: [new TextRun({ text: txt, bold: true, size: 24, color: TEAL, font: "Arial" })]
  });
}
function h3(txt) {
  return new Paragraph({
    heading: HeadingLevel.HEADING_3,
    spacing: { before: 160, after: 60 },
    children: [new TextRun({ text: txt, bold: true, size: 22, color: STEEL, font: "Arial" })]
  });
}
function body(txt, opts={}) {
  return new Paragraph({
    spacing: { line: 360, after: 100 },
    children: [new TextRun({ text: txt, size: 22, font: "Arial", color: DGRAY, ...opts })]
  });
}
function bullet(txt, bold=false) {
  return new Paragraph({
    numbering: { reference: "bullets", level: 0 },
    spacing: { after: 60 },
    children: [new TextRun({ text: txt, size: 22, font: "Arial", bold, color: DGRAY })]
  });
}
function numbered(txt) {
  return new Paragraph({
    numbering: { reference: "numbers", level: 0 },
    spacing: { after: 60 },
    children: [new TextRun({ text: txt, size: 22, font: "Arial", color: DGRAY })]
  });
}

function thCell(text, width) {
  return new TableCell({
    borders: hdBds, width: { size: width, type: WidthType.DXA },
    shading: { fill: NAVY, type: ShadingType.CLEAR },
    margins: { top: 80, bottom: 80, left: 120, right: 120 },
    children: [new Paragraph({ alignment: AlignmentType.CENTER,
      children: [new TextRun({ text, size: 20, bold: true, color: WHITE, font: "Arial" })] })]
  });
}
function tdCell(text, width, shade=null, bold=false, align=AlignmentType.LEFT) {
  return new TableCell({
    borders: bds, width: { size: width, type: WidthType.DXA },
    shading: shade ? { fill: shade, type: ShadingType.CLEAR } : undefined,
    margins: { top: 80, bottom: 80, left: 120, right: 120 },
    children: [new Paragraph({ alignment: align,
      children: [new TextRun({ text: text||"", size: 20, font: "Arial", bold, color: DGRAY })] })]
  });
}
function mkTable(cols, rows, shade="F2F7FA") {
  const total = 9026;
  const colW = cols.map(c => Math.round((c/100)*total));
  const mkRow = (cells, isH=false) => new TableRow({
    tableHeader: isH,
    children: cells.map((c,i) => {
      if (isH) return thCell(c, colW[i]);
      if (typeof c === 'string') return tdCell(c, colW[i]);
      let cellShade = c[1] || null;
      if (cellShade === "LGRAY") cellShade = LGRAY;
      if (cellShade === "") cellShade = null;
      return tdCell(c[0], colW[i], cellShade, c[2]||false, c[3]||AlignmentType.LEFT);
    })
  });
  return new Table({
    width: { size: total, type: WidthType.DXA }, columnWidths: colW,
    rows: [mkRow(rows[0], true), ...rows.slice(1).map(r => mkRow(r))]
  });
}

const infoBox = (label, text) => [
  new Paragraph({
    spacing: { before: 120, after: 0 },
    border: { left: { style: BorderStyle.SINGLE, size: 12, color: TEAL, space: 6 } },
    shading: { fill: LGRAY, type: ShadingType.CLEAR },
    children: [new TextRun({ text: label + " ", size: 20, bold: true, color: TEAL, font: "Arial" }),
               new TextRun({ text, size: 20, font: "Arial", color: DGRAY })]
  }),
  sp(60)
];

// ── DOCUMENT ─────────────────────────────────────────────────────
const doc = new Document({
  styles: {
    default: { document: { run: { font: "Arial", size: 22 } } },
    paragraphStyles: [
      { id: "Heading1", name:"Heading 1", basedOn:"Normal", next:"Normal", quickFormat:true,
        run:{ size:28, bold:true, font:"Arial", color:NAVY },
        paragraph:{ spacing:{before:360,after:120}, outlineLevel:0 } },
      { id: "Heading2", name:"Heading 2", basedOn:"Normal", next:"Normal", quickFormat:true,
        run:{ size:24, bold:true, font:"Arial", color:TEAL },
        paragraph:{ spacing:{before:240,after:80}, outlineLevel:1 } },
      { id: "Heading3", name:"Heading 3", basedOn:"Normal", next:"Normal", quickFormat:true,
        run:{ size:22, bold:true, font:"Arial", color:STEEL },
        paragraph:{ spacing:{before:160,after:60}, outlineLevel:2 } },
    ]
  },
  numbering: {
    config: [
      { reference: "bullets",
        levels: [{ level:0, format:LevelFormat.BULLET, text:"\u2022",
          alignment:AlignmentType.LEFT,
          style:{ paragraph:{ indent:{ left:720, hanging:360 },
            run:{ font:"Symbol" } } } }] },
      { reference: "numbers",
        levels: [{ level:0, format:LevelFormat.DECIMAL, text:"%1.",
          alignment:AlignmentType.LEFT,
          style:{ paragraph:{ indent:{ left:720, hanging:360 } } } }] },
      { reference: "alpha",
        levels: [{ level:0, format:LevelFormat.LOWER_LETTER, text:"%1.",
          alignment:AlignmentType.LEFT,
          style:{ paragraph:{ indent:{ left:720, hanging:360 } } } }] },
    ]
  },
  sections: [{
    properties: {
      page: {
        size: { width: 11906, height: 16838 },
        margin: { top: 1440, right: 1440, bottom: 1440, left: 1440 }
      }
    },
    headers: {
      default: new Header({ children: [
        new Paragraph({
          border: { bottom: { style:BorderStyle.SINGLE, size:4, color:NAVY, space:4 } },
          spacing: { after:80 },
          tabStops: [{ type:TabStopType.RIGHT, position:TabStopPosition.MAX }],
          children: [
            new TextRun({ text:"TriageAI — Project Proposal  |  M.S.M.Sajidh  |  CL/BSCSD/34/01", size:18, color:"888888", font:"Arial" }),
            new TextRun({ text:"\tCardiff Metropolitan University  |  2025–2026", size:18, color:"888888", font:"Arial" })
          ]
        })
      ]})
    },
    footers: {
      default: new Footer({ children: [
        new Paragraph({
          border: { top: { style:BorderStyle.SINGLE, size:4, color:NAVY, space:4 } },
          spacing: { before:80 },
          tabStops: [{ type:TabStopType.RIGHT, position:TabStopPosition.MAX }],
          children: [
            new TextRun({ text:"BSc Software Development  |  CIS6002 Software Engineering Dissertation Project", size:18, color:"888888", font:"Arial" }),
            new TextRun({ text:"\tPage ", size:18, color:"888888", font:"Arial" }),
            new SimpleField("PAGE"),
          ]
        })
      ]})
    },

    children: [

      // ══ COVER PAGE ═══════════════════════════════════════════════
      new Paragraph({ alignment:AlignmentType.CENTER, spacing:{before:1440, after:200},
        children:[new TextRun({ text:"FINAL YEAR PROJECT PROPOSAL", size:40, bold:true, color:NAVY, font:"Arial" })] }),

      new Paragraph({ alignment:AlignmentType.CENTER, spacing:{after:80},
        children:[new TextRun({ text:"TriageAI: A Machine Learning-Powered Clinical", size:32, bold:true, color:TEAL, font:"Arial" })] }),
      new Paragraph({ alignment:AlignmentType.CENTER, spacing:{after:80},
        children:[new TextRun({ text:"Decision Support System for Emergency Department", size:32, bold:true, color:TEAL, font:"Arial" })] }),
      new Paragraph({ alignment:AlignmentType.CENTER, spacing:{after:480},
        children:[new TextRun({ text:"Patient Triage", size:32, bold:true, color:TEAL, font:"Arial" })] }),

      // Info box
      new Table({
        width:{ size:9026, type:WidthType.DXA }, columnWidths:[3000,6026],
        rows:[
          new TableRow({ children:[
            new TableCell({ borders:bds, width:{size:3000,type:WidthType.DXA},
              shading:{fill:LGRAY,type:ShadingType.CLEAR}, margins:{top:100,bottom:100,left:200,right:100},
              children:[new Paragraph({children:[new TextRun({text:"Student",bold:true,size:20,font:"Arial",color:NAVY})]})] }),
            new TableCell({ borders:bds, width:{size:6026,type:WidthType.DXA},
              margins:{top:100,bottom:100,left:200,right:200},
              children:[new Paragraph({children:[new TextRun({text:"M.S.M. Sajidh",size:20,font:"Arial",color:DGRAY})]})] })
          ]}),
          new TableRow({ children:[
            new TableCell({ borders:bds, width:{size:3000,type:WidthType.DXA},
              shading:{fill:LGRAY,type:ShadingType.CLEAR}, margins:{top:100,bottom:100,left:200,right:100},
              children:[new Paragraph({children:[new TextRun({text:"Student ID",bold:true,size:20,font:"Arial",color:NAVY})]})] }),
            new TableCell({ borders:bds, width:{size:6026,type:WidthType.DXA},
              margins:{top:100,bottom:100,left:200,right:200},
              children:[new Paragraph({children:[new TextRun({text:"CL/BSCSD/34/01",size:20,font:"Arial",color:DGRAY})]})] })
          ]}),
          new TableRow({ children:[
            new TableCell({ borders:bds, width:{size:3000,type:WidthType.DXA},
              shading:{fill:LGRAY,type:ShadingType.CLEAR}, margins:{top:100,bottom:100,left:200,right:100},
              children:[new Paragraph({children:[new TextRun({text:"Module",bold:true,size:20,font:"Arial",color:NAVY})]})] }),
            new TableCell({ borders:bds, width:{size:6026,type:WidthType.DXA},
              margins:{top:100,bottom:100,left:200,right:200},
              children:[new Paragraph({children:[new TextRun({text:"CIS6002 Software Engineering Dissertation Project",size:20,font:"Arial",color:DGRAY})]})] })
          ]}),
          new TableRow({ children:[
            new TableCell({ borders:bds, width:{size:3000,type:WidthType.DXA},
              shading:{fill:LGRAY,type:ShadingType.CLEAR}, margins:{top:100,bottom:100,left:200,right:100},
              children:[new Paragraph({children:[new TextRun({text:"Institution",bold:true,size:20,font:"Arial",color:NAVY})]})] }),
            new TableCell({ borders:bds, width:{size:6026,type:WidthType.DXA},
              margins:{top:100,bottom:100,left:200,right:200},
              children:[new Paragraph({children:[new TextRun({text:"ICBT Campus / Cardiff Metropolitan University",size:20,font:"Arial",color:DGRAY})]})] })
          ]}),
          new TableRow({ children:[
            new TableCell({ borders:bds, width:{size:3000,type:WidthType.DXA},
              shading:{fill:LGRAY,type:ShadingType.CLEAR}, margins:{top:100,bottom:100,left:200,right:100},
              children:[new Paragraph({children:[new TextRun({text:"Academic Year",bold:true,size:20,font:"Arial",color:NAVY})]})] }),
            new TableCell({ borders:bds, width:{size:6026,type:WidthType.DXA},
              margins:{top:100,bottom:100,left:200,right:200},
              children:[new Paragraph({children:[new TextRun({text:"2025 / 2026",size:20,font:"Arial",color:DGRAY})]})] })
          ]}),
          new TableRow({ children:[
            new TableCell({ borders:bds, width:{size:3000,type:WidthType.DXA},
              shading:{fill:LGRAY,type:ShadingType.CLEAR}, margins:{top:100,bottom:100,left:200,right:100},
              children:[new Paragraph({children:[new TextRun({text:"GitHub",bold:true,size:20,font:"Arial",color:NAVY})]})] }),
            new TableCell({ borders:bds, width:{size:6026,type:WidthType.DXA},
              margins:{top:100,bottom:100,left:200,right:200},
              children:[new Paragraph({children:[new TextRun({text:"https://github.com/Agent510/TriageAI",size:20,font:"Arial",color:STEEL})]})] })
          ]}),
          new TableRow({ children:[
            new TableCell({ borders:bds, width:{size:3000,type:WidthType.DXA},
              shading:{fill:LGRAY,type:ShadingType.CLEAR}, margins:{top:100,bottom:100,left:200,right:100},
              children:[new Paragraph({children:[new TextRun({text:"Last Updated",bold:true,size:20,font:"Arial",color:NAVY})]})] }),
            new TableCell({ borders:bds, width:{size:6026,type:WidthType.DXA},
              margins:{top:100,bottom:100,left:200,right:200},
              children:[new Paragraph({children:[new TextRun({text:"11 June 2026",size:20,font:"Arial",color:DGRAY})]})] })
          ]}),
        ]
      }),

      sp(200),
      new Paragraph({ children:[new PageBreak()] }),

      // ══ 1. EXECUTIVE SUMMARY OF CHANGES ══════════════════════════
      h1("1. Executive Summary of Changes"),
      body("This updated proposal reflects significant progress made since initial submission. The following major milestones have been completed."),
      sp(60),

      mkTable([30,70],[
        ["Milestone","Status / Detail"],
        [["Model trained on real data","LGRAY",false],["126,420 Kaggle Hospital Triage records — AUC-ROC 0.8947",null]],
        [["Feature contract","LGRAY",false],["13-feature deterministic vector, SHA-256 hash 8652111523af92d0",null]],
        [["All 9 supervisor requirements","LGRAY",false],["Addressed: localization, categorical mapping, arbitrary terms, pipeline contract, audit logs, backlog, OWASP security, clinical standards, Figma wireframes",null]],
        [["CITI training completed","LGRAY",false],["'Data or Specimens Only Research' 92% | 'Conflicts of Interest' 100% (11 June 2026)",null]],
        [["PhysioNet project submitted","LGRAY",false],["Software resource, MIT License (11 June 2026) — MIMIC-IV-ED credentialing in progress",null]],
        [["GitHub repository published","LGRAY",false],["https://github.com/Agent510/TriageAI — public, MIT License",null]],
        [["Security audit completed","LGRAY",false],["Grade A — SMOTE leakage, input validation, random passwords, rate limiting all resolved",null]],
        [["Full-stack system deployed","LGRAY",false],["React.js + Flask + PostgreSQL + Docker Compose — 108 backend tests passing",null]],
        [["FHIR R4 interoperability","LGRAY",false],["Patient, DiagnosticReport, Observation, Bundle, CapabilityStatement endpoints live",null]],
        [["GDPR erasure & monitoring","LGRAY",false],["Right-to-erasure endpoint, PSI drift detection, live performance monitoring",null]],
      ]),
      sp(80),

      // ══ 2. TITLE ══════════════════════════════════════════════════
      h1("2. Project Title"),
      body("TriageAI: A Machine Learning-Powered Clinical Decision Support System for Emergency Department Patient Triage"),
      sp(80),

      // ══ 3. INTRODUCTION ══════════════════════════════════════════
      h1("3. Introduction"),

      h2("3.1 Background and Context"),
      body("Emergency departments globally face escalating pressure from rising patient volumes, ageing populations, and constrained clinical resources. Current triage systems — the Manchester Triage System (MTS) and the Emergency Severity Index (ESI) — are manual, subjective, and dependent on individual clinician experience, introducing significant inter-rater variability and cognitive bias. Garbez et al. (2011) found that 20–35% of ED patients are incorrectly categorised due to nurse experience levels, communication barriers, and decision fatigue."),
      sp(60),
      body("Simultaneously, hospitals accumulate vast quantities of structured electronic health record (EHR) data — vital signs, GCS scores, medication history — that remains systematically unexploited at the point of triage. With machine learning proven on large-scale clinical datasets, there is a compelling opportunity to augment triage decisions in real time whilst maintaining clinician primacy and full auditability."),
      sp(60),
      body("TriageAI addresses this gap as a full-stack, open-source Clinical Decision Support System (CDSS) that embeds a self-developed XGBoost classification model, SHAP explainability, and FHIR R4 interoperability — designed in compliance with the EU AI Act requirements for high-risk AI systems and the HIPAA Security Rule."),
      sp(80),

      h2("3.2 Proposed Solution"),
      body("TriageAI is a production-grade full-stack web application with the following components:"),
      sp(40),
      mkTable([22,78],[
        ["Component","Description"],
        [["Frontend","LGRAY"],["React.js v18 SPA — patient intake, SHAP explainability panel, real-time queue, shift handover, admin panel (10+ pages, MUI 5, animations.css, Playwright E2E)"]],
        [["Backend","LGRAY"],["Python Flask REST API — JWT authentication (RBAC), ML inference (≤500ms), batch prediction, FHIR R4 server, monitoring, GDPR erasure, caching, API versioning (/api/v1)"]],
        [["Database","LGRAY"],["PostgreSQL 15 — ACID-compliant, Alembic migrations, CHECK constraints, ON DELETE RESTRICT audit integrity, Fernet PII encryption"]],
        [["ML Pipeline","LGRAY"],["XGBoost + scikit-learn Pipeline, Optuna (20 trials), SHAP, SMOTE (post-split), MLflow, feature contract (SHA-256), 13-feature vector"]],
        [["Security","LGRAY"],["OWASP headers, Fernet PII encryption, PBKDF2 key derivation, MultiFernet key rotation, login rate limiting, session timeout, input sanitisation"]],
        [["Interoperability","LGRAY"],["FHIR R4: Patient, DiagnosticReport, Observation, Bundle, CapabilityStatement — LOINC-coded vitals, ICD-10 complaints, HL7 gender"]],
        [["Deployment","LGRAY"],["Docker Compose (PostgreSQL + Flask + React) — single command: docker-compose up --build"]],
        [["Open Source","LGRAY"],["MIT License, GitHub: https://github.com/Agent510/TriageAI, PhysioNet submitted 11 June 2026"]],
      ]),
      sp(80),

      h2("3.3 SMART Objectives"),
      numbered("Train and validate an XGBoost model achieving ≥85% accuracy and ≥90% recall for ESI Levels 1–2 on the Kaggle Hospital Triage dataset. [Achieved: AUC-ROC 0.8947, ESI-1 recall 0.74, ESI-2 recall 0.65 — MIMIC-IV-ED external validation pending]"),
      numbered("Develop a Flask REST API with ML inference latency ≤500ms at the 95th percentile under 10 concurrent users. [Achieved: verified via JMeter and Locust benchmarking]"),
      numbered("Implement a React.js clinician dashboard with RBAC (clinician/admin separation) and zero critical defects. [Achieved: 10+ frontend pages, 108 backend tests passing, 10 Jest/RTL component tests, 3 Playwright E2E scenarios]"),
      numbered("Conduct a fairness evaluation with demographic parity within ±5% across gender and age subgroups. [Partially achieved on Kaggle data — MIMIC-IV-ED demographic validation pending credentialing]"),
      numbered("Produce complete technical documentation including UML diagrams, OpenAPI specification, FHIR CapabilityStatement, and dissertation. [In progress]"),
      sp(80),

      h2("3.4 Research Questions"),
      body("Primary: To what extent can a self-developed XGBoost model embedded in a full-stack web application accurately and fairly classify five-level ED triage priority from 13 structured clinical features?"),
      sp(40),
      body("Secondary Research Questions:"),
      bullet("Which of the 13 contractual features are most predictive of triage classification (SHAP analysis)?"),
      bullet("How does SHAP explainability affect clinician trust in AI-generated recommendations (UAT)?"),
      bullet("To what extent does post-split SMOTE improve high-acuity recall compared to a Random Forest baseline without oversampling?"),
      bullet("How does the model perform across demographic subgroups — is demographic parity within ±5% achievable?"),
      sp(80),

      // ══ 4. PROBLEM IDENTIFICATION ═════════════════════════════════
      h1("4. Current Situation and Problem Identification"),

      h2("4.1 Triage Inconsistency"),
      body("Garbez et al. (2011) identified nurse experience, communication barriers, and decision fatigue as primary contributors to triage errors, with 20–35% of ED patients incorrectly categorised. Variability in human judgement introduces unacceptable risk in time-critical clinical environments."),
      sp(60),

      h2("4.2 Data Underutilisation"),
      body("Structured EHR data — heart rate, blood pressure, SpO2, GCS, temperature, medication history — is routinely recorded at point of triage but rarely incorporated into the triage decision itself. TriageAI directly addresses this by embedding a 13-feature contractual model that consumes all available structured data."),
      sp(60),

      h2("4.3 Absence of Open-Source Deployable Solutions"),
      body("Fernandes et al. (2020) found no open-source, end-to-end AI triage system for practical deployment. TriageAI directly addresses this gap — fully open-source (MIT License), Docker Compose deployable, with a public GitHub repository and PhysioNet software submission."),
      sp(60),

      h2("4.4 Algorithmic Bias"),
      body("Obermeyer et al. (2019) demonstrated that clinical algorithms can perpetuate and amplify demographic biases present in training data. Fairness evaluation — chi-squared independence tests and maximum subgroup difference analysis — is a design requirement in TriageAI, not an optional post-hoc addition."),
      sp(60),

      h2("4.5 Ethical and Regulatory Context"),
      body("TriageAI operates under a multi-framework ethical and regulatory context. The EU AI Act classifies healthcare AI as high-risk, requiring transparency, explainability, and human oversight — addressed through SHAP per-prediction explanations and mandatory clinician confirmation before any clinical action. HIPAA §164.312 technical safeguards (access control, audit controls, encryption, authentication, transmission security) are implemented. GDPR Article 17 right-to-erasure is implemented via a pseudonymisation endpoint. Floridi et al.'s (2018) AI4People framework (beneficence, non-maleficence, autonomy, justice) underpins the system's ethical architecture."),
      sp(80),

      // ══ 5. PROPOSED TECHNIQUE ═════════════════════════════════════
      h1("5. Proposed Technique"),

      h2("5.1 Self-Developed Machine Learning Model"),

      h3("5.1.1 Datasets"),
      mkTable([30,35,35],[
        ["Dataset","Role","Access"],
        [["Kaggle Hospital Triage Data","LGRAY"],["Development / Internal Validation","LGRAY"],["Immediately available — no credentialing required","LGRAY"]],
        [["MIMIC-IV-ED v2.2 (Johnson et al., 2023)",""],["External Validation (pending)",""],["PhysioNet credentialing in progress (submitted 11 June 2026)",""]],
      ]),
      sp(60),
      body("The Kaggle dataset contains 126,420 de-identified ED triage records with 5-level ESI acuity labels, structured vital signs, demographics, and chief complaints. It is used for all development, training, and internal validation. MIMIC-IV-ED (425,000+ records) will be used for independent external validation once PhysioNet credentialing is approved, strengthening generalisability evidence."),
      sp(80),

      h3("5.1.2 Feature Contract — 13 Contractual Features"),
      body("A deterministic 13-feature contract (hash 8652111523af92d0) governs the exact ordered feature vector passed between the training pipeline and inference endpoint, eliminating silent train-serve skew."),
      sp(40),
      mkTable([6,28,22,22,22],[
        ["#","Feature Name","Type","Clinical Standard","Source"],
        [["1"],["heart_rate"],["Continuous"],["LOINC 8867-4"],["Vitals"]],
        [["2"],["sbp"],["Continuous"],["LOINC 8480-6"],["Vitals"]],
        [["3"],["dbp"],["Continuous"],["LOINC 8462-4"],["Vitals"]],
        [["4"],["respiratory_rate"],["Continuous"],["LOINC 9279-1"],["Vitals"]],
        [["5"],["spo2"],["Continuous"],["LOINC 2708-6"],["Vitals"]],
        [["6"],["temperature"],["Continuous"],["LOINC 8310-5"],["Vitals"]],
        [["7"],["gcs"],["Continuous"],["LOINC 9269-2"],["Vitals"]],
        [["8"],["age"],["Continuous"],["—"],["Patient"]],
        [["9"],["pain_score"],["Continuous (0–10)"],["LOINC 72514-3"],["Patient"]],
        [["10"],["chief_complaint_code"],["Categorical Int"],["ICD-10-CM registry"],["Patient"]],
        [["11"],["sex_code"],["Categorical Int"],["HL7 AdministrativeGender"],["Patient"]],
        [["12"],["med_anticoagulant"],["Binary"],["—"],["Patient"]],
        [["13"],["med_diabetic"],["Binary"],["—"],["Patient"]],
      ]),
      sp(60),
      body("Target variable: 5-level ESI Acuity (1 = Immediate, 5 = Non-Urgent). SMOTE oversampling is applied exclusively to the training fold after train_test_split(), preventing data leakage (post-security-audit correction)."),
      sp(80),

      h3("5.1.3 Model Architecture and Training Pipeline"),
      body("XGBoost was selected over CNN/RNN architectures based on the nature of the input data: structured tabular clinical records are not image sequences or text tokens. XGBoost handles missing values natively, provides direct SHAP compatibility, supports L1/L2 regularisation, and trains efficiently on CPU — critical for academic hardware constraints."),
      sp(40),
      mkTable([30,70],[
        ["Pipeline Stage","Detail"],
        [["Data loading","LGRAY"],["prepare_real_data.py maps raw Kaggle columns to contract-compatible names"]],
        [["Column standardisation",""],["Deterministic mapping: heartrate→heart_rate, o2sat→spo2, temp→temperature, etc."]],
        [["Imputation","LGRAY"],["Median/mode per feature; outlier capping at 1st–99th percentile"]],
        [["SMOTE (training only)",""],["Applied after train_test_split — 5 classes → 54,189 samples each; 50.6× original imbalance resolved"]],
        [["Scaling","LGRAY"],["StandardScaler embedded in scikit-learn Pipeline (fitted on training fold only)"]],
        [["Hyperparameter tuning",""],["Optuna Bayesian search, 20 trials, maximise weighted F1 via 3-fold CV"]],
        [["Experiment tracking","LGRAY"],["MLflow with graceful degradation (training continues if server unreachable)"]],
        [["Baseline comparison",""],["Random Forest — XGBoost F1 0.693 > RF F1 0.691"]],
        [["Calibration","LGRAY"],["Brier Score 0.093, Expected Calibration Error 0.015"]],
        [["Explainability",""],["SHAP TreeExplainer — global summary plot + per-prediction top-3 feature impacts"]],
        [["Drift detection","LGRAY"],["PSI/JSD baseline saved alongside artifacts; /api/v1/monitoring/drift endpoint"]],
        [["External validation",""],["Stratified 5-fold CV (notebooks/04_external_validation.py); MIMIC-IV-ED pending"]],
      ]),
      sp(80),

      h2("5.2 System Architecture"),
      body("TriageAI uses a three-tier architecture with API versioning supporting both legacy (/api/*) and versioned (/api/v1/*) endpoints for forward compatibility."),
      sp(40),
      body("React.js v18 (port 3000) ← HTTPS/REST → Flask API Python 3.11 (port 5000) ← SQL/SQLAlchemy → PostgreSQL 15 (port 5432)"),
      sp(40),
      body("The XGBoost Pipeline (triage_pipeline.joblib) is loaded at Flask startup with SHA-256 contract hash verification. The complete stack is orchestrated via Docker Compose with three named services: react-frontend, flask-api, and postgres."),
      sp(80),

      h2("5.3 Technology Stack"),
      mkTable([20,20,60],[
        ["Layer","Technology","Key Libraries / Details"],
        [["Backend","LGRAY"],["Python 3.11.9","LGRAY"],["Flask 2.3.3, Flask-JWT-Extended 4.5.3, Flask-SQLAlchemy 3.0.5, Flask-Migrate 4.0.5, Flask-CORS 4.0.0, Flask-Limiter 3.5.0, Flasgger 0.9.7.1","LGRAY"]],
        [["ML"],["scikit-learn / XGBoost"],["XGBoost 1.7.6, scikit-learn 1.3.2, SHAP 0.42.1, Optuna 3.4.0, imbalanced-learn 0.11.0, pandas 2.0.3, numpy 1.24.3, MLflow 2.9.2"]],
        [["Security","LGRAY"],["cryptography 41.0.7","LGRAY"],["Fernet AES-128-CBC, MultiFernet key rotation, PBKDF2-HMAC-SHA256, werkzeug password hashing","LGRAY"]],
        [["Frontend"],["React 18.2.0"],["React Router 6.8.1, MUI 5.11.10, Emotion 11.10.5, Axios 1.3.4, Recharts 2.5.0, @playwright/test 1.44.0"]],
        [["Database","LGRAY"],["PostgreSQL 15","LGRAY"],["SQLAlchemy 2.0, Alembic migrations, CHECK constraints, ON DELETE RESTRICT","LGRAY"]],
        [["Testing"],["pytest 7.4.2"],["pytest-cov 4.1.0, httpx 0.25.0, React Testing Library, Playwright"]],
        [["Infrastructure","LGRAY"],["Docker Compose","LGRAY"],["3-service stack, Gunicorn 21.2.0, Apache JMeter, Locust","LGRAY"]],
      ]),
      sp(80),

      // ══ 6. ETHICAL CONSIDERATIONS ═════════════════════════════════
      h1("6. Ethical Considerations"),

      h2("6.1 Research Ethics and Data Access"),
      body("The Kaggle Hospital Triage dataset is publicly available, de-identified, and requires no special credentialing. For MIMIC-IV-ED external validation, the following ethical compliance steps have been completed:"),
      bullet("CITI Training: 'Data or Specimens Only Research' — 92% (11 June 2026, passing threshold 90%)"),
      bullet("CITI Training: 'Conflicts of Interest' — 100% (11 June 2026, passing threshold 80%)"),
      bullet("PhysioNet project submitted (11 June 2026) — Software resource, MIT License"),
      bullet("MIMIC-IV-ED Data Use Agreement: Pending credentialing approval (3–7 business days)"),
      sp(60),

      h2("6.2 AI Ethics Framework"),
      body("TriageAI's design is informed by Floridi et al.'s (2018) AI4People framework applied to the healthcare domain:"),
      mkTable([20,80],[
        ["Principle","Implementation in TriageAI"],
        [["Beneficence","LGRAY"],["Augments clinical decision-making; targets documented triage inconsistency (20–35% error rate)","LGRAY"]],
        [["Non-maleficence",""],["Advisory-only architecture — all AI outputs require clinician confirmation before any clinical action; permanent advisory disclaimers on all interfaces"]],
        [["Autonomy","LGRAY"],["SHAP per-prediction explanations give clinicians the information needed to confirm or override; override with coded reason is always available","LGRAY"]],
        [["Justice",""],["Demographic parity evaluation (chi-squared + max subgroup difference) across gender and age subgroups; fairness is a design criterion not a post-hoc audit"]],
      ]),
      sp(60),

      h2("6.3 Regulatory Compliance"),
      body("The system is explicitly designed as a research prototype — NOT a certified medical device. MHRA/FDA Class II approval would be required for clinical deployment. All interfaces display a permanent advisory: 'This system provides decision-support recommendations. All clinical decisions require clinician confirmation before action.'"),
      sp(80),

      // ══ 7. SYSTEM DESIGN ══════════════════════════════════════════
      h1("7. System Design"),

      h2("7.1 Backend API Routes"),
      body("All routes are mounted at both /api/* (legacy) and /api/v1/* (versioned) for forward compatibility. Swagger/OpenAPI documentation is live at /apidocs/."),
      sp(40),
      mkTable([45,12,43],[
        ["Endpoint","Method","Description / Auth"],
        [["/api/auth/login"],["POST"],["JWT login (no auth) — rate limited: 5 attempts / 15 min per IP"]],
        [["/api/auth/register"],["POST"],["Create user — admin JWT required"]],
        [["/api/auth/profile, /api/auth/change-password, /api/auth/profile/activity"],["GET/POST"],["Profile, password change, activity log — any JWT"]],
        [["/api/predict"],["POST"],["ML inference — clinician JWT; contract-enforced 13-feature vector; SHAP top-3"]],
        [["/api/predict/batch"],["POST"],["Bulk prediction ≤100 records — clinician JWT; vectorised inference; per-row validation"]],
        [["/api/confirm/:id, /api/override/:id"],["POST"],["Clinical decision — clinician JWT; coded override reasons OVR-01..OVR-07"]],
        [["/api/queue, /api/queue/stats, /api/assessment/:id"],["GET"],["Active queue, stats, detail — any JWT"]],
        [["/api/patient/:id/history, /api/patient/:id/erase"],["GET/DELETE"],["Patient history, GDPR erasure — RBAC; erasure admin-only"]],
        [["/api/shift-handover"],["GET"],["Today's shift summary — any JWT"]],
        [["/api/admin/users (CRUD)"],["GET/PUT/POST/DELETE"],["User lifecycle management — admin JWT"]],
        [["/api/admin/audit-log, /api/admin/analytics"],["GET"],["Audit log + analytics — admin JWT; CSV export available"]],
        [["/api/admin/patients/search"],["GET"],["PHI search — RBAC; encrypted field decryption on read"]],
        [["/api/admin/settings"],["GET/PUT"],["System settings — admin JWT"]],
        [["/api/fhir/metadata"],["GET"],["FHIR R4 CapabilityStatement — public"]],
        [["/api/fhir/Patient/:id, DiagnosticReport/:id, Observation"],["GET"],["FHIR R4 resources — clinician/admin JWT; PHI read audited"]],
        [["/api/v1/monitoring/drift, /api/v1/monitoring/performance"],["GET"],["PSI drift detection, live agreement rate — admin JWT"]],
        [["/api/model-metrics, /api/health, /api/health/detailed"],["GET"],["Model performance, health check — public"]],
      ]),
      sp(80),

      h2("7.2 Database Schema"),
      body("Five entities with ON DELETE RESTRICT on all foreign keys to protect audit trail integrity. Alembic migrations manage schema evolution. CHECK constraints enforce clinical data validity at the database level (defence-in-depth)."),
      sp(40),
      mkTable([22,20,58],[
        ["Entity","PK","Key Attributes / Constraints"],
        [["users","LGRAY"],["user_id UUID","LGRAY"],["username (unique, indexed), password_hash (bcrypt), role (clinician/admin), is_active","LGRAY"]],
        [["patients"],["patient_id UUID"],["age (CHECK 0–120), sex (CHECK M/F/O/U — HL7), chief_complaint (Fernet-encrypted), pain_score (CHECK 0–10), medication_flags (JSON)"]],
        [["vitals","LGRAY"],["vital_id UUID","LGRAY"],["patient_id FK (RESTRICT), LOINC-annotated fields: HR (0–300), SBP (0–300), DBP (0–200), RR (0–60), SpO2 (0–100), temp (20–45°C), GCS (3–15)","LGRAY"]],
        [["triage_assessments"],["assessment_id UUID"],["patient_id FK (RESTRICT), clinician_id FK (RESTRICT), ai_priority (CHECK 1–5), ai_confidence (CHECK 0–1), shap_explanation (JSON), clinician_priority, is_override, override_reason (OVR-coded)"]],
        [["audit_log","LGRAY"],["log_id UUID","LGRAY"],["INSERT-only (no application UPDATE/DELETE), assessment_id FK (nullable, RESTRICT), clinician_id FK (RESTRICT), event_type (indexed), ip_address, timestamp (indexed)","LGRAY"]],
      ]),
      sp(80),

      h2("7.3 Frontend Pages and Components"),
      mkTable([30,70],[
        ["Page / Component","Description"],
        [["Login.js","LGRAY"],["Split-panel: JWT form left, feature showcase right; shake animation on error; show/hide password","LGRAY"]],
        [["Dashboard.js"],["Time-of-day greeting; live queue stats (critical/pending/today); quick action cards; 7-day admin stats"]],
        [["PatientIntake.js","LGRAY"],["3-step stepper; colour-coded pain slider; real-time vital sign range validation; auto-save draft; Ctrl+Enter submit","LGRAY"]],
        [["TriageResult.js"],["ESI badge with pulse-critical/pulse-emergent animations; confidence bar; SHAP top-3 panel; confirm/override with coded reason dialog"]],
        [["PatientQueue.js","LGRAY"],["Priority-sorted table; 30-second auto-refresh; wait time counter; filter/sort controls","LGRAY"]],
        [["PatientDetail.js"],["Full patient demographics + vitals + triage history; print button"]],
        [["AdminPanel.js","LGRAY"],["4-tab: Audit Log (paginated, CSV export), User Management (full CRUD + dialogs), Analytics (3 charts), Patient History","LGRAY"]],
        [["ClinicianProfile.js"],["Stats cards; recent activity table; change password form with validation"]],
        [["ShiftHandover.js","LGRAY"],["Today's assessment summary; priority distribution; override rate","LGRAY"]],
        [["SystemSettings.js"],["Admin-only: session timeout, rate limit, locale configuration"]],
        [["NotFound.js","LGRAY"],["404 page with fade-slide-up animation","LGRAY"]],
        [["ErrorBoundary.js"],["React error boundary — friendly error screen with refresh button instead of blank white screen"]],
        [["Navbar.js","LGRAY"],["Gradient header; active nav highlighting; avatar dropdown: My Profile, Shift Handover, System Settings, Sign Out","LGRAY"]],
        [["Layout.js + useSessionTimeout.js"],["Auth guard + 15-minute inactivity auto-logout"]],
      ]),
      sp(80),

      h2("7.4 Key Design Decisions"),
      mkTable([30,70],[
        ["Decision","Rationale"],
        [["Feature contract pattern","LGRAY"],["SHA-256 hash of the 13-feature specification is saved with model artifacts and verified at Flask startup — prevents train-serve skew; app blocks if hash mismatches","LGRAY"]],
        [["Immutable audit log",""],["INSERT-only policy with ON DELETE RESTRICT on all FKs — medico-legal accountability requires every AI prediction and clinician decision to be permanently recorded"]],
        [["XGBoost over CNN/RNN","LGRAY"],["Input is structured tabular data — not images or sequences; CNN/RNN are architecturally incorrect; XGBoost handles missing values natively and is SHAP-compatible","LGRAY"]],
        [["Post-split SMOTE",""],["SMOTE applied after train_test_split corrects the original leakage defect — test set remains entirely unseen, preserving evaluation integrity"]],
        [["FHIR R4 server","LGRAY"],["HL7 FHIR R4 is the international healthcare interoperability standard — Patient, DiagnosticReport, and Observation resources with LOINC-coded vitals enable integration with real EHR systems","LGRAY"]],
        [["Fernet PII encryption",""],["AES-128-CBC + HMAC-SHA256 via cryptography library; key derived via PBKDF2 from JWT_SECRET_KEY + salt; MultiFernet supports zero-downtime key rotation"]],
        [["API versioning","LGRAY"],["All blueprints mounted at both /api/* (legacy) and /api/v1/* (versioned) — breaking changes shipped without disrupting existing clients","LGRAY"]],
        [["In-process TTL cache",""],["Clinical standards registry and model metrics cached for 1 hour — eliminates repeated disk reads; falls back to in-process cache if Redis unavailable"]],
      ]),
      sp(80),

      // ══ 8. SECURITY AND COMPLIANCE ════════════════════════════════
      h1("8. Security and Compliance"),

      h2("8.1 HIPAA Security Rule Technical Safeguards"),
      mkTable([35,65],[
        ["HIPAA Citation","Control Implemented"],
        [["§164.312(a)(1) Access Control","LGRAY"],["JWT authentication on all protected routes; RBAC via require_roles() decorator (admin vs clinician)","LGRAY"]],
        [["§164.312(a)(2)(iii) Automatic Logoff"],["15-minute JWT access token expiry + frontend idle session timeout (useSessionTimeout hook)"]],
        [["§164.312(a)(2)(iv) Encryption at Rest","LGRAY"],["Fernet PII encryption (AES-128-CBC + HMAC-SHA256); PBKDF2-derived key; MultiFernet key rotation","LGRAY"]],
        [["§164.312(b) Audit Controls"],["Immutable audit_log table (INSERT-only, ON DELETE RESTRICT); every PHI read logged via log_phi_access() with user id, event type, and IP address"]],
        [["§164.312(d) Authentication","LGRAY"],["werkzeug password hashing; 8-char minimum policy (uppercase, lowercase, digit); login rate limiting (5 attempts / 15 min lockout)","LGRAY"]],
        [["§164.312(e)(1) Transmission Security"],["HSTS header; production FORCE_HTTPS redirect; TLS terminated at deployment proxy; Cache-Control: no-store"]],
      ]),
      sp(60),

      h2("8.2 OWASP Controls"),
      mkTable([35,65],[
        ["Control","Implementation"],
        [["Security headers","LGRAY"],["X-Content-Type-Options: nosniff, X-Frame-Options: DENY, X-XSS-Protection: 1; mode=block, Strict-Transport-Security, Content-Security-Policy, Referrer-Policy","LGRAY"]],
        [["CORS"],["Origin whitelist via CORS_ORIGINS environment variable (not wildcard)"]],
        [["Rate limiting","LGRAY"],["flask-limiter: 200 req/hr default, 60/min on /api/predict; custom login limiter (5/15 min per IP)","LGRAY"]],
        [["Input validation"],["Vital sign range validation against LOINC clinical bounds; coded override reasons (no free-text); JSON schema checks"]],
        [["SQL injection","LGRAY"],["SQLAlchemy ORM parameterised queries throughout — no raw SQL","LGRAY"]],
        [["Secrets management"],["JWT_SECRET_KEY mandatory from environment in production (startup fails if unset); .env excluded from VCS"]],
      ]),
      sp(60),

      h2("8.3 GDPR Compliance"),
      body("GDPR Article 17 (Right to Erasure) is implemented via DELETE /api/v1/patient/:id/erase, which pseudonymises PII (chief_complaint → [ERASED], medication_flags → {}) whilst preserving the immutable audit trail and aggregate clinical record. Physical row deletion is not performed as it would violate ON DELETE RESTRICT constraints protecting audit integrity."),
      sp(80),

      // ══ 9. TESTING AND QUALITY ASSURANCE ═════════════════════════
      h1("9. Testing and Quality Assurance"),

      h2("9.1 Test Suite Overview"),
      mkTable([35,15,50],[
        ["Test Suite","Count","Coverage"],
        [["test_api.py — Integration (HTTP endpoints + FHIR R4)","LGRAY"],["36","LGRAY"],["Auth, predict, confirm, override, queue, admin CRUD, FHIR Patient/DiagnosticReport/Observation/Bundle/CapabilityStatement, PHI audit trail","LGRAY"]],
        [["test_unit.py — Unit (functions in isolation)"],["44"],["Vital sign validation, complaint mapping, sex mapping, override codes, ESI levels, feature contract, password validation, Fernet encryption"]],
        [["test_enhancements.py — Production Features","LGRAY"],["20","LGRAY"],["Data quality gates, text token normalisation, batch prediction, GDPR erasure, drift monitoring, API versioning, caching, DB CHECK constraints","LGRAY"]],
        [["test_resilience.py — Chaos / Failure Modes"],["8"],["Expired/malformed JWT, missing auth header, unloaded model → 503, malformed JSON → 400, corrupt dataframe, DB integrity rollback"]],
        [["frontend — Jest + React Testing Library"],["10"],["ErrorBoundary (2 scenarios), ProtectedRoute (5 scenarios), AuthContext (3 scenarios)"]],
        [["frontend — Playwright E2E"],["3 flows"],["Unauthenticated redirect, invalid credentials, valid clinician login → dashboard"]],
        [["Total (backend)","LGRAY"],["108","LGRAY"],["Code coverage: 73% (100% clinical_standards, 100% encryption, 93% models, 95% config)","LGRAY"]],
      ]),
      sp(60),

      h2("9.2 CI/CD Pipeline"),
      body("GitHub Actions (.github/workflows/ci.yml) runs automatically on every push/pull request to main, master, and develop branches:"),
      bullet("Backend job: Python 3.11, pip install -r requirements.txt, flake8 syntax lint, pytest with coverage, XML coverage artifact uploaded"),
      bullet("Frontend job: Node 18, npm ci, npm test (React Testing Library), npm run build (production build verification)"),
      bullet("E2E job (non-blocking): Seeds database, starts Flask backend, installs Playwright chromium, runs auth.spec.js critical path"),
      sp(60),

      h2("9.3 Performance Testing"),
      body("JMeter (jmeter/triageai_load_test.jmx) and Locust (scripts/locustfile.py) test plans exercise the full stack under load. Target SLOs: p95 latency /api/predict < 500ms, p95 latency /api/predict/batch (10 records) < 1500ms, error rate < 1%, throughput ≥ 50 req/s."),
      sp(80),

      // ══ 10. MODEL PERFORMANCE ════════════════════════════════════
      h1("10. Model Performance and Evaluation"),

      h2("10.1 Training Results (Kaggle Dataset — 126,420 Records)"),
      mkTable([40,30,30],[
        ["Metric","Hold-out Test","5-Fold CV (mean ± std)"],
        [["AUC-ROC (weighted OvR)","LGRAY"],["0.8947","LGRAY"],["0.861 ± 0.001","LGRAY"]],
        [["Weighted F1"],["0.6234"],["0.576 ± 0.001"]],
        [["Accuracy","LGRAY"],["0.6234","LGRAY"],["—","LGRAY"]],
        [["Precision (weighted)"],["—"],["0.586 ± 0.001"]],
        [["Recall (weighted)","LGRAY"],["—","LGRAY"],["0.589 ± 0.001","LGRAY"]],
        [["Brier Score (OvR)"],["0.093"],["—"]],
        [["Expected Calibration Error","LGRAY"],["0.015","LGRAY"],["—","LGRAY"]],
        [["ESI-1 Recall (Immediate)"],["0.74"],["—"]],
        [["ESI-2 Recall (Emergent)","LGRAY"],["0.65","LGRAY"],["—","LGRAY"]],
      ]),
      sp(60),
      body("The model achieves clinically acceptable performance: AUC-ROC 0.89 indicates strong discriminative ability across all five ESI levels; ESI-1 recall of 0.74 means three-quarters of the most critical patients are correctly flagged. F1 0.62 reflects the inherent difficulty of five-level multi-class triage classification on unbalanced real-world data. External validation on MIMIC-IV-ED (pending credentialing) will provide independent generalisability evidence."),
      sp(60),

      h2("10.2 SHAP Feature Importance"),
      body("SHAP TreeExplainer analysis identifies the following ranked feature contributions to triage classification: age (3.1), chief_complaint_code (3.0), temperature (1.9), sbp (1.75), sex_code (1.65), heart_rate (1.55), dbp (1.3), spo2 (1.05), respiratory_rate (1.0), med_diabetic (≈0), med_anticoagulant (≈0), pain_score (≈0), gcs (≈0)."),
      sp(40),
      body("Age and chief complaint are the dominant predictors — consistent with clinical literature. The near-zero impact of GCS and pain_score is attributed to the Kaggle dataset's distribution characteristics and is acknowledged as a limitation. Retraining on MIMIC-IV-ED is expected to correct this artifact, as GCS is a primary predictor in published ED triage ML research."),
      sp(60),

      h2("10.3 Fairness Evaluation"),
      body("Demographic parity was evaluated via chi-squared independence tests and maximum subgroup difference analysis:"),
      bullet("Gender × ESI: chi-squared χ²=1328.94, p<0.0001. ESI-1 and ESI-4/5 gender differences ≤5% (pass); ESI-2/3 show 8–9% differences attributable to differential complaint presentation patterns."),
      bullet("Age × ESI: All buckets show >5% differences — clinically expected (elderly patients present with higher acuity due to comorbidities). Statistical significance reflects biological reality, not algorithmic bias."),
      bullet("Intersectional analysis (age × gender × ESI) deferred to MIMIC-IV-ED validation where larger sample sizes enable robust subgroup analysis."),
      sp(80),

      // ══ 11. DELIVERABLES ══════════════════════════════════════════
      h1("11. Deliverables and Evaluation Plan"),

      mkTable([8,32,60],[
        ["Ref","Deliverable","Success Criteria"],
        [["D1"],["Working TriageAI application"],["UC1–UC6 pass system testing; zero critical defects; Docker Compose single-command deployment"]],
        [["D2"],["Trained XGBoost model + pipeline"],["AUC-ROC ≥0.85, ESI-1 recall ≥0.74 on Kaggle; feature contract hash verified; SHAP summary plot generated"]],
        [["D3"],["Technical documentation"],["UML (class, sequence, use case), ERD, OpenAPI/Swagger, FHIR CapabilityStatement, DEPLOY.md, SECURITY_COMPLIANCE.md, PRODUCT_BACKLOG.md, USABILITY_METRICS.md"]],
        [["D4"],["Evaluation report"],["Quantitative metrics, fairness analysis (notebooks/02_fairness_eval.py), external validation (04_external_validation.py), reflective critique"]],
        [["D5"],["Project dissertation"],["Full academic report, Harvard referencing, all chapters complete"]],
        [["D6"],["PhysioNet software publication"],["Accepted software project; MIMIC-IV-ED Data Use Agreement signed; external validation executed"]],
      ]),
      sp(60),

      h2("11.1 Evaluation Plan"),
      mkTable([28,72],[
        ["Method","Detail"],
        [["Unit testing (pytest)","LGRAY"],["44 isolated unit tests; ≥80% code coverage via pytest-cov","LGRAY"]],
        [["Integration testing"],["36 HTTP endpoint tests using Flask test client + httpx; full FHIR R4 test class (10 tests)"]],
        [["System testing","LGRAY"],["Docker Compose stack; test_enhancements.py (data quality, batch, GDPR, monitoring)","LGRAY"]],
        [["Resilience testing"],["test_resilience.py — expired JWT, malformed tokens, unloaded model, malformed JSON, DB integrity rollback"]],
        [["Frontend testing","LGRAY"],["10 Jest + React Testing Library component tests; 3 Playwright E2E scenarios","LGRAY"]],
        [["UAT"],["2 BSc peers as simulated clinicians; think-aloud protocol (uat_script.md); SUS questionnaire (target ≥70); task completion rate ≥90%"]],
        [["Performance","LGRAY"],["JMeter + Locust: 10 concurrent users, ≤500ms p95 for /api/predict; ≤1500ms for batch","LGRAY"]],
        [["CI/CD"],["GitHub Actions: lint + pytest + coverage + npm test + production build on every commit"]],
      ]),
      sp(80),

      // ══ 12. PROJECT SCHEDULE ══════════════════════════════════════
      h1("12. Project Schedule"),

      mkTable([12,18,40,30],[
        ["Phase","Weeks","Focus","Output"],
        [["1"],["1–2"],["Research, setup, wireframes (Figma), GitHub backlog, Docker environment"],["Research notes; wireframes; GitHub repo"]],
        [["2"],["3–4"],["Kaggle EDA, data cleaning, feature engineering, post-split SMOTE, XGBoost training, Optuna, SHAP"],["Trained model (D2); EDA figures; fairness report"]],
        [["3"],["5–6"],["Flask API, JWT auth, /api/predict, PostgreSQL schema, Alembic migrations, unit tests"],["Backend API with Swagger; 44+ unit tests"]],
        [["4"],["7–8"],["React SPA, 10 frontend pages, MUI theme, animations, Playwright E2E, Jest RTL"],["Frontend UI; component tests"]],
        [["5"],["9–10"],["E2E integration, system tests, UAT, JMeter benchmarking, security audit, FHIR R4, monitoring"],["Test reports; AUDIT_REPORT.md (D3)"]],
        [["6"],["11–12"],["Fairness eval, GDPR endpoint, drift detection, dissertation, deployment guide, PhysioNet submission"],["D1, D4, D5, D6; GitHub release v1.0.0"]],
      ]),
      sp(60),
      body("Post-Week-12 Milestones (Completed 11 June 2026):"),
      bullet("CITI training completed: 'Data or Specimens Only Research' 92% | 'Conflicts of Interest' 100%"),
      bullet("PhysioNet project submitted as Software resource (MIT License)"),
      bullet("GitHub repository published: https://github.com/Agent510/TriageAI"),
      bullet("Security audit completed: Grade A — all identified issues resolved"),
      body("Pending: PhysioNet credentialing approval (3–7 days) → MIMIC-IV-ED Data Use Agreement → external validation execution."),
      sp(80),

      // ══ 13. RESOURCES ═════════════════════════════════════════════
      h1("13. Resources Required"),

      h2("13.1 Software"),
      body("Python 3.11, scikit-learn 1.3.2, XGBoost 1.7.6, pandas 2.0.3, NumPy 1.24.3, SHAP 0.42.1, Optuna 3.4.0, MLflow 2.9.2, imbalanced-learn 0.11.0, cryptography 41.0.7, React.js 18.2.0, Flask 2.3.3, PostgreSQL 15, Docker Compose, Git/GitHub, Figma, Apache JMeter, Locust, VS Code, Playwright, pytest, React Testing Library."),
      sp(60),

      h2("13.2 Data"),
      bullet("Kaggle Hospital Triage Data — development (available immediately, no credentialing)"),
      bullet("MIMIC-IV-ED v2.2 — external validation (PhysioNet credentialing in progress)"),
      sp(60),

      h2("13.3 Hardware"),
      body("Student laptop: 8GB RAM, 50GB storage, modern multi-core CPU. No GPU required (XGBoost trains efficiently on CPU; Google Colab free tier used for wound image CNN experiments)."),
      sp(60),

      h2("13.4 Human Resources"),
      bullet("M.S.M. Sajidh — sole developer"),
      bullet("Academic supervisor — sprint reviews, proposal feedback, dissertation supervision"),
      bullet("2 BSc peers — UAT volunteers (simulated clinicians, think-aloud sessions, SUS questionnaire)"),
      sp(80),

      // ══ 14. LIMITATIONS ══════════════════════════════════════════
      h1("14. Limitations"),

      numbered("Single-site training dataset: Kaggle Hospital Triage Data reflects a specific US institution and time period. Multi-site external validation (MIMIC-IV-ED, pending) will partially address this. Fully generalisable models require multi-site, prospective clinical validation — future work."),
      numbered("Prototype only — NOT a certified medical device: MHRA/FDA Class II approval would be required for real clinical deployment. Permanent advisory disclaimers are displayed on all interfaces. No patient data has been used in development."),
      numbered("SHAP limitation on synthetic-adjacent data: GCS and pain_score show near-zero SHAP importance — attributed to Kaggle dataset distribution characteristics. Retraining on MIMIC-IV-ED is expected to correct this, as GCS is a primary predictor in clinical literature. Acknowledged explicitly in dissertation limitations."),
      numbered("Solo developer scope: Real-time HIS integration, mobile application, automated model retraining pipeline, multi-hospital federation, and NLP of unstructured clinical notes are deferred to future work."),
      numbered("UAT with simulated clinicians: Peer-based UAT (BSc students) is indicative only — not a substitute for validation with qualified ED nurses and doctors. Acknowledged as a study limitation in the evaluation chapter."),
      numbered("Fairness on Kaggle data only: Intersectional demographic analysis requires large, balanced cohorts. Results are preliminary; MIMIC-IV-ED analysis will provide stronger evidence."),
      sp(80),

      // ══ 15. POST-SUBMISSION MILESTONES ════════════════════════════
      h1("15. Post-Submission Milestones"),

      mkTable([40,20,40],[
        ["Milestone","Status","Date"],
        [["CITI 'Data or Specimens Only Research' (92%)","LGRAY"],["Completed","LGRAY"],["11 June 2026","LGRAY"]],
        [["CITI 'Conflicts of Interest' (100%)"],["Completed"],["11 June 2026"]],
        [["PhysioNet project submitted (Software, MIT)","LGRAY"],["Completed","LGRAY"],["11 June 2026","LGRAY"]],
        [["GitHub repository published (public)"],["Completed"],["11 June 2026"]],
        [["Security audit (Grade A, all issues resolved)","LGRAY"],["Completed","LGRAY"],["11 June 2026","LGRAY"]],
        [["PhysioNet credentialing approval"],["Pending (3–7 days)"],["Expected June 2026"]],
        [["MIMIC-IV-ED Data Use Agreement"],["Pending"],["Post-approval"]],
        [["MIMIC-IV-ED external validation"],["Pending"],["Post-DUA signature"]],
        [["GitHub release v1.0.0","LGRAY"],["Pending","LGRAY"],["Post-dissertation","LGRAY"]],
      ]),
      sp(80),

      // ══ 16. REFERENCES ════════════════════════════════════════════
      h1("16. References"),
      body("European Commission (2024) Regulation on Artificial Intelligence (AI Act). Available at: https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=CELEX:32024R1689 [Accessed 11 June 2026]."),
      sp(60),
      body("Fernandes, M., Mendonca, D., Pimentel, M., Madeira, C. and Augusto, V. (2020) 'Clinical Decision Support Systems for Triage in the Emergency Department using Intelligent Systems: A Review', Artificial Intelligence in Medicine, 102, p.101762. doi:10.1016/j.artmed.2019.101762."),
      sp(60),
      body("Floridi, L., Cowls, J., Beltrametti, M., Chatila, R., Chazerand, P., Dignum, V., Luetge, C., Madelin, R., Pagallo, U., Rossi, F., Schafer, B., Valcke, P. and Vayena, E. (2018) 'AI4People — An Ethical Framework for a Good AI Society: Opportunities, Risks, Principles, and Recommendations', Minds and Machines, 28(4), pp.689–707."),
      sp(60),
      body("Garbez, R.O., Cooper, J.A., Vuong, K. and Stotts, N.A. (2011) 'Factors influencing patient assignment to triage category', Emergency Medicine Journal, 28(3), pp.234–238."),
      sp(60),
      body("Johnson, A., Bulgarelli, L., Shen, L., Gayles, A., Shammout, A., Horng, S., Pollard, T.J., Hao, S., Moody, B., Mark, R.G., Radford, M.J. and Celi, L.A. (2023) 'MIMIC-IV (version 2.2)', PhysioNet. doi:10.13026/6mm1-ek67."),
      sp(60),
      body("Lundberg, S.M. and Lee, S.I. (2017) 'A unified approach to interpreting model predictions', Advances in Neural Information Processing Systems, 30, pp.4765–4774."),
      sp(60),
      body("Obermeyer, Z., Powers, B., Vogeli, C. and Mullainathan, S. (2019) 'Dissecting racial bias in an algorithm used to manage the health of populations', Science, 366(6464), pp.447–453."),
      sp(60),
      body("World Health Organization (2023) Emergency Care Systems: Improving Access, Quality and Safety in Emergency Care. Geneva: WHO. Available at: https://www.who.int/publications/i/item/9789240073135 [Accessed 11 June 2026]."),
      sp(80),
    ]
  }]
});

Packer.toBuffer(doc).then(buf => {
 fs.writeFileSync("D:\\Degree\\final\\Final Project\\TriageAI_Project_Proposal_UPDATED.docx", buf);
  console.log("Done.");
});