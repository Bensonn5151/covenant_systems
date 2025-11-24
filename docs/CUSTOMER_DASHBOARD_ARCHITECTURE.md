# Covenant Systems - Customer Dashboard Architecture

**Updated:** 2025-11-19
**Type:** Customer-Facing Compliance Intelligence Platform

---

## 🎯 Purpose

This is the **customer-facing dashboard** where companies interact with their compliance intelligence. It provides actionable insights, gap analysis, and regulatory intelligence - not backend pipeline management.

**Who uses this:**
- Compliance Officers
- Legal Teams
- Risk Managers
- C-Suite Executives
- Board Members

**What they do:**
- Understand compliance posture
- Identify and remediate gaps
- Track regulatory changes
- Generate stakeholder reports
- Make informed policy decisions

---

## 📐 Navigation Architecture

### Top Navigation

```
┌─────────────────────────────────────────────────────────────────────┐
│ [CovenantAI Logo]                                                    │
│                                                                      │
│  Overview | Regulatory Library | Mappings | Findings | Insights |   │
│  Reports | Risk Dashboard | 👤 Profile                              │
└─────────────────────────────────────────────────────────────────────┘
```

**Pages:**

1. **Overview** - Executive compliance dashboard
2. **Regulatory Library** - Browse regulations & your coverage
3. **Mappings** - How your policies align with regulations
4. **Findings** - Gaps, conflicts, recommendations
5. **Insights** - AI analysis & regulatory intelligence
6. **Reports** - Export compliance analytics
7. **Risk Dashboard** - Real-time risk metrics
8. **Profile** - User settings & notifications

---

## 🔍 Smart Filter Bar

**Context-aware filters across all pages:**

