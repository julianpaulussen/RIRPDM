# Use Case Study - RI Portfolio Monitoring at a Research Funding Agency

The use case and its competency questions show how the ontology answers questions
that today require manual collation of roadmap PDFs, finance spreadsheets and
evaluation reports. 

## 1. Context

Research funders are confronted with the challenge of supporting increasingly
large and complex RI portfolios, and decision processes need to be properly
informed. Monitoring mechanisms are heterogeneous, ranging from automated processes to no
monitoring at all, and there is need for efficient mechanisms to monitor performance
of national and international RIs in terms of research, benefits (impact),
management and governance. The ESFRI Monitoring Working Group (2019) added the
data-availability pain point directly: some RIs "are not yet able to gather the
data needed to track all KPIs and may need specific tools to be developed."

The information a portfolio analyst needs lives in four disconnected silos:

| Silo | Holds | Typical source |
|------|-------|----------------|
| Roadmap / governance / lifecycle | RI typology, governance, phase | ESFRI roadmap entries |
| Finance | full-lifecycle & operating costs | finance spreadsheets |
| Evaluation | Scientific- / Implementation-Case scores | ESFRI panel reports |
| Bibliometrics | publications & datasets enabled | CrossRef, OpenAIRE, DataCite |

--- 

**Example cross-cutting question**: "Which ESFRI Landmarks cost over €100 M, scored
lower on scientific merit after selection than before, and still hold unpreserved
datasets? Answering it today means joining all four silos by hand. RIRPDM
collapses it into a single SPARQL query.


Explanations:
- (Scientific merit = "how scientifically valuable an RI is assessed across different dimensions")
- (ESFRI Landmark = fully operational RIs
recognised by ESFRI as major European research assets)

## 2. Actor and goal

- **Actor:** a *Research Infrastructure Portfolio Analyst* at a funding
  agency or ministry
- **Goal:** monitor the RI portfolio to support investment, compliance and
  reporting decisions from one queryable model, minimising the reporting burden
  the ESFRI working group flagged (RIs already report differing KPI sets to boards, funders, ...)

## 3. Scenario walk-through

The analyst prepares a quarterly portfolio review. Each step maps to a competency question.

### Step 1 - What RIs exist and where are they in their lifecycle? - CQ01
*"What research infrastructures exist, of what type, and in which lifecycle phase?"*

The analyst starts with a simple inventory: what RIs are there, what type is each
(single-sited, distributed, virtual), and what phase are they in (**CQ01**)? This
gives the full portfolio picture before narrowing to any specific group.

### Step 2 - How is each distributed RI structured? - CQ02
*"For a distributed RI, what is its central hub and which national nodes does it include?"*

Distributed RIs are the hardest to govern.Responsibility is split across a
central hub and national nodes. The analyst maps out this structure for each
distributed RI (**CQ02**). Missing nodes or an absent hub would be a governance
red flag.

### Step 3 - Who funds each RI, and for how much? - CQ03
*"Which RIs are funded, by which grant and agency, and for how much?"*

The analyst traces the funding chain: which grant covers each RI, which agency
awarded it, and what is its value (**CQ03**). This works for any funder or
programme, because all funding data follows the same FRAPO (Funding, Research Administration and Projects Ontology) vocabulary.

### Step 4 - Are research outputs open and preserved? - CQ04
*"Which datasets are FAIR-compliant but do not ensure long-term preservation?"*

The analyst checks for a common compliance gap: datasets that follow FAIR 
principles for research data management on paper but have no long-term preservation guarantee (**CQ04**). (FAIR = Findable, Accessible, Interoperable, Reusable).

### Step 5 - Did each RI deliver on its scientific promise? - CQ05
*"How did an RI's Scientific Excellence score change from proposal to selection?"*

Before an RI is selected, ESFRI scores its scientific merit ("ex ante").
After selection, the RI is scored again ("ex post"). The analyst compares both
scores (**CQ05**) to see whether merit improved, held steady, or dropped.

> **Note:** scores are not meant for cross-RI comparison. Each RI is different.
> Read results not as a ranking ~ ESFRI Monitoring Working Group (2019).

### Step 6 - Which Landmarks are a problem across all four dimensions? - CQ06
*"Which operational Landmarks cost above threshold, dropped in scientific merit, and still have unpreserved datasets?"*

The analyst wants to find out which operational Landmarks are flagged on every
front at once: high investment cost, a drop in scientific merit since selection,
and datasets that are still not preserved. No single source holds all of this:
roadmap data, finance records, evaluation scores and bibliometric records each
live separately. The analyst runs one query that joins all four silos (**CQ06**)
and gets a prioritised watch-list in return.

### Step 7 - How deep does the funding chain go? - CQ07
*"Which funding sources, at any level, support a given RI, directly or indirectly?"*

Funding has levels: an RI is covered by a grant, and that grant is part of a broader programme. The analyst wants both in one query, not two (**CQ07**). Because `isSupportedBy` is transitive, the reasoner fills in the gap. If the RI is supported by a grant, and the grant is supported by a programme, the RI is automatically also supported by the programme.

### Step 8 - Which institutions collaborate? - CQ08
*"Which research institutions collaborate with each other?"*

The analyst maps institutional collaboration networks across RIs to identify shared interests and avoid funding duplication (**CQ08**). `collaboratesWith` is symmetric. Asserting that institution A collaborates with B is enough. The reasoner infers the reverse. Only one direction needs to be populated in the knowledge graph.

## 4. Outcome

In one session against the SPARQL endpoint the analyst produces the quarterly
review: 
- a full RI inventory with types and phases (CQ01), 
- distributed-RI structure maps (CQ02), 
- a funding table with grant provenance (CQ03),
- a list of FAIR-but-unpreserved datasets (CQ04),
- an ex-ante/ex-post merit comparison (CQ05), 
- the integrated cross-silo watch-list (CQ06),
- a full multi-level funding chain per RI (CQ07),
- and an institutional collaboration network map (CQ08).
No roadmap PDF or finance spreadsheet was opened.

## 5. CQ coverage map

| Decision point | Silo(s) | Competency question |
|---|---|---|
| Portfolio inventory & lifecycle | Roadmap | CQ01 |
| Distributed RI structure | Roadmap | CQ02 |
| Funding chain | Finance | CQ03 |
| Open-science compliance | Bibliometrics | CQ04 |
| Scientific merit over time | Evaluation | CQ05 |
| Cross-silo integration | All four | CQ06 |
| Transitive funding chain | Finance | CQ07 |
| Institutional collaboration network | Roadmap | CQ08 |

All eight CQs are exercised by the single scenario, each covering a distinct part
of the schema and a distinct data silo.

## 6. Sources

// TODO: READ LISTED DOCUMENTS AND VERIFY THE USE CASE STUDY. ALL OF THEM HOLD OR COULD HOLD VALUABLE INFORMATION. 

- OECD Global Science Forum & Science Europe (2020), *Optimising the Operation
  and Use of National Research Infrastructures* (OECD STI Policy Paper No. 91).
- ESFRI Working Group on Monitoring of Research Infrastructures Performance (2019)
- ESFRI Roadmap Guide
- European Commission (2017), *Sustainable European Research Infrastructures
- RI-PATHS (H2020) 