# /spec — Interactive spec writer for STAMP features

Interview the user to produce a completed `specs/<module>-<feature>.md` from the template at `specs/_template.md`. Ask one question at a time and wait for the answer before asking the next. Do not ask all questions upfront.

## Interview sequence

Ask these questions in order. Adapt follow-up questions based on prior answers — skip questions that are already answered by context.

1. **What does the feature do?**
   Ask for a one-sentence user-facing description (what the user can *do*, written for the CHANGELOG).

2. **Which module does it belong to?**
   Options: `stereo`, `stats`, `plot`, `pipeline`, `io`, or a new module. Explain briefly if it is unclear which fits.

3. **What does the user pass in?**
   Ask about the `data` argument (single-column `pd.DataFrame` from `load()`, a specific result type, raw array?) and any additional parameters.

4. **What does it return?**
   Ask whether an existing result type covers it or a new dataclass is needed. If new, ask what fields it should have.

5. **What is the algorithm or scientific method?**
   Ask for a description of the method and any literature references (author, year, journal).

6. **What parameters does the user control?**
   Ask for each parameter: name, type, default value, and one-line description. Continue until the user says there are no more.

7. **What inputs are invalid?**
   Ask what should raise `ValueError` (hard errors) and what should emit a `UserWarning` (soft warnings).

8. **What are the important edge cases?**
   Prompt with examples: empty array, single value, extreme parameter values. Ask the user what the correct behaviour is for each.

9. **Does this feature need a new notebook?**
   If yes, ask for the notebook's purpose in one sentence and the key sections it should demonstrate.

## After the interview

1. Read `specs/_template.md` to load the template structure.
2. Fill in every section from the answers collected. Do not leave any placeholder text — if a section is not applicable (e.g. no notebook), write "N/A" and note why.
3. Infer the `specs/` filename as `specs/<module>-<feature>.md` from the module and a short slug of the feature name.
4. Show the completed spec to the user as a markdown block and ask: **"Does this look right? Reply with any corrections, or say 'approve' to write the file."**
5. On approval, write the file to `specs/<module>-<feature>.md`. Confirm the path and tell the user the next step: *"Spec saved. When you're ready, say 'start the feature' and I'll enter Plan mode using this spec."*

## Rules

- Ask one question at a time. Never present more than one question in a single message.
- Never write any code or create any files until the user says "approve".
- If the user's answer is ambiguous, ask a clarifying follow-up before moving on.
- Keep questions short — one or two sentences maximum.
- After the user approves, do not enter Plan mode automatically. Wait for an explicit instruction.
