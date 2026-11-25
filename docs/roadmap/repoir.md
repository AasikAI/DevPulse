# RepoIR - Future Feature Idea

**Status:** IDEA - NOT APPROVED - NOT SCHEDULED
**Timing (owner's decision):** to be built only after the complete DevPulse product is built.
**Scope rule:** RepoIR is out of scope for every current phase, including Phase 2. No code, tables, dependencies, UI, permissions, or stubs for it may be added until it has its own approved spec.

## 1. Intent (owner's words)

> We have to provide an additional AI feature called "RepoIR" where the connected GitHub account and repositories' codebase can be onboarded into our application, so that it uses a deterministic parser to analyse the codebase, code files, their dependencies, code-file relationships, and ontology considerations, and presents an IR as a YAML file. That IR can then be used by an LLM to generate an architecture diagram and a knowledge graph, rather than passing the entire codebase to the LLM to analyse and generate the artifact.

## 2. Understanding of the idea (to be confirmed at specification time)

```text
Connected GitHub repository
  -> Onboarding
    -> Deterministic parser (no LLM)
      -> IR (intermediate representation) as a YAML file
        -> LLM consumes the IR, not the full codebase
          -> Architecture diagram
          -> Knowledge graph
```

The core value is that the expensive, non-deterministic LLM step works from a compact, structured, reproducible description of the codebase instead of raw source.

Parser inputs and relationships named by the owner: codebase, code files, dependencies, relationships between code files, and ontology considerations.

## 3. What is deliberately not defined yet

Nothing below is decided. Each item becomes a question for the future requirements stage.

- Supported languages and frameworks
- Parser technology and approach
- IR schema, YAML structure, and versioning
- Ontology: what it is, who defines it, and whether it is fixed or extensible
- Which LLM and provider generate the diagrams and knowledge graph
- Output formats of the architecture diagram and the knowledge graph
- Whether the IR is stored (PostgreSQL, file storage, or generated on demand)
- How a repository is onboarded and re-onboarded when code changes
- Size and repository limits

## 4. Observations against the current approved baseline (not decisions)

These are points where the idea touches existing rules. They must be resolved explicitly, never silently.

| Existing rule | How RepoIR touches it |
|---|---|
| DevPulse is not a repository source-code storage platform | RepoIR must read source code to parse it. Whether code is read transiently or retained anywhere is an open decision, and it may require an explicit change to this principle. |
| GitHub permissions are minimum and any increase needs explicit approval | Reading repository contents likely needs a permission that the earlier phases do not request. This is an approval item, not something to add early. [INFERRED] |
| Credentials, tokens, and secrets must never reach logs, errors, or task arguments | Parsing and onboarding jobs must follow the same rules. Repository secrets that appear in source code must not leak into the IR or to an LLM. [INFERRED] |
| Approved stack lists no LLM or AI components | An LLM provider, and any parsing libraries, are new dependencies and need explicit approval. |
| Neutral, evidence-based language; no developer ranking or productivity scoring | Architecture and knowledge-graph outputs must describe code structure only, never evaluate people. |
| Feature-oriented layered modular monolith | RepoIR would be a new feature module following the same layer rules. Long-running onboarding and parsing would likely need background execution, to be decided in design. [INFERRED] |
| PostgreSQL is the system of record | Where the IR and generated artifacts live must follow, or explicitly amend, this rule. |

Code sent to an LLM, even as an IR, is derived from the user's source code. The privacy and consent implications must be part of the specification.

## 5. Open questions for the future requirements stage

1. Is source code read transiently, cached, or stored? What is retained afterwards?
2. Which repositories can be onboarded: all authorized repositories, selected ones, public only, or private as well?
3. Which languages are supported first, and is the parser one tool or a set of per-language tools?
4. What is the IR? (YAML schema, level of detail, stability guarantees, how versions are handled)
5. What does "ontology consideration" mean concretely: a fixed vocabulary of code concepts, a configurable one, or something else?
6. How is the IR kept fresh as the repository changes?
7. Which LLM and provider will be used, and can the user's code or IR leave DevPulse's infrastructure?
8. Is the YAML shown to or downloadable by the user, or internal only?
9. What are the acceptable outputs for "architecture diagram" and "knowledge graph"?
10. How is the correctness of a deterministic parser verified (golden fixtures, reproducibility tests)?

## 6. How this feature will be delivered

When the owner decides to start it, RepoIR follows the same controlled workflow as every other feature:

1. Intent recorded and open questions answered
2. Phase prompt file, then `spec.md`, assumptions, open questions, BDD feature files, and coverage
3. Requirements approval gate
4. Design, TDD plan, and implementation plan
5. Implementation approval gate
6. One vertical slice at a time using TDD, with a slice review after each

Until then, this file is only a record of intent.
