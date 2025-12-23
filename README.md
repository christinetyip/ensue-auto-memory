# Ensue Auto-Memory

Automatic persistent memory for Claude Code sessions. Remembers your preferences, corrections, and project context across sessions without manual intervention.

## Features

- **Automatic retrieval**: Your context is loaded at session start
- **Pattern detection**: Preferences and corrections are detected and saved automatically
- **Project awareness**: Project-specific context is loaded based on your working directory
- **Invisible operation**: Works in the background without manual commands

## Quick Start

### 1. Install the Plugin

```bash
# Add the marketplace (if not already added)
/plugin marketplace add https://github.com/mutable-state-inc/ensue-auto-memory

# Install the plugin
/plugin install ensue-auto-memory
```

### 2. Set Environment Variables

Add to your shell profile (`~/.zshrc`, `~/.bashrc`, etc.):

```bash
export ENSUE_API_KEY="your-api-key-here"
export ENSUE_USERNAME="your-username"
```

Get an API key at https://www.ensue-network.ai/dashboard

### 3. Restart Claude Code

```bash
# Exit and restart to load the plugin
claude
```

## How It Works

### At Session Start

The plugin automatically loads:
- Your identity (name, role, etc.)
- Your preferences (code style, tools, workflows)
- Your corrections (things you've told Claude NOT to do)
- Project-specific context (based on current directory)

### During Sessions

When you express preferences or make corrections, they're automatically saved:

```
You: "I prefer early returns over nested conditionals"
→ Saved to @yourname/preferences/code-style

You: "No, don't add emojis to commit messages"
→ Saved to @yourname/corrections/no-emojis

You: "We're using JWT for authentication in this project"
→ Saved to @yourname/projects/my-api/auth
```

### At Session End

A final check ensures any significant learnings are saved before the session ends.

## Memory Categories

| Category | What's Stored | Example Key |
|----------|---------------|-------------|
| `identity/` | Name, role, company, timezone | `@you/identity/role` |
| `preferences/` | Code style, tools, workflows | `@you/preferences/testing` |
| `corrections/` | Things NOT to do | `@you/corrections/no-emojis` |
| `projects/{name}/` | Project-specific context | `@you/projects/api/stack` |

## Configuration

Optional environment variables to customize behavior:

| Variable | Default | Description |
|----------|---------|-------------|
| `ENSUE_RELEVANCY_THRESHOLD` | `0.7` | Minimum score for discovered memories (0-1) |
| `ENSUE_PROJECT_LIMIT` | `5` | Max project memories to load |
| `ENSUE_PREFERENCES_LIMIT` | `10` | Max preferences to load |
| `ENSUE_CORRECTIONS_LIMIT` | `5` | Max corrections to load |

## Requirements

- Python 3.7+
- Claude Code CLI
- Ensue API key

## Privacy & Security

- Memories are stored in your Ensue account
- Only you can access your memories (keys prefixed with your username)
- API keys are never logged or exposed
- Don't store credentials or secrets in memories

## Troubleshooting

### Memories not loading?

1. Verify environment variables are set:
   ```bash
   echo $ENSUE_API_KEY
   echo $ENSUE_USERNAME
   ```

2. Check plugin is installed:
   ```bash
   /plugins
   ```

3. Restart Claude Code after setting environment variables

### Hook not running?

Run Claude Code in debug mode:
```bash
claude --debug
```

## Links

- [Ensue Dashboard](https://www.ensue-network.ai/dashboard)
- [Ensue Documentation](https://www.ensue-network.ai/docs)
- [Ensue Homepage](https://ensue.dev)
