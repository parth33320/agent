# Miriam Miradi 12-Layer Production Agent Architecture

This document defines the 12 production engineering layers for reliable, scalable, and maintainable enterprise agentic systems (based on Miriam Miradi's 4-phase architecture).

---

## Overview of the 4 Phases & 12 Layers

| Phase | Layer # | Layer Name | Core Focus |
|---|---|---|---|
| **Phase 1: Foundation** | 1 | Business Understanding | Decision scoping, business rules, and success criteria |
| | 2 | Data Understanding | Completeness, availability, freshness, and quality checks |
| | 3 | Knowledge Engineering | Chunking, embeddings, indexing, and structured knowledge graphs |
| **Phase 2: Context & Routing** | 4 | Context Engineering | Differentiated context bundles per intent/category |
| | 5 | Model Engineering | Task-specific model profiles, roles, and parameter tuning |
| | 6 | Semantic Engineering | Domain ontology, concept resolution, and abbreviation expansion |
| | 7 | Agent Engineering | Graph topology, state management, and deterministic routing |
| **Phase 3: Reliability & Safety** | 8 | Loop Engineering | Self-correction loops, allergy/constraint verification, and human escalation |
| | 9 | Evaluation Engineering | Repeatable golden eval cases, pass-rate metrics, and regressions |
| | 10 | Harness Engineering | Execution replay, end-to-end tracing, and reproducible state capture |
| **Phase 4: Scale & Evolution** | 11 | Infrastructure Engineering | Timeouts, backoffs, circuit breakers, and graceful degradation |
| | 12 | Continual Learning | Failure clustering, pattern mining, and human feedback loops |

---

## Layer Specifications

### Layer 1: Business Understanding
- **Definition:** Formal specification of the business decision scope, operational constraints, decision support boundaries, and explicit success criteria before deploying agent autonomy.
- **Supply Chain Example:** Defining explicit decision bounds for autonomous spot procurement: purchase orders under $25,000 can be auto-approved only if supplier SLA compliance is above 98% and delivery lead time is within 3 business days; otherwise route to human procurement manager.
- **Failure Mode Without It:** Agent executes out-of-scope actions, unauthorized contractual commitments, or arbitrary business decisions lacking governance, leading to financial liability and compliance violations.
- **Verification Pattern:**
  - `grep -rnE "(decision_scope|business_rules|policy_engine|success_criteria|supported_decision)" .`

---

### Layer 2: Data Understanding
- **Definition:** Systematic assessment of input data completeness, freshness, provenance, and field-level availability prior to model inference.
- **Supply Chain Example:** Checking whether a supplier invoice contains a matching bill of lading (BOL), validated purchase order ID, and updated tax identifier before triggering automated three-way invoice matching.
- **Failure Mode Without It:** Decisions are rendered on missing, stale, or phantom data (e.g., reordering inventory based on a supplier feed that hasn't synced in 48 hours).
- **Verification Pattern:**
  - `grep -rnE "(data_completeness|check_missing_fields|field_availability|data_validation|schema_validation)" .`

---

### Layer 3: Knowledge Engineering
- **Definition:** Ingestion, normalization, chunking, indexing, and retrieval-augmented structuring (including vector search and knowledge graphs) of domain information.
- **Supply Chain Example:** Vectorizing tier-1 vendor contracts, Master Services Agreements (MSAs), and Incoterms standards into a vector index alongside a supplier graph tracking multi-tier component dependencies.
- **Failure Mode Without It:** Agent operates in a vacuum or hallucinates vendor terms, contractual penalties, and supplier relationship histories.
- **Verification Pattern:**
  - `grep -rnE "(vector_store|embeddings|knowledge_graph|document_ingestion|retrieval_tool|chunking)" .`

---

### Layer 4: Context Engineering
- **Definition:** Dynamic assembly of differentiated, minimal, task-specific context bundles tailored to the immediate operational scenario rather than dumping global state into prompts.
- **Supply Chain Example:** When handling an emergency cargo diversion due to port strikes, injecting only carrier spot rates, customs transit permits, and active re-routing channels rather than full annual procurement histories.
- **Failure Mode Without It:** Context saturation, lost-in-the-middle phenomena, prompt token bloat, and diluted attention causing missed critical constraints.
- **Verification Pattern:**
  - `grep -rnE "(context_bundle|context_builder|assemble_context|differentiated_context|filter_context)" .`

---

### Layer 5: Model Engineering
- **Definition:** Assignment of specialized, task-tuned model profiles (temperature, system instructions, capability tiers, and model sizes) matched to specific subtasks rather than using a single generic LLM.
- **Supply Chain Example:** Using a lightweight, fast model for barcode and SKU extraction, a fine-tuned medium model for classification and customs code tagging, and a frontier reasoning model for supplier contract dispute negotiation.
- **Failure Mode Without It:** Overpaying in latency and API costs for trivial tasks while underperforming on complex analytical negotiations.
- **Verification Pattern:**
  - `grep -rnE "(model_profile|model_tier|temperature=|system_prompt|model_selector|gemini-1\.5|gpt-4)" .`

---

### Layer 6: Semantic Engineering
- **Definition:** Domain-specific vocabulary normalization, abbreviation expansion, synonym resolution, and semantic disambiguation prior to retrieval and reasoning.
- **Supply Chain Example:** Resolving "PO" to "Purchase Order" (and distinguishing from "Port of Origin"), standardizing "FOB" (Free on Board) vs "CIF" (Cost, Insurance, and Freight), and normalizing vendor names across regional ERP systems.
- **Failure Mode Without It:** Mismatched records, misclassified purchase orders, and faulty searches caused by polysemy and domain jargon confusion.
- **Verification Pattern:**
  - `grep -rnE "(resolve_concept|semantic_resolution|domain_ontology|abbreviation_map|synonym_mapper)" .`

---

### Layer 7: Agent Engineering
- **Definition:** Multi-agent state orchestration, graph topologies (e.g. LangGraph / StateGraph), role segregation, and deterministic state transitions.
- **Supply Chain Example:** Designing an autonomous procurement workflow where a Buyer Agent negotiates pricing with a Supplier Agent across stateful negotiation rounds, transitioning to a Compliance Verifier node before human sign-off.
- **Failure Mode Without It:** Uncontrolled loops, lost conversation states, deadlocks, and unpredictable agent transitions in complex multi-step processes.
- **Verification Pattern:**
  - `grep -rnE "(StateGraph|LangGraph|add_node|add_edge|agent_executor|Workflow)" .`

---

### Layer 8: Loop Engineering
- **Definition:** Deterministic verification guardrails, constraint validation loops, corrective regeneration with feedback, and bounded escalation to human reviewers (HITL).
- **Supply Chain Example:** A verifier node inspecting drafted supplier purchase orders for restricted country sanctions or hazardous material handling compliance; if a violation is detected, looping back with a corrective prompt or escalating to the compliance team.
- **Failure Mode Without It:** Critical constraint violations (analogous to administering medicine despite known patient allergies) slipping silently into production outputs.
- **Verification Pattern:**
  - `grep -rnE "(verification_loop|retry_count|human_in_the_loop|human_review|escalat|constraint_check)" .`

---

### Layer 9: Evaluation Engineering
- **Definition:** Repeatable, deterministic benchmark evaluation suites testing regression test cases with explicit expected outcomes, scoring system accuracy and safety across versions.
- **Supply Chain Example:** A golden dataset of 50 historic supply chain disruptions (port closure, supplier insolvency, sudden demand spike) run against candidate prompt/model versions to verify pass rates stay above 95%.
- **Failure Mode Without It:** Silent performance degradation, prompt brittleness, and "whack-a-mole" regressions where fixing one customer edge case breaks five others.
- **Verification Pattern:**
  - `grep -rnE "(test_eval|golden_dataset|evaluation_runner|benchmark|run_eval|pass_rate)" .`

---

### Layer 10: Harness Engineering
- **Definition:** Execution runtime tracing, comprehensive metadata capture (inputs, intermediate steps, tool calls, model outputs, configs), and deterministic replay capabilities.
- **Supply Chain Example:** Capturing full execution telemetry for an autonomous freight booking decision so internal auditors can replay the exact tool calls, tariff tables, and model tokens that produced the booking.
- **Failure Mode Without It:** Inability to debug sporadic production failures, non-reproducible model deviations, and inability to satisfy regulatory audit requirements.
- **Verification Pattern:**
  - `grep -rnE "(trace_run|execution_trace|run_metadata|replay_run|telemetry|logger\.info)" .`

---

### Layer 11: Infrastructure / Production Engineering
- **Definition:** Operational resilience engineering including timeouts, exponential backoff retries, rate-limiting, circuit breakers, sandboxing, and graceful degradation under dependency failure.
- **Supply Chain Example:** When third-party customs EDI or port tracking APIs time out or return 503 errors, the agent falls back to cached transit estimates and queues transactions without crashing the main orchestration pipeline.
- **Failure Mode Without It:** Cascading system outages, thread exhaustion, frozen pipelines, and catastrophic downtime when external APIs suffer transient outages.
- **Verification Pattern:**
  - `grep -rnE "(timeout=|retry_strategy|exponential_backoff|fallback|circuit_breaker|max_retries)" .`

---

### Layer 12: Continual Learning
- **Definition:** Systematic clustering of human feedback, production corrections, and recurring failure modes to propose governed system updates and verified test additions.
- **Supply Chain Example:** Aggregating human dispatcher overrides on autonomous route suggestions to identify recurring weather detour miscalculations, generating a candidate prompt improvement with updated safety thresholds.
- **Failure Mode Without It:** The system repeatedly makes the same mistakes, requiring continuous manual operator intervention with no compounding intelligence.
- **Verification Pattern:**
  - `grep -rnE "(continual_learning|feedback_loop|failure_pattern|cluster_errors|candidate_improvement)" .`