```
┌─────────────────────────────────────────────────────────────────────┐
│ 🔍 [Search regulations, policies, requirements...]                   │
│                                                                      │
│ 📜 Regulation ▾  |  🌍 Jurisdiction ▾  |  ⚠️  Risk Level ▾  |       │
│ 🏢 Business Area ▾  |  📅 Date Range ▾  |  🎯 Status ▾              │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 📊 Page Designs

### 1️⃣ Overview (Executive Dashboard)

**Purpose:** High-level compliance health at a glance

```
┌─────────────────────────────────────────────────────────────────────┐
│ COMPLIANCE HEALTH SCORE                                             │
│                                                                      │
│        ┌─────────────────────────┐                                  │
│        │                         │                                  │
│        │         95.2%           │         ↑ 2.3% from last month   │
│        │      Compliant          │                                  │
│        │                         │                                  │
│        └─────────────────────────┘                                  │
│                                                                      │
│ ┌────────────────┐  ┌────────────────┐  ┌────────────────┐         │
│ │ 247            │  │ 8              │  │ 12             │         │
│ │ Regulations    │  │ Open Findings  │  │ This Quarter   │         │
│ │ Tracked        │  │ (2 High Risk)  │  │ Reg Updates    │         │
│ └────────────────┘  └────────────────┘  └────────────────┘         │
│                                                                      │
│ ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ │
│                                                                      │
│ PRIORITY ACTIONS                      RECENT REGULATORY CHANGES     │
│ ┌─────────────────────────────────┐  ┌─────────────────────────────┐│
│ │ 🔴 High Priority (2)            │  │ Nov 15: OSFI B-13 Updated   ││
│ │                                 │  │ → Technology Risk Mgmt      ││
│ │ • Update AML risk assessment   │  │                             ││
│ │   program (PCMLTFA §9.6)       │  │ Nov 10: PIPEDA Amendment    ││
│ │                                 │  │ → Data Breach Notification  ││
│ │ • Add cyber expertise to board │  │                             ││
│ │   (OSFI B-13)                  │  │ Nov 3: Bank Act Clarification│
│ │                                 │  │ → Capital Requirements      ││
│ │ [View All Findings →]          │  │                             ││
│ │                                 │  │ [View All Updates →]        ││
│ └─────────────────────────────────┘  └─────────────────────────────┘│
│                                                                      │
│ COMPLIANCE BY DOMAIN                                                 │
│ ┌──────────────────────────────────────────────────────────────────┐│
│ │                                                                  ││
│ │ Anti-Money Laundering    ████████████████████ 98%  ✅           ││
│ │ Know Your Customer       ██████████████████░░ 92%  ✅           ││
│ │ Privacy & Data           ████████████████████ 97%  ✅           ││
│ │ Cybersecurity            ████████████░░░░░░░░ 73%  ⚠️            ││
│ │ Capital Requirements     ████████████████████ 100% ✅           ││
│ │ Consumer Protection      ██████████████████░░ 89%  ✅           ││
│ │                                                                  ││
│ └──────────────────────────────────────────────────────────────────┘│
│                                                                      │
│ [Generate Executive Report] [Schedule Board Briefing]               │
└─────────────────────────────────────────────────────────────────────┘
```

**Key Features:**
- Overall health score with trend
- Priority action items
- Regulatory update feed
- Domain-level compliance breakdown
- Quick export for executives

---

### 2️⃣ Regulatory Library

**Purpose:** Browse and understand applicable regulations

```
┌─────────────────────────────────────────────────────────────────────┐
│ REGULATORY LIBRARY                           [View: List | Grid]     │
│                                                                      │
│ 🔍 Search: "privacy data breach notification"                       │
│                                                                      │
│ ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ │
│                                                                      │
│ ┌──────────────────────────────────────────────────────────────────┐│
│ │ 🇨🇦 PIPEDA - Personal Information Protection Act                 ││
│ │                                                                   ││
│ │ Jurisdiction: Federal (Canada)  |  Regulator: OPC                ││
│ │ Your Coverage: 96% ████████████████████░                         ││
│ │                                                                   ││
│ │ Key Requirements (127 sections):                                 ││
│ │  • Consent for collection (Section 5.3) ✅ Covered               ││
│ │  • Data breach notification (Section 10.1) ✅ Covered            ││
│ │  • Access to personal info (Section 4.9) ⚠️  Partial             ││
│ │                                                                   ││
│ │ [View Full Act] [View Your Coverage] [View Mappings]             ││
│ └──────────────────────────────────────────────────────────────────┘│
│                                                                      │
│ ┌──────────────────────────────────────────────────────────────────┐│
│ │ 🏦 Bank Act (Canada)                                              ││
│ │                                                                   ││
│ │ Jurisdiction: Federal (Canada)  |  Regulator: OSFI               ││
│ │ Your Coverage: 94% ███████████████████░░                         ││
│ │                                                                   ││
│ │ Key Requirements (458 sections):                                 ││
│ │  • Licensing (Section 6) ✅ Covered                              ││
│ │  • Capital requirements (Section 485) ✅ Covered                 ││
│ │  • Related party transactions (Section 489) ❌ Gap Found         ││
│ │                                                                   ││
│ │ [View Full Act] [View Your Coverage] [View Mappings]             ││
│ └──────────────────────────────────────────────────────────────────┘│
│                                                                      │
│ ┌──────────────────────────────────────────────────────────────────┐│
│ │ 📋 OSFI B-13 - Technology & Cybersecurity Risk                   ││
│ │                                                                   ││
│ │ Jurisdiction: Federal (Canada)  |  Regulator: OSFI               ││
│ │ Your Coverage: 87% ██████████████████░░░                         ││
│ │ Last Updated: 2025-11-15 🆕                                      ││
│ │                                                                   ││
│ │ What Changed:                                                     ││
│ │  • Penetration testing: Annual → Quarterly ⚠️  Action Required   ││
│ │  • Board expertise: Cybersecurity required ⚠️  Action Required   ││
│ │                                                                   ││
│ │ [View Guideline] [View Changes] [Impact Assessment]              ││
│ └──────────────────────────────────────────────────────────────────┘│
│                                                                      │
│ [Filter by Jurisdiction] [Show Only Gaps] [Export List]             │
└─────────────────────────────────────────────────────────────────────┘
```

**Features:**
- Search across all regulations
- Coverage % for each regulation
- Visual indicators for gaps
- Change notifications (NEW badges)
- Direct links to full text
- Coverage summary per regulation

---

### 3️⃣ Mappings (Policy ↔ Regulation Alignment)

**Purpose:** Visualize how your policies map to regulations

```
┌─────────────────────────────────────────────────────────────────────┐
│ COMPLIANCE MAPPINGS                      [View: Graph | Table]       │
│                                                                      │
│ Selected: AML Framework v3.2                                         │
│                                                                      │
│ ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ │
│                                                                      │
│ RELATIONSHIP GRAPH                                                   │
│ ┌──────────────────────────────────────────────────────────────────┐│
│ │                                                                   ││
│ │         PCMLTFA §9.6                  Bank Act §7                ││
│ │         [Risk Assessment]              [AML Compliance]          ││
│ │                │                              │                  ││
│ │                │ requires                     │ requires         ││
│ │                ↓                              ↓                  ││
│ │                                                                   ││
│ │           ┌───────────────────────────────────────┐              ││
│ │           │   AML Framework v3.2                  │              ││
│ │           │   (Your Internal Policy)              │              ││
│ │           │                                       │              ││
│ │           │   Coverage: 95%                       │              ││
│ │           │   Last Updated: 2025-10-01            │              ││
│ │           └───────────────────────────────────────┘              ││
│ │                           │                                       ││
│ │                           │ implements                            ││
│ │                           ↓                                       ││
│ │                  OSFI B-13 Guideline                             ││
│ │                  [Technology Risk]                                ││
│ │                                                                   ││
│ └──────────────────────────────────────────────────────────────────┘│
│                                                                      │
│ MAPPING DETAILS                                                      │
│ ┌──────────────────────────────────────────────────────────────────┐│
│ │ Regulation Section        │ Your Policy Section  │ Status        ││
│ ├──────────────────────────────────────────────────────────────────┤│
│ │ PCMLTFA §9.6(1)          │ AML Framework §4.2   │ ✅ Mapped     ││
│ │ "Risk assessment program"│ "Risk Assessment"    │ (95% match)   ││
│ │                          │                      │               ││
│ │ PCMLTFA §9.6(2)          │ AML Framework §4.3   │ ⚠️  Partial   ││
│ │ "Periodic review"        │ "Annual Review"      │ (Need update) ││
│ │                          │                      │               ││
│ │ PCMLTFA §9.6(3)          │ --                   │ ❌ Gap        ││
│ │ "Documentation reqs"     │ Not covered          │ (Action req'd)││
│ │                          │                      │               ││
│ │ Bank Act §7(1)           │ AML Framework §2.1   │ ✅ Mapped     ││
│ │ "AML program required"   │ "Program Overview"   │ (100% match)  ││
│ └──────────────────────────────────────────────────────────────────┘│
│                                                                      │
│ COVERAGE SUMMARY                                                     │
│ ┌──────────────────────────────────────────────────────────────────┐│
│ │ Fully Mapped:     42 requirements  ████████████████████ 84%     ││
│ │ Partially Mapped:  5 requirements  ███░░░░░░░░░░░░░░░░ 10%     ││
│ │ Not Mapped:        3 requirements  ██░░░░░░░░░░░░░░░░░  6%     ││
│ │                                                                  ││
│ │ [View Gaps] [Export Coverage Matrix] [Update Policy]            ││
│ └──────────────────────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────────────────┘
```

**Features:**
- Interactive relationship graph
- Clause-level mapping table
- Coverage percentage per policy
- Gap identification
- Side-by-side text comparison
- Export mapping matrix

---

### 4️⃣ Findings (Gaps & Recommendations)

**Purpose:** Actionable compliance issues and AI recommendations

```
┌─────────────────────────────────────────────────────────────────────┐
│ COMPLIANCE FINDINGS                    [8 Total] [2 High Priority]  │
│                                                                      │
│ Filters: [⚠️  High Risk ▾] [All Domains ▾] [Open Only ☑]            │
│                                                                      │
│ ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ │
│                                                                      │
│ ┌──────────────────────────────────────────────────────────────────┐│
│ │ 🔴 HIGH PRIORITY                                 Finding #F-0042  ││
│ │                                                                   ││
│ │ Missing Coverage: PCMLTFA §9.6(3) Documentation Requirements     ││
│ │                                                                   ││
│ │ What's Required:                                                  ││
│ │ "The entity shall maintain records of all risk assessments       ││
│ │  conducted, including methodology, findings, and mitigation      ││
│ │  plans, for a minimum of 7 years."                               ││
│ │                                                                   ││
│ │ Current Policy Status:                                            ││
│ │ Your AML Framework v3.2 does not specify documentation           ││
│ │ requirements or retention periods for risk assessments.          ││
│ │                                                                   ││
│ │ Risk Impact: High                                                 ││
│ │  • Regulatory non-compliance                                     ││
│ │  • Potential enforcement action                                  ││
│ │  • Audit findings                                                ││
│ │                                                                   ││
│ │ AI Recommendation:                                                ││
│ │ Add new section 4.4 "Risk Assessment Documentation" with:        ││
│ │  1. Required documentation elements                              ││
│ │  2. 7-year retention requirement                                 ││
│ │  3. Storage and access controls                                  ││
│ │                                                                   ││
│ │ Suggested Policy Text:                                            ││
│ │ ┌────────────────────────────────────────────────────────────┐   ││
│ │ │ "4.4 Risk Assessment Documentation                         │   ││
│ │ │                                                            │   ││
│ │ │ The organization shall maintain comprehensive records of  │   ││
│ │ │ all risk assessments, including:                          │   ││
│ │ │  • Assessment methodology and criteria                    │   ││
│ │ │  • Identified risks and severity ratings                  │   ││
│ │ │  • Mitigation plans and responsible parties               │   ││
│ │ │                                                            │   ││
│ │ │ All records shall be retained for a minimum of 7 years    │   ││
│ │ │ in accordance with PCMLTFA requirements."                 │   ││
│ │ └────────────────────────────────────────────────────────────┘   ││
│ │                                                                   ││
│ │ [Copy Policy Text] [Mark as Resolved] [Assign to Team Member]    ││
│ └──────────────────────────────────────────────────────────────────┘│
│                                                                      │
│ ┌──────────────────────────────────────────────────────────────────┐│
│ │ 🔴 HIGH PRIORITY                                 Finding #F-0038  ││
│ │                                                                   ││
│ │ Outdated Requirement: OSFI B-13 Penetration Testing Frequency    ││
│ │                                                                   ││
│ │ What Changed (Nov 15, 2025):                                     ││
│ │ Before: "Annual penetration testing required"                    ││
│ │ After:  "Quarterly penetration testing required"                 ││
│ │                                                                   ││
│ │ Your Current Policy (IT Security v2.1):                          ││
│ │ "Penetration testing shall be conducted annually..."             ││
│ │                                                                   ││
│ │ Required Action:                                                  ││
│ │ Update IT Security Policy to reflect quarterly requirement       ││
│ │                                                                   ││
│ │ [View Policy] [Generate Update] [Track Progress]                 ││
│ └──────────────────────────────────────────────────────────────────┘│
│                                                                      │
│ FINDINGS SUMMARY                                                     │
│ ┌──────────────────────────────────────────────────────────────────┐│
│ │ ID     │ Type      │ Domain    │ Risk  │ Status      │ Assigned  ││
│ ├──────────────────────────────────────────────────────────────────┤│
│ │ F-0042 │ Gap       │ AML       │ 🔴 High│ Open       │ Sarah K.  ││
│ │ F-0038 │ Outdated  │ Cyber     │ 🔴 High│ In Progress│ Mike T.   ││
│ │ F-0035 │ Partial   │ Privacy   │ 🟡 Med │ Open       │ --        ││
│ │ F-0031 │ Gap       │ KYC       │ 🟡 Med │ Resolved   │ Jane D.   ││
│ │ F-0029 │ Ambiguous │ Capital   │ 🟢 Low │ Open       │ --        ││
│ └──────────────────────────────────────────────────────────────────┘│
│                                                                      │
│ [Export Findings Report] [Bulk Assign] [Create Remediation Plan]    │
└─────────────────────────────────────────────────────────────────────┘
```

**Features:**
- Prioritized list of compliance issues
- AI-generated policy recommendations
- Draft policy text suggestions
- Before/after change tracking
- Assignment and workflow
- Progress tracking

---

### 5️⃣ Insights (AI Regulatory Intelligence)

**Purpose:** Ask questions and get AI-powered answers

```
┌─────────────────────────────────────────────────────────────────────┐
│ REGULATORY INSIGHTS                            🤖 AI-Powered         │
│                                                                      │
│ ASK COVENANT AI                                                      │
│ ┌──────────────────────────────────────────────────────────────────┐│
│ │ 💬 "What are the key changes in OSFI B-13 that affect our        ││
│ │     organization and what actions do we need to take?"           ││
│ │                                                        [Ask 🔍]   ││
│ └──────────────────────────────────────────────────────────────────┘│
│                                                                      │
│ AI RESPONSE:                                                         │
│ ┌──────────────────────────────────────────────────────────────────┐│
│ │ Based on the November 15, 2025 update to OSFI B-13, here are    ││
│ │ the key changes affecting your organization:                     ││
│ │                                                                   ││
│ │ 1. Penetration Testing Frequency 🔴 High Priority                ││
│ │    ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ ││
│ │    Changed from annual to quarterly penetration testing          ││
│ │                                                                   ││
│ │    Your Current Policy: IT Security Policy v2.1 requires annual  ││
│ │    Action Required: Update testing schedule and budget           ││
│ │                                                                   ││
│ │    Evidence:                                                      ││
│ │    • OSFI B-13 Section 4.2.3: "Institutions must conduct        ││
│ │      comprehensive penetration testing on a quarterly basis..."  ││
│ │    • Your IT Security §5.3: "Annual penetration testing..."     ││
│ │                                                                   ││
│ │ 2. Board Cybersecurity Expertise 🔴 High Priority                ││
│ │    ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ ││
│ │    New requirement for board-level cybersecurity expertise       ││
│ │                                                                   ││
│ │    Your Current Status: Board Charter does not specify           ││
│ │    Action Required: Amend charter or recruit cyber expert        ││
│ │                                                                   ││
│ │ 3. Third-Party Risk Management 🟡 Medium Priority                ││
│ │    ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ ││
│ │    Enhanced vendor risk assessment requirements                  ││
│ │                                                                   ││
│ │    Your Current Policy: Vendor Management v1.3 is partially     ││
│ │    compliant                                                      ││
│ │    Action Required: Add continuous monitoring requirement        ││
│ │                                                                   ││
│ │ Summary:                                                          ││
│ │ 3 policies need updates | Estimated effort: 40 hours             ││
│ │ Timeline: 30 days to full compliance                             ││
│ │                                                                   ││
│ │ [Generate Action Plan] [Export Analysis] [View Full Changes]     ││
│ └──────────────────────────────────────────────────────────────────┘│
│                                                                      │
│ ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ │
│                                                                      │
│ RECENT REGULATORY UPDATES                                            │
│ ┌──────────────────────────────────────────────────────────────────┐│
│ │ Nov 15, 2025 - OSFI B-13 Technology Risk Guideline               ││
│ │ Impact: High | 3 policies affected | [View Analysis]             ││
│ │                                                                   ││
│ │ Nov 10, 2025 - PIPEDA Data Breach Notification Amendment         ││
│ │ Impact: Medium | 1 policy affected | [View Analysis]             ││
│ │                                                                   ││
│ │ Nov 3, 2025 - Bank Act Capital Requirements Clarification        ││
│ │ Impact: Low | No action required | [View Analysis]               ││
│ └──────────────────────────────────────────────────────────────────┘│
│                                                                      │
│ TRENDING TOPICS                                                      │
│ ┌──────────────────────────────────────────────────────────────────┐│
│ │ [Cybersecurity 🔥] [Data Privacy] [AML] [Climate Risk]          ││
│ └──────────────────────────────────────────────────────────────────┘│
│                                                                      │
│ POPULAR QUESTIONS                                                    │
│ • "What are my organization's cybersecurity obligations?"           │
│ • "Show me all privacy-related requirements for payment processors" │
│ • "Compare our AML policy with PCMLTFA requirements"                │
└─────────────────────────────────────────────────────────────────────┘
```

**Features:**
- Natural language Q&A
- Evidence-based answers with citations
- Impact analysis
- Regulatory change feed
- Topic trending
- Suggested questions

---

### 6️⃣ Reports (Export & Share)

**Purpose:** Generate compliance reports for stakeholders

```
┌─────────────────────────────────────────────────────────────────────┐
│ COMPLIANCE REPORTS                                                   │
│                                                                      │
│ QUICK REPORTS                                                        │
│ ┌──────────────────────────────────────────────────────────────────┐│
│ │ 📊 Compliance Health Report          [Generate PDF]              ││
│ │    Executive summary of current compliance status                ││
│ │                                                                   ││
│ │ 📋 Gap Analysis Report                [Generate Excel]           ││
│ │    Detailed list of all findings and recommendations             ││
│ │                                                                   ││
│ │ 🗺️  Coverage Matrix                   [Generate PDF]             ││
│ │    Policy-to-regulation mapping table                            ││
│ │                                                                   ││
│ │ 📈 Quarterly Board Report             [Generate PDF]             ││
│ │    Executive summary for board of directors                      ││
│ │                                                                   ││
│ │ ⚠️  Risk Dashboard                     [Generate PDF]             ││
│ │    Risk heatmap and metrics                                      ││
│ └──────────────────────────────────────────────────────────────────┘│
│                                                                      │
│ CUSTOM REPORT BUILDER                                                │
│ ┌──────────────────────────────────────────────────────────────────┐│
│ │ Report Title: [_______________________________________]           ││
│ │                                                                   ││
│ │ Include Sections:                                                 ││
│ │  ☑ Compliance Score & Trend                                      ││
│ │  ☑ Priority Findings                                             ││
│ │  ☑ Regulatory Updates This Period                                ││
│ │  ☑ Coverage by Domain                                            ││
│ │  ☐ Detailed Gap Analysis                                         ││
│ │  ☐ Mapping Matrix                                                ││
│ │  ☐ Remediation Timeline                                          ││
│ │                                                                   ││
│ │ Filters:                                                          ││
│ │  Jurisdiction:   [Federal (Canada) ▾]                            ││
│ │  Date Range:     [Last Quarter ▾]                                ││
│ │  Risk Level:     [All ▾]                                         ││
│ │  Domain:         [All ▾]                                         ││
│ │                                                                   ││
│ │ Format:  ◉ PDF  ○ Excel  ○ PowerPoint                           ││
│ │ Branding: ☑ Include company logo                                 ││
│ │           ☑ Confidential watermark                               ││
│ │                                                                   ││
│ │ [Preview Report] [Generate & Download]                            ││
│ └──────────────────────────────────────────────────────────────────┘│
│                                                                      │
│ SCHEDULED REPORTS                                                    │
│ ┌──────────────────────────────────────────────────────────────────┐│
│ │ Name                    │ Frequency │ Recipients     │ Action     ││
│ ├──────────────────────────────────────────────────────────────────┤│
│ │ Monthly Compliance Brief│ Monthly   │ Executive Team │ [Edit]     ││
│ │ Quarterly Board Report  │ Quarterly │ Board Members  │ [Edit]     ││
│ │ Weekly Updates Summary  │ Weekly    │ Compliance Mgr │ [Edit]     ││
│ └──────────────────────────────────────────────────────────────────┘│
│                                                                      │
│ [+ New Scheduled Report]                                             │
│                                                                      │
│ REPORT HISTORY                                                       │
│ ┌──────────────────────────────────────────────────────────────────┐│
│ │ Nov 15, 2025 - Q4 Compliance Health Report.pdf    [Download]     ││
│ │ Nov 1, 2025 - OSFI B-13 Impact Analysis.xlsx      [Download]     ││
│ │ Oct 31, 2025 - October Gap Analysis.pdf           [Download]     ││
│ └──────────────────────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────────────────┘
```

**Features:**
- Pre-built templates
- Custom report builder
- Scheduled/automated reports
- Multiple export formats
- Branding options
- Email distribution

---

### 7️⃣ Risk Dashboard

**Purpose:** Real-time compliance risk visualization

```
┌─────────────────────────────────────────────────────────────────────┐
│ RISK DASHBOARD                                                       │
│                                                                      │
│ OVERALL COMPLIANCE TREND (12 Months)                                 │
│ ┌──────────────────────────────────────────────────────────────────┐│
│ │ 100% ┤                                           ●──●            ││
│ │  95% ┤                       ●───●───●──────●───●                ││
│ │  90% ┤           ●───●──────●                                    ││
│ │  85% ┤   ●──────●                                                ││
│ │  80% ┼───┼───┼───┼───┼───┼───┼───┼───┼───┼───┼───┼──→          ││
│ │      Jan Feb Mar Apr May Jun Jul Aug Sep Oct Nov Dec             ││
│ │                                                                   ││
│ │  Current: 95.2% ↑ 2.3%                                           ││
│ └──────────────────────────────────────────────────────────────────┘│
│                                                                      │
│ RISK HEATMAP                                                         │
│ ┌──────────────────────────────────────────────────────────────────┐│
│ │                                                                   ││
│ │              Policy  Controls  Monitoring  Training               ││
│ │              ───────────────────────────────────────              ││
│ │ AML           🟢      🟢        🟡         🟢                     ││
│ │ KYC           🟡      🟢        🟢         🟡                     ││
│ │ Privacy       🟢      🟡        🟢         🟢                     ││
│ │ Cyber         🔴      🟡        🔴         🟡      ← High Risk    ││
│ │ Capital       🟢      🟢        🟢         🟢                     ││
│ │ Consumer      🟡      🟢        🟢         🟡                     ││
│ │                                                                   ││
│ │ 🟢 Compliant (90-100%)  🟡 Needs Attention (70-89%)              ││
│ │ 🔴 High Risk (<70%)                                              ││
│ └──────────────────────────────────────────────────────────────────┘│
│                                                                      │
│ KEY METRICS                                                          │
│ ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐      │
│ │ Policy Coverage │  │ Open Findings   │  │ Avg Resolution  │      │
│ │      94.3%      │  │        8        │  │     12 days     │      │
│ │      ↑ 1.2%     │  │     ↓ 3         │  │      ↓ 2        │      │
│ └─────────────────┘  └─────────────────┘  └─────────────────┘      │
│                                                                      │
│ REGULATORY CHANGE IMPACT                                             │
│ ┌──────────────────────────────────────────────────────────────────┐│
│ │ This Quarter: 12 regulatory updates                              ││
│ │                                                                   ││
│ │  High Impact:    2 updates  → 5 policies affected                ││
│ │  Medium Impact:  7 updates  → 8 policies affected                ││
│ │  Low Impact:     3 updates  → 0 policies affected                ││
│ │                                                                   ││
│ │ [View All Changes]                                                ││
│ └──────────────────────────────────────────────────────────────────┘│
│                                                                      │
│ TOP RISKS                                                            │
│ ┌──────────────────────────────────────────────────────────────────┐│
│ │ 🔴 Cybersecurity - OSFI B-13 penetration testing frequency       ││
│ │    Affects: IT Security Policy | Priority: High                  ││
│ │                                                                   ││
│ │ 🔴 Cybersecurity - Board expertise requirement                   ││
│ │    Affects: Board Charter | Priority: High                       ││
│ │                                                                   ││
│ │ 🟡 KYC - Customer verification timeline clarity                  ││
│ │    Affects: KYC Policy | Priority: Medium                        ││
│ └──────────────────────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────────────────┘
```

**Features:**
- Compliance trend over time
- Risk heatmap (domain × function)
- Key performance metrics
- Impact of regulatory changes
- Top risk callouts
- Visual dashboards for executives

---

### 8️⃣ Profile & Settings

**Purpose:** User preferences and account management

```
┌─────────────────────────────────────────────────────────────────────┐
│ PROFILE & SETTINGS                                                   │
│                                                                      │
│ [Profile] [Notifications] [Team] [Organization]                     │
│                                                                      │
│ ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ │
│                                                                      │
│ PROFILE                                                              │
│ ┌──────────────────────────────────────────────────────────────────┐│
│ │ Name:        Sarah Kim                                           ││
│ │ Email:       sarah.kim@company.com                               ││
│ │ Role:        Compliance Manager                                  ││
│ │ Department:  Legal & Compliance                                  ││
│ │                                                                   ││
│ │ [Edit Profile] [Change Password]                                 ││
│ └──────────────────────────────────────────────────────────────────┘│
│                                                                      │
│ NOTIFICATION PREFERENCES                                             │
│ ┌──────────────────────────────────────────────────────────────────┐│
│ │ Email Notifications:                                              ││
│ │  ☑ New regulatory updates (immediate)                            ││
│ │  ☑ High-priority findings (immediate)                            ││
│ │  ☑ Medium-priority findings (daily digest)                       ││
│ │  ☐ Low-priority findings                                         ││
│ │  ☑ Weekly compliance summary                                     ││
│ │                                                                   ││
│ │ In-App Notifications:                                             ││
│ │  ☑ Task assignments                                              ││
│ │  ☑ Report generation complete                                    ││
│ │  ☑ System announcements                                          ││
│ │                                                                   ││
│ │ [Save Preferences]                                                ││
│ └──────────────────────────────────────────────────────────────────┘│
│                                                                      │
│ ORGANIZATION SETTINGS                                                │
│ ┌──────────────────────────────────────────────────────────────────┐│
│ │ Company Name:     Acme Financial Services Inc.                   ││
│ │ Industry:         Banking                                        ││
│ │ Jurisdictions:    Federal (Canada), Ontario                      ││
│ │                                                                   ││
│ │ Default Filters:                                                  ││
│ │  Primary Jurisdiction: Federal (Canada)                          ││
│ │  Risk Threshold:       Medium and above                          ││
│ │                                                                   ││
│ │ [Update Settings]                                                 ││
│ └──────────────────────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────────────────┘
```

---

## 🎨 Design System

**Consistent with landing page:**

- Dark terminal aesthetic (#050505 background)
- Green accent (#10b981) for actions, success
- Red (#ef4444) for high risk
- Amber (#f59e0b) for warnings
- Monospace fonts for technical elements
- Clean sans-serif for body text
- Lucide icons throughout
- Grid patterns for backgrounds

---

## 🔌 Backend Integration

### API Structure

```
/api/v1/
├── overview/          # Dashboard metrics
├── regulations/       # Regulatory library
├── mappings/          # Policy-regulation alignment
├── findings/          # Gaps and recommendations
├── insights/          # AI Q&A and analysis
├── reports/           # Report generation
├── risk/              # Risk metrics
└── user/              # Profile and settings
```

### Data Flow

```
Customer Action → Next.js Frontend → FastAPI Backend →
                                    ↓
                        ┌───────────┴───────────┐
                        │                       │
                    PostgreSQL          Vector DB (Qdrant)
                 (structured data)    (semantic search)
                        │                       │
                        └───────────┬───────────┘
                                    ↓
                            Knowledge Graph (YAML)
                                    ↓
                            AI Processing Layer
                                    ↓
                            Response to Frontend
```

---

## 🚀 Implementation Plan

### Phase 1: Core Pages
1. Overview dashboard
2. Regulatory Library
3. Basic navigation

### Phase 2: Intelligence
4. Mappings visualization
5. Findings with AI recommendations
6. Insights Q&A

### Phase 3: Reporting
7. Reports generation
8. Risk Dashboard
9. Export functionality

### Phase 4: Polish
10. Real-time updates
11. Team collaboration
12. Mobile responsiveness

---

**This is a customer-facing platform, not an admin tool.**

No pipeline monitoring, ETL jobs, or system configuration - those stay backend-only.