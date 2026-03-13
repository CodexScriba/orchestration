# Orchestration + Kanban2Code Notes

This file captures the current understanding of how to orchestrate Kanban2Code task execution reliably, what failed in prior attempts, and what architecture choices are most likely to work in practice.

---

# 1. What Kanban2Code Is

Kanban2Code is a staged task system built around Markdown task files with YAML frontmatter.

Core stages:
- `inbox`
- `plan`
- `code`
- `audit`
- `completed`

Core execution agents:
- `planner`
- `coder`
- `auditor`

Meta/orchestration agents may also exist:
- `roadmapper`
- `architect`
- `splitter`
- `conversational`

For execution work, the important loop is:

`plan -> code -> audit -> completed`

If audit fails:

`audit -> code -> audit`

with a hard bounce limit.

---

# 2. Where the Truth Lives

## Task frontmatter is the source of truth

The task file frontmatter should remain authoritative for:
- `stage`
- `agent`
- `bounces`
- `tags`
- `contexts`
- `created`

Do **not** create a second state system that tries to replace those values.

## Supplemental orchestration state is still useful

A separate orchestration state file can exist, but only for metadata that frontmatter should not hold.

Examples of valid orchestrator-only metadata:
- queue order
- session active/inactive
- cron enabled/disabled
- current account used
- last action timestamp
- spawn tool/model used
- stale/escalated flags

This should be treated as supplemental state only.

---

# 3. Why a Pure Prompt/Skill Approach Failed Repeatedly

The major failure mode observed was not lack of understanding. It was failure to execute tightly.

Observed pattern:
1. A stage completed.
2. The assistant reported what happened.
3. The next step was described.
4. But the next step was not actually started.
5. The pipeline stalled.

This happened repeatedly at boundaries such as:
- planner finished but task file was not updated
- code finished but audit was not launched
- audit failed but coder retry was not launched
- audit passed but commit was not executed

### Key lesson
A conversational agent is good at:
- summarizing state
- understanding policies
- choosing a next action

A conversational agent is **not reliably enough** a state machine by itself.

For this reason, orchestration should be implemented as code, not as vibes.

---

# 4. What the Execution Engine Must Do

A reliable orchestrator needs to behave like a deterministic queue runner.

Minimum capabilities:
- read tasks from folder(s) or explicit file list
- resolve a strict ordered queue
- inspect current task frontmatter
- select the correct stage runtime
- spawn the stage runtime
- detect success/failure from file state and output
- immediately continue to the next required stage
- stop on defined escalation conditions
- write machine-readable run state
- expose logs/status summaries

This should not depend on the operator remembering the next step.

---

# 5. Recommended Architecture

## Best split

### Python orchestrator = execution engine
Use Python for:
- queue resolution
- stage dispatch
- retries
- bounce limits
- timeouts
- commit steps
- status files
- Telegram notifications/hooks
- cron or systemd integration

### Skill/config layer = policy layer
Use a skill or config layer for:
- model routing
- account rotation rules
- prompt assembly rules
- reporting format
- commit message templates
- escalation policy

This is a cleaner split than trying to make a chat agent itself be the orchestrator.

---

# 6. Model Routing Lessons

The intended home setup evolved into the following routing preferences.

## Planning
Preferred:
- Gemini Flash 3.x
  - tested names included:
    - `gemini-3-flash-preview`

Fallback:
- Qwen CLI with Kimi K2.5
  - verified working path:
    - `qwen -m kimi-k2.5 -p "Say exactly: hi"`

Important note:
- model naming matters a lot
- `gemini-3-flash-preview` worked, while incorrect `gemini-3.0-*` names caused confusion

## Coding
Preferred:
- Codex CLI
- model:
  - `gpt-5.4`
- reasoning:
  - `medium`

Working command pattern:
```bash
codex exec -m "gpt-5.4" -c model_reasoning_effort="medium" "<prompt>"
```

Fallback:
- Claude Sonnet

## Auditing
Preferred:
- Claude Opus

Fallback:
- Codex `gpt-5.4` high reasoning

Working fallback pattern:
```bash
codex exec -m "gpt-5.4" -c model_reasoning_effort="high" "<prompt>"
```

---

# 7. Account Rotation / Key Rotation

Codex account rotation is useful when many accounts exist and rate limits need to be spread.

A practical pattern:
- rotate **once per task**, not per stage
- keep the same account through bounces for that task
- verify login after switching
- if account fails, try next in round-robin
- if all fail, escalate

Example current Codex account pool observed:
- personal
- work
- home
- karlas
- estela
- annual
- LanguageLine

Switching pattern:
```bash
ln -sf ~/.codex/accounts/TARGET.json ~/.codex/auth.json
echo "TARGET" > ~/.codex/current
codex login status
```

Important correction:
- active auth path should be `~/.codex/auth.json`
- **not** `~/.codex/accounts/auth.json`

Claude rotation was not solidly defined in the home setup and should be treated separately unless a real switch command exists.

---

# 8. Prompt Assembly Rules

This is critical.

The orchestrator must assemble prompts itself.

## Never do this
- send placeholders like `[PASTE FULL CONTENT OF ...]`
- summarize role files in a way that drops stage constraints
- rely on UI-only “copy XML” workflows

## Do this instead
For each stage prompt, inject the actual file contents directly:
1. role file
2. ai-guide.md
3. task file
4. any explicitly required context files

This matters because if the role instructions are weakened, the model may:
- start coding during planning
- skip audit handoff behavior
- omit required task-file sections
- break the pipeline

---

# 9. Planner, Coder, Auditor Differences

## Planner
In the observed setup, planner often returned updated task markdown that then had to be written back manually by the orchestrator.

