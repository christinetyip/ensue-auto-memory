# ensue-auto-memory vs ensue-memory

This document explains what's new in `ensue-auto-memory` compared to the original `ensue-memory` skill.

## Summary

| Aspect | ensue-memory (original) | ensue-auto-memory (new) |
|--------|------------------------|-------------------------|
| Trigger | Manual ("remember this", "recall") | Automatic (hooks + pattern detection) |
| Retrieval | On-demand via user request | Automatic at session start |
| Saving | On-demand via user request | Automatic when patterns detected |
| Project awareness | None | Auto-detects project from `$CLAUDE_PROJECT_DIR` |
| Key structure | User-defined | Enforced: `@{username}/{category}/{subcategory}` |
| Configuration | None | Environment variables for thresholds/limits |

---

## Architecture Comparison

### Original: ensue-memory

```
ensue-memory-network/
├── .claude-plugin/
│   └── marketplace.json
├── skills/
│   └── ensue-memory/
│       └── SKILL.md          ← All logic lives here
└── README.md
```

**How it worked:**
- Single SKILL.md with instructions
- Claude follows instructions when user triggers with keywords
- No hooks, no scripts
- Relies entirely on Claude recognizing triggers and following instructions

### New: ensue-auto-memory

```
ensue-auto-memory/
├── .claude-plugin/
│   └── marketplace.json
├── hooks/                     ← NEW: Hook-based automation
│   ├── hooks.json
│   └── scripts/
│       ├── session-start.py   ← Automatic retrieval
│       └── user-prompt.py     ← Pattern detection + discovery
├── skills/
│   └── auto-memory/
│       └── SKILL.md           ← In-session behavior + save instructions
└── README.md
```

---

## What's New

### 1. SessionStart Hook (automatic retrieval)

**File:** `hooks/hooks.json` + `hooks/scripts/session-start.py`

**What it does:**
- Runs automatically when Claude Code session starts
- Calls `list_keys` to get all user's keys
- Filters by `@{username}/` prefix
- Loads memories by category with limits:
  - `identity/*` - all
  - `preferences/*` - limit 10 (configurable)
  - `corrections/*` - limit 5 (configurable)
  - `projects/{project-name}/*` - limit 5 (configurable)
- Injects as `systemMessage` context for Claude

**Why:** User doesn't need to ask "what do you know about me?" - context is already there.

```json
// hooks/hooks.json
"SessionStart": [{
  "matcher": "*",
  "hooks": [{
    "type": "command",
    "command": "python3 ${CLAUDE_PLUGIN_ROOT}/hooks/scripts/session-start.py",
    "timeout": 20
  }]
}]
```

---

### 2. UserPromptSubmit Hook (pattern detection + discovery)

**File:** `hooks/hooks.json` + `hooks/scripts/user-prompt.py`

**What it does:**
1. **Pattern detection**: Regex matching for:
   - Preferences: "I prefer", "I always", "I like", "my preferred"
   - Corrections: "no, don't", "stop doing", "that's wrong"
   - Identity: "my name is", "I work at", "I'm a"

2. **Semantic discovery**: For substantive prompts (>20 chars):
   - Calls `discover_memories` with user's prompt as query
   - Filters results by `@{username}/` prefix
   - Filters by relevancy score > 0.7 (configurable)
   - Fetches values for high-relevance keys
   - Injects as additional context

**Why:**
- Automatically prompts Claude to save when preferences/corrections detected
- Surfaces relevant memories based on what user is asking about

```json
// hooks/hooks.json
"UserPromptSubmit": [{
  "matcher": "*",
  "hooks": [{
    "type": "command",
    "command": "python3 ${CLAUDE_PLUGIN_ROOT}/hooks/scripts/user-prompt.py",
    "timeout": 10
  }]
}]
```

---

### 3. Stop Hook (end-of-session save check)

**File:** `hooks/hooks.json`

**What it does:**
- Runs when Claude is about to stop/end session
- Uses **prompt-based hook** (not command)
- Asks Claude to review the conversation for unsaved:
  - Preferences stated
  - Corrections made
  - Project decisions
  - Identity information
