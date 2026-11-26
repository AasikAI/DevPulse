---
description: "Turn a plain-words intent into one spec.md (technical spec, scenarios, acceptance criteria). Writes the spec only; no plan, no code."
agent: agent
---

# Intent to spec

Turn the developer's intent (the text that follows this prompt) into one file: `specs/<feature-slug>/spec.md`.

## Do this

1. Read `.github/copilot-instructions.md` and `specs/_template/spec.md`. Skim the existing code only as far as needed to avoid contradicting it (existing modules, naming, data already stored).
2. Write `specs/<feature-slug>/spec.md` using the template sections. Use a short kebab-case slug.
3. Stop. Tell the developer what you wrote, list the open questions that need an answer, and wait.

## Rules

- Copy the intent verbatim into section 1. Do not rewrite or improve it.
- Keep the whole spec short. Plain words, no filler.
- Split the work: put the smallest end-to-end working version under **MVP** and everything else under **Later**.
- Describe what and why, not code. No class names, SQL, or file-by-file design. Copilot makes the plan in a later step.
- Respect the architecture and security rules in `.github/copilot-instructions.md`. The database stays between GitHub and the UI.
- Write 5 to 12 scenarios in Given/When/Then: the happy path first, then the failures, ownership, and security cases that matter. No more than needed.
- Write acceptance criteria as a checklist the developer can tick during review.
- **Do not guess.** If something is unclear, put it in **Open questions** with 2 to 4 options and the trade-off. Do not choose for the developer. Put anything you had to assume in **Assumptions**.
- Do not create any other file (no separate feature files, assumption files, or coverage files). Do not write a plan. Do not write code.
- Do not mention phases or phase numbers.

## Your final message

- The path of the spec file.
- Three to five lines summarising the MVP.
- The open questions, numbered, so the developer can answer them in one reply.

Then wait for the developer's review.
