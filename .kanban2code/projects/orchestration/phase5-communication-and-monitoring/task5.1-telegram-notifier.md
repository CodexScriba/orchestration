---
stage: plan
tags: [feature, p1]
agent: planner
contexts: [skills/python-core-skills]
---

# Task 5.1: Telegram notifier

## Goal

Implement the Telegram notification system for stage changes and escalations.

## Definition of Done

- [ ] Sends Telegram message on every stage change
- [ ] Includes: task ID, stage transition, account used, model/provider used
- [ ] Sends on blocked/stalled/escalated states with reason
- [ ] Bot token and chat ID loaded from config (not hardcoded)
- [ ] Graceful failure: notification errors do not block execution

## Files

- `src/orchestrator/notifier.py` - create - Telegram notification delivery

## Tests

- [ ] Notification sent on stage change (mocked Telegram API)
- [ ] Notification includes required fields
- [ ] Notification failure does not raise or block the run
- [ ] Bot token and chat ID loaded from config

## Context

Phase 5: Communication and Monitoring
