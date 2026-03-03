# Durak Architecture Refactoring Plan

This plan is designed to keep the project modular, clean, non-duplicative, and logically consistent while deciding the right long-term architecture for Turkish NLP.

## North Star

- Build a reliable Turkish NLP toolkit that is easy to use from Python.
- Keep core linguistic behavior deterministic and reproducible.
- Minimize duplication across Rust, Python, resources, docs, and CLI.
- Preserve performance where it matters without over-engineering early.

## 10x Engineering Guardrails (Anti-God-Object)

These rules apply to every phase and PR.

- [ ] No god objects: each module/class has one primary responsibility.
- [ ] Keep `src/lib.rs` and `python/durak/pipeline.py` as composition layers, not logic dumps.
- [ ] Enforce one-direction dependencies: API/CLI -> pipeline -> domain modules -> backend adapters -> resources.
- [ ] Domain modules must not import CLI or presentation concerns.
- [ ] Define module ownership and boundaries before adding features.
- [ ] Prefer small cohesive files over large mixed-purpose files.
- [ ] Require each feature to declare entry point, owned module, data contract, and tests.
- [ ] Avoid side-by-side duplicate implementations without parity tests.
- [ ] Any temporary duplication must include a removal issue and deadline.
- [ ] Public API changes require deprecation notes and migration examples.

### Structural Constraints

- [ ] Add and enforce file/module budget warnings (example: soft limit for large files).
- [ ] Split by capability, not by utility dumping (`utils` growth requires ADR justification).
- [ ] Keep data models centralized; avoid re-defining token/doc schemas across layers.
- [ ] Keep resource parsing centralized in one provider per backend.
- [ ] Add architecture checks in CI (import boundaries, forbidden dependencies).

## Architecture Recommendation (Realistic)

- Keep a **hybrid architecture**: Rust as the system/performance layer, Python as the public interface and orchestration layer.
- Add a **reference pure-Python path** for correctness/testing and broader compatibility.
- Use one API contract so users do not care which backend executes.

Why this recommendation:

- Pure Python only: simpler contributor story, but harder to sustain high throughput on large corpora.
- Rust only: high performance, but slows experimentation and raises integration cost.
- Hybrid with strict boundaries gives both speed and usability, and matches current codebase direction.

## Phase 0 - Baseline Alignment (Docs/Metadata)

### Checklist

- [x] Update `README.md` license badge/text to MIT (match `LICENSE` and `pyproject.toml`).
- [x] Remove stale custom license references from `pyproject.toml` comments.
- [x] Ensure README version and release references align with `0.4.0`.
- [x] Document CLI usage (`durak` command) in README.
- [x] Update quickstart to promote `Pipeline` path over deprecated examples.

### Exit Criteria

- [x] No contradictions between README, changelog, license file, and package metadata.

## Phase 1 - Stabilization Gate

### Checklist

- [x] Fix Rust compile blocker (`dictionary` unresolved references in `src/lib.rs`).
- [x] Add or update tests for normalization/tokenization/lemmatization pipeline outputs.
- [x] Create regression fixtures (golden outputs) for representative Turkish samples.
- [x] Run `cargo check` and Python test suite in CI as required checks.

### Exit Criteria

- [x] Build passes consistently.
- [x] Baseline behavior is frozen with tests before refactor.

### Current Iteration Status (2026-03-02)

- [x] `cargo check` passes after compile blocker fix.
- [x] `pytest -q` passes (`174` passed, `3` skipped).
- [x] CLI subprocess import path failures resolved in test harness.
- [x] Lemmatizer over-stripping regressions resolved.
- [x] Vowel harmony progressive-form edge case resolved.
- [x] Golden regression fixtures added and covered by pytest.
- [x] CI workflow now includes explicit `cargo check` + Python tests.

## Phase 2 - Module Boundaries and Contracts

### Checklist

- [x] Define explicit interfaces for: normalizer, tokenizer, lemmatizer, cleaner, resource provider.
- [x] Create shared data models (`Token`, `Doc`, analysis payloads) in Python core package.
- [x] Keep public API stable while moving internals behind interfaces.
- [x] Decide fate of `ProcessingContext` (integrate fully or remove).
- [x] Split composition from implementation so pipeline only orchestrates stages.
- [x] Keep stage logic in dedicated modules only.
- [ ] Keep PyO3 export surface thin and move linguistics/rules/caches to internal Rust modules.

