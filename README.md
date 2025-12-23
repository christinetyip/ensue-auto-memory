# Ensue Auto-Memory

Automatic persistent memory for Claude Code sessions. Remembers your preferences, corrections, and project context across sessions.

## Features

- **Automatic retrieval**: Your context is loaded at session start
- **Pattern detection**: Preferences and corrections are detected and saved automatically
- **Project awareness**: Project-specific context is loaded based on your working directory
- **Invisible operation**: Works in the background without manual commands

## Quick Start

### 1. Set Environment Variables

Add to your shell profile (`~/.zshrc`, `~/.bashrc`, etc.):

```bash
export ENSUE_API_KEY="your-api-key-here"
export ENSUE_USERNAME="your-username"
```

Get a free API key at https://www.ensue-network.ai/dashboard so memories are saved to your own (private) network.

Alternatively, use a Guest API key:

```bash
export ENSUE_API_KEY="lmn_af9e0d32ae044e5faf084d957da9b60b"
export ENSUE_USERNAME="your-username"
```

### 2. Start Claude Code

```bash
claude
```

### 3. Install the Plugin

```bash
/plugin marketplace add https://github.com/christinetyip/ensue-auto-memory
```

```bash
/plugin install ensue-auto-memory
```

And restart Claude to load the new plugins.

## How It Works

### At Session Start

While you're using Claude Code, the plugin automatically saves and loads:
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
| `ENSUE_PROJECT_LIMIT` | `5` | Max project memories to load (can be increased for long-running tasks) |
| `ENSUE_PREFERENCES_LIMIT` | `10` | Max preferences to load |
| `ENSUE_CORRECTIONS_LIMIT` | `5` | Max corrections to load |


## Privacy & Security

- Memories are stored on your own Ensue network if you create a new API key at https://www.ensue-network.ai/dashboard
- Memories are stored on a public Ensue network if you use the Guest API key
- Only you and anyone you grant access to can access the memories on your network (set permissions in the dashboard)
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
   /plugin
   ```

3. Restart Claude Code after setting environment variables

## Links

- [Ensue Dashboard](https://www.ensue-network.ai/dashboard)
- [Ensue Documentation](https://www.ensue-network.ai/docs)
- [Ensue Homepage](https://ensue.dev)
