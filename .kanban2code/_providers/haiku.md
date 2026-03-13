---
cli: claude
model: claude-haiku-4-5
unattended_flags:
  - '--dangerously-skip-permissions'
output_flags:
  - '--output-format'
  - json
prompt_style: flag
safety:
  max_turns: 20
  max_budget_usd: 2
provider: anthropic
---

