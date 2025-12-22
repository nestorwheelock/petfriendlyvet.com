# TDD STOP GATE (MANDATORY)

## BEFORE WRITING ANY CODE, YOU MUST:

### Step 1: Output This Confirmation
```
=== TDD STOP GATE ===
Task: [task ID and name]
[ ] I have read CODING_STANDARDS.md
[ ] I have read the task's Test Cases section
[ ] I am about to write TESTS FIRST (not implementation)
=== PROCEEDING WITH TESTS ===
```

### Step 2: Write Failing Tests
- Create test files based on task's Test Cases section
- Run pytest and SHOW THE FAILING OUTPUT
- Confirm tests fail for the right reasons (code doesn't exist yet)

### Step 3: Only THEN Write Implementation
- Write minimal code to make ONE test pass
- Run tests again
- Repeat until all tests pass

### Step 4: Output Completion Confirmation
```
=== TDD CYCLE COMPLETE ===
Tests written BEFORE implementation: YES
All tests passing: YES
Coverage: [X]%
=== READY FOR GIT COMMIT ===
```

---

## WHY THIS EXISTS

Claude has repeatedly skipped TDD despite:
- Reminders in every user story
- Reminders in every task file
- Reminders in CODING_STANDARDS.md
- Reminders in CLAUDE.md

This stop gate forces explicit acknowledgment that cannot be skipped.

## ENFORCEMENT

If Claude writes implementation code WITHOUT first:
1. Outputting the TDD STOP GATE confirmation
2. Writing and running failing tests
3. Showing the test failure output

Then the work is INVALID and must be redone.

---

## CHECKLIST FOR TASK FILES

Add this to the TOP of every task file:

```markdown
> **STOP! READ THIS FIRST:**
> Before writing ANY code, complete the [TDD STOP GATE](../TDD_STOP_GATE.md)
>
> You must output the confirmation block and write failing tests
> BEFORE any implementation code.
```