### Exit Criteria

- [ ] Every major component has one clear entry point and one clear contract.
- [ ] No mixed concerns (resource loading + business logic + API glue) in the same module.

### Current Iteration Status (2026-03-02)

- [x] Added `python/durak/core/` with explicit internal contracts and shared models.
- [x] Added centralized `python/durak/resources_provider.py`.
- [x] Routed `stopwords` metadata loading and `suffixes` loading through central provider.
- [x] Added provider regression tests and kept API behavior stable.
- [x] Moved pipeline stage registry to dedicated `python/durak/stages.py`.
- [x] Integrated `ProcessingContext` into pipeline via `run_with_context` and `process_text_with_context`.
- [x] Extracted Rust suffix inventory into `src/suffix_inventory.rs` to reduce `src/lib.rs` responsibility.
- [x] Current validation: `pytest -q` -> `182 passed, 3 skipped`.
- [ ] Next remaining Phase 2 work: keep shrinking mixed concerns in Rust core and complete Phase 2 exit criteria.

## Phase 3 - De-duplication Pass

### Checklist

- [x] Consolidate suffix inventories to one source of truth.
- [x] Unify resource loading (prefer one provider abstraction; avoid direct scattered file reads).
- [x] Remove tokenizer behavior drift between Rust and Python implementations.
- [x] Refactor CLI duplicated flows into shared helper pipeline.
- [x] Eliminate per-token re-instantiation hotspots (e.g., stopword manager in loops).

### Exit Criteria

- [x] No critical linguistic rule is defined in multiple places without synchronization.

### Current Iteration Status (2026-03-02)

- [x] CLI process/tokenize flow de-duplicated via shared helpers.
- [x] Stopword manager re-instantiation hotspot removed in CLI token filtering path.
- [x] Morphotactic slot classification now sources suffix groups from `src/suffix_inventory.rs`.
- [x] Apostrophe tokens now load via centralized resource provider.
- [x] Added tokenizer parity tests (`regex` vs `rust`) and default `auto` strategy.
- [x] Added `docs/RULE_OWNERSHIP.md` to document canonical linguistic/resource sources.
- [x] Marked `resources/tr/config/lemma_suffixes.txt` as non-canonical reference-only.
- [x] Current validation: `pytest -q` -> `189 passed, 3 skipped`.
- [x] Phase 3 checklist and exit criteria complete.

## Phase 4 - Backend Strategy (Hybrid, Not Fragmented)

### Checklist

- [x] Implement backend abstraction (`rust`, `python`) under same Python API.
- [x] Provide deterministic parity tests between backends.
- [x] Mark backend capability matrix (what each backend supports).
- [x] Keep fallback behavior explicit when Rust extension is unavailable.

### Exit Criteria

- [x] Users can switch backend without changing app code.
- [x] Output differences are measured and documented.

### Current Iteration Status (2026-03-02)

- [x] Added high-level `DurakController` control layer with `auto/rust/python` backend selection.
- [x] Added explicit backend capability matrix and resolver API.
- [x] Added backend parity and capability tests.
- [x] Added `docs/BACKENDS.md` and linked from README docs section.
- [x] Current validation: `pytest -q` -> `195 passed, 3 skipped`.
- [x] Phase 4 checklist and exit criteria complete.

## Phase 5 - Turkish NLP Feature Expansion (ROI-first)

### Checklist

- [x] Prioritize high-impact features with benchmarks before implementation.
- [ ] Morpheme-aware tokenization improvements.
- [ ] Robust Turkish casing and clitic normalization (`de/da`, `ki`, `mi`).
- [ ] Programmatic inflection utility (rule-based suffix attachment).
- [ ] Corpus quality analyzers (language noise, encoding anomalies, morphological validity scores).
- [ ] Dedup tooling (exact + fuzzy) for large corpus preprocessing.

### Exit Criteria

