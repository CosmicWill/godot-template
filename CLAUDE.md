# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Godot 4.6 top-down shooter game template. All game code lives under `addons/` to minimize project conflicts. The main scene is `addons/top_down/scenes/ui/screens/boot_load.tscn`.

## Running the Project

Open in Godot 4.6 (Forward Plus renderer). No external build tools — the Godot editor handles building and running. Viewport is 480x270 scaled to 1280x720.

## Architecture

### Two addon layers

- **`addons/great_games_library/`** — Engine-agnostic reusable systems (nodes, resources, static utilities). Game-independent. Contains autoloads, custom nodes, resource types, and static helper classes.
- **`addons/top_down/`** — The actual game template. Contains scenes, scripts, assets, and resources specific to the top-down shooter. Depends on `great_games_library`.

### Autoloads (registered in project.godot)

| Autoload | Purpose |
|---|---|
| `SteamInit` | Steam SDK initialization (great_games_library) |
| `SoundManager` | Manages SoundResource playback via pooled AudioStreamPlayers |
| `Music` | Background music player |
| `Transition` | Scene transitions using screenshot + shader dissolve |
| `PersistentData` | Holds SaveableResource list and arbitrary data dictionary across scenes |

### Key design patterns

**Resource-driven architecture** — Most systems communicate through shared Resource instances rather than direct node references. Key resource types:

- **`ReferenceNodeResource`** — Observable node reference. Nodes call `set_reference(self)` to register; dependents call `listen(inst, callback)` to react to changes. Auto-cleans on tree exit. Used instead of global singletons for things like camera, player, spawn parent.
- **`InstanceResource`** — Scene spawner with object pooling. Stores a `scene_path` (not PackedScene, to avoid cyclic refs) and a `parent_reference_resource`. Call `instance(config_callback)` to spawn. Nodes with a `PoolNode` child get recycled instead of freed.
- **`TransmissionResource`** — Data payload for the AreaTransmitter system. Carries a `transmission_name` (channel key) and an error state. Used for damage, pickups, obstacles.
- **`SaveableResource`** — Base class for persistent data. Override `prepare_save()`, `prepare_load()`, `reset_resource()`. Saves to `user://` as `.tres` files. Has `save_type` for future Steam integration.
- **`ValueResource`** — Extends SaveableResource with an `updated` signal. Subtypes: `BoolResource`, `IntResource`, `FloatResource`, `Vector2Resource`, `StringResource`, etc.
- **`SoundResource`** — Defines how a sound plays (pitch range, volume, retrigger cooldown, pitch escalation). Play via `play(sound_player)` or `play_managed()` through SoundManager.

**AreaTransmitter/AreaReceiver system** — Decoupled data transmission between Area2D nodes. `AreaTransmitter2D` detects overlap with `AreaReceiver2D` and sends data through `DataChannelTransmitter` children. Receivers register callbacks by `transmission_name`. Used for all damage, pickups, and environmental effects.

**ResourceNode** — A node holding a dictionary of resources (keyed by `resource_name`). Attached to actors/entities as a central data store. Systems query it via `get_resource(key)`.

### Boot sequence

`boot_load.tscn` -> `BootPreloader` preloads scenes/materials (threaded via `ThreadUtility`) and loads all SaveableResources, then transitions to the title screen.

### Physics layers

| Layer | Name |
|---|---|
| 1 | Environment |
| 2 | Player |
| 3 | Enemy |
| 4 | Navigation Obstacle |

### Audio bus layout

Must stay at `res://default_bus_layout.tres` (Godot limitation with custom AudioBusLayout paths). Three buses: Master, Music, Sounds.

### Scene organization (addons/top_down/scenes/)

- `actors/` — Player and enemy actors
- `arena/` — Arena/wave spawning
- `autoloads/` — Autoload scenes
- `levels/` — Game rooms/levels
- `projectiles/` — Bullets and projectiles
- `weapons/` — Weapon scenes
- `ui/screens/` — Menu screens (title, pause, game over, boot, control rebinding)
- `vfx/` — Visual effects
- `pickups/` — Collectible items

### Script organization (addons/top_down/scripts/)

Scripts are separated from scenes by domain: `actor/`, `arena/`, `damage/`, `game/`, `input/`, `pickups/`, `triggers/`, `ui/`. Bot AI and player input are under `actor/bots/` and `actor/player/` respectively.

## Conventions

- GDScript with static typing (type hints on variables, parameters, return types)
- `class_name` declarations for reusable types
- Resources use `@export` for editor-configurable properties with `@export_group` for organization
- Scene instancing uses file paths (not PackedScene references) in InstanceResource to avoid cyclic dependencies
- Debug frame-stepping: `P` to pause/advance, `[ + P` to unpause

## Linting & Formatting

gdtoolkit is installed (`pip install "gdtoolkit==4.*"`). Config files: `.gdlintrc`, `.gdformatrc`.

```bash
# Lint all game scripts
python -m gdtoolkit.linter addons/top_down/ addons/great_games_library/

# Lint a single file
python -m gdtoolkit.linter path/to/file.gd

# Format (auto-fix whitespace, formatting)
python -m gdtoolkit.formatter path/to/file.gd

# Check formatting without modifying (CI mode)
python -m gdtoolkit.formatter --check addons/

# Complexity analysis
python -m gdtoolkit.gdradon cc addons/top_down/scripts/
```

Excluded from linting: `.godot/`, `addons/kanban_tasks/`, `addons/resource_manager/`.

## Godot CLI Commands

```bash
# Validate project loads (import all resources, report errors)
godot --headless --path . --import --quit

# Check a single script for parse errors
godot --headless --check-only --script res://path/to/script.gd

# Start headless LSP server (for editor integration on port 6005)
godot --path . --editor --headless --lsp-port 6005

# Run with debug visuals
godot --path . --debug-collisions --debug-navigation

# Log output to file
godot --headless --path . --quit --log-file output.log
```

### Debugger Ports
| Service | Port | Override |
|---|---|---|
| LSP | 6005 | `--lsp-port` |
| DAP | 6006 | `--dap-port` |
| Remote Debug | 6007 | `--debug-server` |

## Editor Plugins

- **Kanban Tasks** — Task/todo board (`kanban_tasks_data.kanban`)
- **Resource Manager** — Resource browsing/editing

## Documentation

- `docs/CODEBASE_MAP.md` — Full codebase inventory (226 scripts, 82 scenes, 103 resources)
- `docs/RESTRUCTURE_PLAN.md` — Proposed professional folder restructuring
- `docs/TOOLING.md` — Detailed linting, formatting, and debugger setup guide
