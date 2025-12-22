# TDD STOP GATE (MANDATORY)

## THE 26-STEP DEVELOPMENT CYCLE

This project follows a **26-step iterative development cycle**. The TDD Stop Gate ensures steps 7-10 (Test-Driven Development) are never skipped.

---

## BEFORE WRITING ANY CODE, YOU MUST:

### Step 1: Output This Confirmation
```
=== TDD STOP GATE ===
Task: [task ID and name]
[x] I have read the task's required reading docs
[x] I have read the task's Test Cases section
[x] I am writing TESTS FIRST (not implementation)
=== PROCEEDING WITH FAILING TESTS ===
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
Task: [task ID and name]
Tests written BEFORE implementation: YES
All tests passing: YES
Coverage: [X]%
=== READY FOR STEPS 24-26 ===
```

### Step 5: Ship & Deploy (Steps 24-26)

**Step 24: Git Commit & Push**
```bash
git add -A
git commit -m "feat(scope): description"
git push
```

**Step 25: Deploy to Test Server**
```bash
docker-compose build
docker-compose up -d
docker-compose logs  # verify no errors
```

**Step 26: Deploy to Production (MANUAL ONLY)**
- ⚠️ NEVER automatic
- Requires explicit user request
- Must pass all tests on test server first

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

## THE FULL 26-STEP CYCLE

| Phase | Steps | Description |
|-------|-------|-------------|
| 2.1 Planning | 1-6 | Validate docs, review code, ask questions |
| 2.2 TDD | 7-10 | Write failing tests, make pass |
| 2.3 Quality | 11-14 | Refactor, error handling, documentation |
| 2.4 Git | 15-18 | Add, commit, push, update board |
| 2.5 Review | 19-23 | Code review, testing review, fix issues |
| 2.6 Ship | 24 | Final commit & push to repository |
| 2.7 Test Deploy | 25 | Docker build, deploy to staging |
| 2.8 Production | 26 | Deploy to production (MANUAL ONLY) |

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

---

## QUICK REFERENCE

```
┌─────────────────────────────────────────────────────┐
│  TDD STOP GATE CHECKLIST                            │
├─────────────────────────────────────────────────────┤
│  □ Output TDD STOP GATE confirmation                │
│  □ Write failing tests from Test Cases section      │
│  □ Run pytest - show failures                       │
│  □ Write minimal code to pass                       │
│  □ Run pytest - show passes                         │
│  □ Output TDD CYCLE COMPLETE confirmation           │
│  □ Git commit + push (Step 24)                      │
│  □ Deploy to test server (Step 25)                  │
│  □ Production deploy (Step 26) - ONLY IF REQUESTED  │
└─────────────────────────────────────────────────────┘
```
