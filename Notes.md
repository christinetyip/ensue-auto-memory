Final Structure

  ensue-auto-memory/
  ├── .claude-plugin/
  │   └── marketplace.json      # Plugin metadata
  ├── hooks/
  │   ├── hooks.json            # Hook configuration
  │   └── scripts/
  │       ├── session-start.py  # Loads memories at session start
  │       └── user-prompt.py    # Detects patterns & discovers relevant memories
  ├── skills/
  │   └── auto-memory/
  │       └── SKILL.md          # In-session behavior instructions
  └── README.md                 # Setup instructions

  How It Works

  | Hook             | When              | What It Does                                                        |
  |------------------|-------------------|---------------------------------------------------------------------|
  | SessionStart     | Session begins    | Loads identity, preferences, corrections, project context           |
  | UserPromptSubmit | Each user message | Detects preference/correction patterns, discovers relevant memories |
  | Stop             | Session ends      | Prompt-based check to save any unsaved learnings                    |

  Key Features

  1. Automatic loading: No manual retrieval needed
  2. Pattern detection: Saves when user says "I prefer...", "don't do...", etc.
  3. Semantic discovery: After each prompt, finds relevant memories based on context
  4. Project awareness: Uses basename($CLAUDE_PROJECT_DIR) for project-specific memories
  5. Configurable: Thresholds and limits via environment variables

  To Test

  # Set environment variables
  export ENSUE_API_KEY="lmn_391a21877c0b46d0a49f43651f336856"
  export ENSUE_USERNAME="christine"

  # Test the session-start script directly
  python3 /Users/christine/projects/claude-skill/ensue-auto-memory/hooks/scripts/session-start.py# Ensue Auto-Memory

Quick Summary for the Engineer

  What's New (TL;DR)

  | Component                      | What It Does                                                                   |
  |--------------------------------|--------------------------------------------------------------------------------|
  | hooks/hooks.json               | Defines 3 hooks: SessionStart, UserPromptSubmit, Stop                          |
  | hooks/scripts/session-start.py | Auto-loads memories at session start (no user action needed)                   |
  | hooks/scripts/user-prompt.py   | Detects "I prefer..." patterns + runs discover_memories on each prompt         |
  | hooks.json → Stop hook         | Prompt-based hook that asks Claude to save learnings before session ends       |
  | SKILL.md                       | More structured: enforced key naming, embedding strategy, multi-user filtering |

  The Key Shift

  Before (ensue-memory):
  User: "remember my preferred stack is React"
  Claude: [follows SKILL.md instructions to call API]

  After (ensue-auto-memory):
  [Session starts]
  → SessionStart hook runs session-start.py
  → Memories automatically loaded as context

  User: "I prefer early returns"
  → UserPromptSubmit hook detects pattern
  → Claude prompted to save automatically

  [Session ends]
  → Stop hook checks for unsaved learnings

  The document includes detailed explanations of each new file, the hook configurations, and what's preserved from the original.