- [ ] Every added feature has benchmark, test fixtures, and documented expected behavior.

### Current Iteration Status (2026-03-02)

- [x] Phase 5 started.
- [x] Added long/diverse E2E corpus fixture (`32` cases; clean + noisy mixes).
- [x] Added end-to-end analysis tests covering deterministic behavior, suffix attachment, stopword filtering, and backend tokenization parity.
- [x] Made detached-suffix attachment conservative by default to prevent false merges (`ben de`/quote artifacts).
- [x] Added strict canonical gold-output E2E fixture + tests for exact pipeline outputs on critical scenarios.
- [x] Added aggregate quality gate with measurable reduction target (`>=5%` stopword reduction; current run `8.97%`).
- [x] Full gate validation green: `cargo check` + `pytest -q`.
- [ ] Next Phase 5 implementation target: morpheme-aware tokenization design + benchmark harness.

## Phase 6 - Performance and Scalability (Only After Feature Stability)

### Checklist

- [ ] Benchmark hotspots with real Turkish corpora before introducing complex infra.
- [ ] Introduce advanced techniques only if profiling justifies them.
- [ ] FST/morph automata for specific bottlenecks.
- [ ] Streaming/lazy processing for large datasets.
- [ ] Zero-copy columnar interop only if boundary overhead is proven significant.
- [ ] Publish reproducibility strategy (pipeline hash/versioned resources).

### Exit Criteria

- [ ] Performance work is data-driven, not speculative.

## Governance and Operating Rules

### Checklist

- [ ] Add architecture decision records (ADRs) for major choices.
- [ ] Enforce docs/API/version consistency checks in CI.
- [ ] Define deprecation policy with version windows.
- [ ] Keep one canonical resource format and one canonical loading path.
- [ ] Require ADR for any new cross-cutting module or framework addition.
- [ ] Add PR template checks for anti-god-object and module boundary compliance.

### Exit Criteria

- [ ] Future drift is caught automatically before release.

## Suggested Execution Order

1. Phase 0 -> Phase 1 (immediately).
2. Phase 2 -> Phase 3 (modularity and dedup foundation).
3. Phase 4 (backend abstraction and parity).
4. Phase 5 (feature growth).
5. Phase 6 (scaling optimizations only when justified by benchmarks).

## Tail Roadmap - Gemini Suggestions (Gated After Prior Phases)

This section is intentionally at the tail. Start only after Phases 0-4 are complete and parity/consistency is proven.

### Gate to Start Tail Work

- [x] Docs/metadata consistency complete.
- [x] Core build/tests stable.
- [x] Module boundaries clean and deduplication complete.
- [x] Backend parity tests and capability matrix in place.

### Tail A - High-ROI Turkish NLP Features

- [ ] Build morpheme-boundary-aware tokenizer improvements with design doc, benchmark target, ablation tests, and rollback plan.
- [ ] Build dynamic suffixation/inflection engine with deterministic ruleset, exceptions model, and fixture suite.
- [ ] Harden Turkish casing + clitic normalization (`I/ı`, `İ/i`, `de/da`, `ki`, `mi`) with noisy-corpus accuracy benchmarks and error taxonomy.

### Tail B - NLP/LLM Research Automation

- [ ] Build corpus quality report toolkit covering non-Turkishness signals, encoding issues, and morphology validity scoring.
- [ ] Pipeline hashing for deterministic preprocessing lineage.
- [ ] Exact and fuzzy dedup pipeline for large-scale corpora.
- [ ] Hallucination-risk diagnostics tied to tokenization/morph boundaries (experimental).

### Tail C - Efficiency and Scalability (Only if Profiled Need Exists)

- [ ] Evaluate FST-based morphology path with explicit success metrics.
- [ ] Evaluate streaming/lazy execution mode for large dataset workflows.
- [ ] Evaluate zero-copy columnar interop only if boundary-copy cost is measurable and material.
- [ ] For each optimization: require before/after benchmark and complexity budget.

### Tail Exit Criteria

- [ ] Ensure each adopted Gemini-inspired feature has benchmark evidence, deterministic tests, docs, and ownership.
- [ ] No new architectural debt or module boundary violations introduced.
