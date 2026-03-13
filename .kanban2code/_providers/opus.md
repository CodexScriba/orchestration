---
cli: claude
model: claude-opus-4-6
unattended_flags:
  - '--dangerously-skip-permissions'
output_flags:
  - '--output-format'
  - json
prompt_style: flag
safety:
  max_turns: 20
  max_budget_usd: 5
provider: anthropic
---

