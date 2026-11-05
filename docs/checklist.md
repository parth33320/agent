# 12-Layer Production Agent Readiness Checklist

This checklist contains 12 binary (Yes/No) questions that can be answered by scanning a repository codebase to evaluate its maturity against Miriam Miradi's 12-layer production agent framework.

---

### [ ] Layer 1: Business Understanding
**Question:** Does the codebase define explicit decision boundaries, business rules, or formal decision scope statements that limit what decisions the agent is permitted to make?
- *Verification check:* Look for policy engine rules, decision boundary configs, or decision scope definitions (`decision_scope`, `business_rules`, `policy_engine`, `success_criteria`).

---

### [ ] Layer 2: Data Understanding
**Question:** Does the codebase perform automated data completeness, schema validation, and missing-field checks before feeding input data to the agent or decision model?
- *Verification check:* Look for input validation functions, missing field detections, or schema checkers (`data_completeness`, `check_missing_fields`, `field_availability`, `pydantic` validators).

---

### [ ] Layer 3: Knowledge Engineering
**Question:** Does the codebase ingest, chunk, embed, or index domain knowledge into structured stores, vector databases, or knowledge graphs accessible via retrieval tools?
- *Verification check:* Look for document ingestion pipelines, vector store integrations, embeddings, or knowledge graph definitions (`vector_store`, `embeddings`, `knowledge_graph`, `chunking`).

---

### [ ] Layer 4: Context Engineering
**Question:** Does the codebase dynamically assemble differentiated context bundles tailored to specific request categories or tasks rather than injecting monolithic state?
- *Verification check:* Look for context assembly routines, differentiated context extractors, or selective context bundling logic (`context_bundle`, `context_builder`, `assemble_context`, `differentiated_context`).

---

### [ ] Layer 5: Model Engineering
**Question:** Does the codebase define distinct, task-specific model profiles, roles, temperatures, or system prompts for different operational tasks?
- *Verification check:* Look for task-to-model mapping configs, model profile dictionaries, or distinct model parameter settings per role (`model_profile`, `model_tier`, `temperature=`, `system_prompt`).

---

### [ ] Layer 6: Semantic Engineering
**Question:** Does the codebase implement domain-specific concept resolution, synonym mapping, or abbreviation disambiguation prior to retrieval and reasoning?
- *Verification check:* Look for concept resolution functions, abbreviation dictionaries, or semantic normalization tables (`resolve_concept`, `semantic_resolution`, `domain_ontology`, `abbreviation_map`).

---

### [ ] Layer 7: Agent Engineering
**Question:** Does the codebase employ stateful orchestration graphs (such as LangGraph, StateGraph, or explicit state machines) with deterministic routing transitions between agent nodes?
- *Verification check:* Look for graph node/edge definitions, agent executors, or multi-agent state machines (`StateGraph`, `LangGraph`, `add_node`, `add_edge`, `agent_executor`).

---

### [ ] Layer 8: Loop Engineering
**Question:** Does the codebase implement constraint verification loops that evaluate generated outputs, trigger corrective regeneration upon violation, and escalate to human review when needed?
- *Verification check:* Look for verification loops, constraint checks, retry iterations, or human escalation routing (`verification_loop`, `human_in_the_loop`, `escalat`, `constraint_check`).

---

### [ ] Layer 9: Evaluation Engineering
**Question:** Does the codebase include a repeatable automated evaluation suite with golden benchmark cases and explicit pass/fail assertions to guard against regressions?
- *Verification check:* Look for golden test datasets, evaluation test runners, or pass rate assertions (`test_eval`, `golden_dataset`, `evaluation_runner`, `benchmark`, `run_eval`).

---

### [ ] Layer 10: Harness Engineering
**Question:** Does the codebase capture full execution runtime traces (inputs, intermediate states, tool calls, model responses) with the capability to replay or inspect historic runs?
- *Verification check:* Look for run tracers, execution metadata persistence, replay utilities, or structured run logging (`trace_run`, `execution_trace`, `run_metadata`, `replay_run`).

---

### [ ] Layer 11: Infrastructure / Production Engineering
**Question:** Does the codebase implement operational resilience mechanisms such as timeouts, exponential backoff retries, fallbacks, or circuit breakers for external API dependencies?
- *Verification check:* Look for network timeouts, retry decorators/configs, fallback responses, or circuit breaker patterns (`timeout=`, `retry_strategy`, `exponential_backoff`, `fallback`, `max_retries`).

---

### [ ] Layer 12: Continual Learning
**Question:** Does the codebase provide mechanisms to log human feedback or corrections, cluster recurring failure patterns, and suggest candidate system improvements?
- *Verification check:* Look for feedback capture handlers, error pattern clustering, or candidate improvement logging (`continual_learning`, `feedback_loop`, `failure_pattern`, `candidate_improvement`).