That caused friction.

Better option:
- let planner edit the task file directly when possible
- then inspect if needed

Why this matters:
- fewer steps
- fewer token-wasting handoffs
- less chance of “planner finished but task file never updated”

## Coder
Coder is usually safe to run as a real repo-editing agent.

Expected result:
- code files changed
- tests run
- task file updated to `stage: audit`, `agent: auditor`
- `## Audit` section written

## Auditor
Auditor must:
- review implementation
- write review section
- decide accepted vs needs work
- on accepted, task goes to `completed`
- on failed audit, task goes back to `code`

---

# 10. Bounce Tracking

This is one of the most important controls.

Recommended rule:
- max failed audit cycles per task = **2**

Meaning:
- first failed audit -> back to code
- second failed audit -> back to code
- third audit cycle should not continue automatically; stop and escalate

This prevents runaway loops.

---

# 11. Commit Rules

A passed audit should not just sit there.

## Rule
If audit is accepted:
- commit immediately

## Safe commit pattern
Only stage:
- files listed in `## Audit`
- task file
- architecture file if changed by auditor

Never:
- `git add .`
- `git add -A`
- commit with merge conflicts
- auto-retry failed commit blindly

Suggested commit message pattern:
```bash
git commit -m "feat(task-id): short description from task title

Audited: rating/10 by AUDIT_MODEL
Files: N files changed
Bounces: N

Co-Authored-By: kanban2claw <noreply@openclaw.dev>"
```

---

# 12. Reporting Style

The most effective reporting style turned out to be short, one-line, structured event messages.

Examples:
- `[SWITCH] personal -> work`
- `[PLAN:START] task4.1 | model: gemini-3-flash-preview | account: karlas`
- `[PLAN:DONE] task4.1 | stage: plan -> code`
- `[CODE:START] task4.1 | model: gpt-5.4-medium | account: karlas`
- `[CODE:DONE] task4.1 | stage: code -> audit`
- `[AUDIT:PASS] task4.1 | rating: 8/10 | -> completed`
- `[COMMIT] task4.1 | hash: abc1234`

This is better than long narration during execution.

---

# 13. Cron / Watchdog Lessons

Several cron/watchdog ideas were explored.

## Weak version (bad)
A watchdog that only says:
- task stale
- next action should be X

Problem:
- it consumes tokens
- but does not actually move work forward

## Better version
A cron or scheduled wake-up should trigger a **full resume protocol**, not just status reporting.

That means when it wakes up, it should:
1. read orchestration instructions
2. read current state
3. inspect current task frontmatter
4. detect exact next required step
5. execute that step
6. report what it did

This is much better than a small “watchdog only” behavior.

## Best version
In practice, a true Python/state-machine runner is still better than cron-driven conversational recovery.

Cron is useful for:
- monitoring
- resume nudges
- Telegram notifications

But it should not be the primary execution engine if determinism is required.

---

# 14. Recommended State Files

For a real runner, the following are useful:
- request file (`run-request.json`)
- run state (`state.json` or `runs/<run-id>.json`)
- structured logs (`jsonl`)
- summary markdown
- optional human handoff file

A single `orchestration-state.json` can still be useful for lightweight orchestration metadata, but a richer Python runner state model is stronger.

---

# 15. What Was Learned from the Python Orchestrator in Downloads

The Python orchestrator under:
- `/home/cynicus/Downloads/orchestrator/`

is a better execution engine than the purely skill-based approach.

Why:
- explicit `run / status / continue`
- real config file
- real logs
- explicit retry policy
- queue resolution built into code
- less dependent on chat behavior

That makes it suitable as:
- the actual execution engine

while `kanban2claw` is better suited as:
- policy/config/operator layer

---

# 16. Suggested Final Home Architecture

## Recommended split

### Execution engine
Python orchestrator
- queue resolution
- stage transitions
- retries
- timeouts
- commits
- status files
- hooks/notifications

### Policy layer
kanban2claw skill/config
- model routing
- fallback order
- account rotation rules
- reporting format
- first-contact protocol
- commit rules
- cron/resume policy if still desired

This gives you:
- deterministic execution
- flexible model policy
- easier editing of home-specific behavior

---

# 17. First Contact Protocol (Recommended)

When `kanban2claw` is explicitly invoked, the first-contact protocol should run before any work starts.

Required steps:
1. Ensure there is a real task queue.
2. Build or refresh orchestration state.
3. Ensure the cron/resume hook exists if that mode is enabled.
4. Confirm the cron is active.
5. Select the first runnable task.
6. Switch required account(s).
7. Report ready state.
8. Only then begin execution.

If any step fails:
- stop
- report blocked
- do not start task execution

---

# 18. Biggest Operational Lessons

1. **Task frontmatter must remain source of truth.**
2. **Prompt assembly must use real file contents.**
3. **Audit bounce limits are essential.**
4. **Accepted audits must commit immediately.**
5. **One-line structured reporting works best during execution.**
6. **Cron that only reports is mostly wasted tokens.**
7. **A Python runner is better than a conversational agent for strict orchestration.**
8. **Model policy and execution engine should be separated.**
9. **Planner direct file editing is better than returning text for later application when safe.**
10. **The orchestrator must think in complete loops, not just next-step descriptions.**

---

# 19. Practical Recommendation

If building this repo further, the best path is:

1. Use the Python runner as the real orchestrator.
2. Move home-specific model/account policy into editable config.
3. Keep Kanban2Code task files authoritative.
4. Use Telegram notifications/hooks for status.
5. Treat skill logic as policy guidance, not execution control.

That will be significantly more reliable than asking a chat agent to be a perfect queue runner.
