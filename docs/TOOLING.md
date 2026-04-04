# Development Tooling

## GDScript Linting (gdtoolkit)

### Installation
```bash
pip install "gdtoolkit==4.*"
# or with pipx (isolated, recommended)
pipx install "gdtoolkit==4.*"
```

This provides four commands: `gdlint`, `gdformat`, `gdparse`, `gdradon`.

### Linting
```bash
# Lint a single file
gdlint addons/top_down/scripts/actor/MoverTopDown2D.gd

# Lint entire project
gdlint addons/

# Lint with specific config
gdlint --config .gdlintrc addons/
```

### Formatting
```bash
# Format a file in-place
gdformat addons/top_down/scripts/actor/MoverTopDown2D.gd

# Check formatting without modifying (CI mode, exit code 1 if changes needed)
gdformat --check addons/

# Show diff of what would change
gdformat --diff addons/top_down/scripts/
```

### Complexity Analysis
```bash
# Cyclomatic complexity report
gdradon cc addons/top_down/scripts/
```

### Configuration

Generate default `.gdlintrc` at project root:
```bash
gdlint --dump-default-config > .gdlintrc
```

Key settings in `.gdlintrc`:
```yaml
class-name: "([A-Z][a-z0-9]*)+"
function-name: "(_on_([A-Z][a-z0-9]*)+(_[a-z0-9]+)*|_?[a-z][a-z0-9]*(_[a-z0-9]+)*)"
signal-name: "[a-z][a-z0-9]*(_[a-z0-9]+)*"
max-line-length: 100
max-file-lines: 1000
function-arguments-number: 10
max-public-methods: 20
excluded_directories: [".git", ".godot", "addons/kanban_tasks", "addons/resource_manager"]
```

### Inline Suppression
```gdscript
# gdlint: ignore=function-name, unused-argument
func SomeFunc(unused):
    pass

# gdlint: disable=function-name
func BadName(): pass
# gdlint: enable=function-name
```

### GDQuest Formatter (Alternative, faster)
Rust-based, much faster than gdtoolkit's gdformat:
```bash
# Windows via Scoop
scoop install extras/gdscript-formatter

# Usage
gdscript-formatter addons/top_down/scripts/
gdscript-formatter --check addons/     # CI mode
```

---

## Godot CLI Error Checking

### Validate a single script
```bash
godot --headless --check-only --script res://path/to/script.gd
```
Exit code 0 = no parse errors.

### Import & scan entire project
```bash
godot --headless --path . --import --quit
```
Reports warnings and errors for all resources/scenes to stdout.

### Run and quit (catches initialization errors)
```bash
godot --headless --path . --quit
```

### Verbose mode
```bash
godot --headless --path . --verbose --quit
```

### Log to file
```bash
godot --headless --path . --quit --log-file output.log
```

---

## Godot Debugger Connections

### Ports (defaults)
| Service | Port | Override Flag |
|---------|------|---------------|
| LSP (Language Server) | 6005 | `--lsp-port` |
| DAP (Debug Adapter) | 6006 | `--dap-port` |
| Remote Debug | 6007 | `--debug-server` |

### Headless LSP Server
Run Godot as a pure LSP server (no window) for editor integration:
```bash
godot --path . --editor --headless --lsp-port 6005
```

Provides: completions, diagnostics (errors/warnings), go-to-definition, hover, rename, symbols.

### VS Code Integration

**Required extension:** `geequlim.godot-tools` (Godot Tools)

**settings.json:**
```json
{
    "godotTools.editorPath.godot4": "path/to/godot",
    "godotTools.lsp.serverHost": "127.0.0.1",
    "godotTools.lsp.serverPort": 6005,
    "godotTools.lsp.headless": true
}
```

**launch.json (debugging):**
```json
{
    "version": "0.2.0",
    "configurations": [
        {
            "name": "Launch Godot",
            "type": "godot",
            "request": "launch",
            "address": "127.0.0.1",
            "port": 6007,
            "project": "${workspaceFolder}"
        },
        {
            "name": "Attach to Godot",
            "type": "godot",
            "request": "attach",
            "address": "127.0.0.1",
            "port": 6007
        }
    ]
}
```

### DAP Capabilities
Godot's Debug Adapter supports: breakpoints, step in/over/out, variable inspection, evaluate expressions, hover evaluation, restart, terminate.

### Debug CLI Flags Reference
```
-d, --debug                  Local stdout debugger
--profiling                  Enable script profiler
--gpu-profile                GPU task profiling
--gpu-validation             Graphics API validation layers
--debug-collisions           Show collision shapes at runtime
--debug-navigation           Show nav polygons at runtime
--debug-avoidance            Show avoidance debug visuals
--debug-canvas-item-redraw   Show canvas redraw rectangles
--log-file <path>            Redirect output to file
-v, --verbose                Verbose stdout
```

---

## Quick Reference Commands

```bash
# Lint all game scripts
gdlint addons/top_down/ addons/great_games_library/

# Format all game scripts
gdformat addons/top_down/ addons/great_games_library/

# Check formatting (CI)
gdformat --check addons/

# Validate project loads
godot --headless --path . --import --quit

# Start headless LSP for editor
godot --path . --editor --headless --lsp-port 6005

# Run game with debug visuals
godot --path . --debug-collisions --debug-navigation

# Run with profiler
godot --path . -d --profiling
```