- Saves anything significant before session ends

**Why:** Catches learnings that weren't saved during the session (e.g., if session ends abruptly).

```json
// hooks/hooks.json
"Stop": [{
  "matcher": "*",
  "hooks": [{
    "type": "prompt",
    "prompt": "Before ending this session, review the conversation for significant learnings...",
    "timeout": 30
  }]
}]
```

---

### 4. Enforced Key Structure

**Original:** User/Claude decided key names ad-hoc

**New:** Enforced structure in SKILL.md:
```
@{ENSUE_USERNAME}/{category}/{subcategory}

Categories:
- identity/       → name, role, company, timezone
- preferences/    → code style, tools, workflows
- corrections/    → things NOT to do
- projects/{name}/ → project-specific context
```

**Why:** Consistent structure enables automatic filtering and retrieval by category.

---

### 5. Project Awareness

**Original:** No project awareness

**New:** Auto-detects project from `basename($CLAUDE_PROJECT_DIR)`

**How it works:**
- `session-start.py` extracts project name from environment
- Loads `@{username}/projects/{project-name}/*` memories
- SKILL.md instructs Claude to save project decisions under this path

**Why:** Different projects have different context. User doesn't need to specify which project.

---

### 6. Embedding Strategy

**Original:** Not specified

**New:** Explicit in SKILL.md:
```json
{
  "key_name": "@christine/preferences/code-style",
  "description": "Short label",           // Concise
  "value": "Verbose detailed content...", // Rich, semantic
  "embed": true,
  "embed_source": "value"                 // Embed the verbose value
}
```

**Why:** Better semantic search results when `discover_memories` searches over verbose values.

---

### 7. Multi-User Awareness

**Original:** Mentioned but not enforced

**New:** Explicit filtering in both hooks and SKILL.md:
- All API results filtered by `@{username}/` prefix
- SKILL.md explicitly states: "NEVER read, reference, or use memories belonging to other users"

**Why:** Ensue network has multiple users. Must filter to avoid loading others' data.

---

### 8. Configuration via Environment Variables

**Original:** None

**New:**
| Variable | Default | Description |
|----------|---------|-------------|
| `ENSUE_USERNAME` | (required) | Username for key prefixing |
| `ENSUE_API_KEY` | (required) | API key |
| `ENSUE_RELEVANCY_THRESHOLD` | 0.7 | Min score for discovered memories |
| `ENSUE_PROJECT_LIMIT` | 5 | Max project memories at startup |
| `ENSUE_PREFERENCES_LIMIT` | 10 | Max preferences at startup |
| `ENSUE_CORRECTIONS_LIMIT` | 5 | Max corrections at startup |

**Why:** Users can tune behavior without editing code.

---

## What's Preserved from Original

1. **curl-based API calls** - Still uses curl via Bash, not MCP tools
2. **SKILL.md for instructions** - Still the source of truth for Claude's behavior
3. **Same Ensue API** - `create_memory`, `get_memory`, `discover_memories`, etc.
4. **Security guidance** - Never expose API key, never store credentials

---

## File-by-File Summary

| File | Purpose | New vs Modified |
|------|---------|-----------------|
| `hooks/hooks.json` | Defines SessionStart, UserPromptSubmit, Stop hooks | **NEW** |
| `hooks/scripts/session-start.py` | Automatic memory retrieval at session start | **NEW** |
| `hooks/scripts/user-prompt.py` | Pattern detection + semantic discovery | **NEW** |
| `skills/auto-memory/SKILL.md` | In-session save behavior, key structure, guidelines | **MODIFIED** (more structured) |
| `.claude-plugin/marketplace.json` | Plugin metadata | Similar structure |
| `README.md` | Setup instructions | Updated for new features |

---

## Migration Notes

Users of `ensue-memory` can install `ensue-auto-memory` alongside or as replacement:

1. **No data migration needed** - Same Ensue API, same data store
2. **Key structure change** - New memories will use `@{username}/{category}/` structure
3. **Environment variables required** - Must set `ENSUE_USERNAME` (new requirement)
4. **Existing memories still accessible** - Old keys work, new keys follow new structure
