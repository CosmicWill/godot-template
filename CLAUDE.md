# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Godot 4.6 top-down shooter game template with a three-tier architecture: `core/` (engine utilities), `systems/` (reusable game systems), `game/` (game-specific content). The main scene is `game/screens/boot_load.tscn`.

## Running the Project

Open in Godot 4.6 (Forward Plus renderer). No external build tools — the Godot editor handles building and running. Viewport is 480x270 scaled to 1280x720.

## Architecture

### Three-tier structure

- **`core/`** — Engine-agnostic reusable utilities (nodes, resources, static helpers). Game-independent. Any project can use these.
- **`systems/`** — Reusable game systems (actor, damage, weapons, pickups, arena, camera, input, transition, UI). Genre-specific but not game-specific. Scripts are co-located with their scenes.
- **`game/`** — Game-specific content (specific enemies, weapons, levels, screens, resources, autoloads). Content that would change between different games using the same systems.
- **`assets/`** — All raw media (images, music, sounds, shaders) at project root.
- **`addons/`** — True editor plugins only (Kanban Tasks, Resource Manager).

### Autoloads (registered in project.godot)

| Autoload | Path | Purpose |
|---|---|---|
| `SteamInit` | `core/autoload/SteamInit.gd` | Steam SDK initialization |
| `SoundManager` | `game/autoloads/sound_manager.tscn` | Manages SoundResource playback via pooled AudioStreamPlayers |
| `Music` | `game/autoloads/music.tscn` | Background music player |
| `Transition` | `game/autoloads/transition.tscn` | Scene transitions using screenshot + shader dissolve |
| `PersistentData` | `game/autoloads/persistent_data.tscn` | Holds SaveableResource list and arbitrary data dictionary across scenes |

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

`game/screens/boot_load.tscn` -> `BootPreloader` preloads scenes/materials (threaded via `ThreadUtility`) and loads all SaveableResources, then transitions to the title screen.

### Physics layers

| Layer | Name |
|---|---|
| 1 | Environment |
| 2 | Player |
| 3 | Enemy |
| 4 | Navigation Obstacle |

### Audio bus layout

Must stay at `res://default_bus_layout.tres` (Godot limitation with custom AudioBusLayout paths). Three buses: Master, Music, Sounds.

### Directory layout

```
core/                           # Engine utilities (was great_games_library)
├── autoload/                   # Logger, Music, SoundManager, SteamInit
├── nodes/                      # AreaTransmitter, Navigation, ResourceNode, etc.
├── resources/                  # InstanceResource, SaveableResource, ValueResource, etc.
└── static/                     # GameMath, PhysicsHelper, ThreadUtility, etc.

systems/                        # Reusable game systems
├── actor/                      # actor.tscn + MoverTopDown2D, DashAbility, etc.
├── damage/                     # ActorDamage, HealthResource + properties/
├── weapons/                    # weapon.tscn + WeaponManager + projectile/
├── pickups/                    # pickup.tscn + ItemPickup, ItemResource
├── arena/                      # arena_entry.tscn, enemy_manager.tscn + spawning
├── camera/                     # main_camera.tscn + CameraFollow2D
├── input/                      # binding_button.tscn + ActionResource, BindingMenu
├── transition/                 # TransitionManager + transition.gdshader
├── obstacles/                  # block_wall, door, hole_obstacle
├── ui/                         # menu_button.tscn, audio_slider.tscn + ButtonAnimation
├── vfx/                        # AfterImageVFX, ParticleStarter
├── game/                       # GameOverDetect, ProcessingComponent, PreloadResource
├── triggers/                   # TriggerSceneChanger
├── tile_layers/                # floor_layer.tscn, obstacle_layer.tscn
├── screen_effects/             # screen_effects.tscn
└── room_template/              # room_template.tscn

game/                           # Game-specific content
├── actors/                     # player/, enemies/ (zombie, slime, boss), ai/
├── weapons/                    # gun/, shotgun/, assault_rifle/, sword/ + projectiles/
├── levels/                     # room_0.tscn, room_start.tscn
├── pickups/                    # coin_pickup, health_pickup, item_pickup
├── vfx/                        # Explosions, death animations, particles
├── screens/                    # boot_load, title, pause, game_over, control_rebinding
├── hud/                        # game_hud.tscn, HealthPanel, UiWeaponInventory
├── resources/                  # All .tres instances by domain
├── autoloads/                  # sound_manager, music, persistent_data, transition
├── scripts/                    # GameEnums, MusicSetter, PersistentData, PlayerSpawner
└── ui/                         # Screen-specific UI scripts

assets/                         # All raw media
├── images/                     # Characters, GUI, items, tilesets, VFX, weapons
├── music/                      # Background music files
├── sounds/                     # Sound effect files
└── shaders/                    # All .gdshader files

addons/                         # True editor plugins only
├── kanban_tasks/               # Task/todo board
└── resource_manager/           # Resource browsing/editing
```

## Conventions

- GDScript with static typing (type hints on variables, parameters, return types)
- `class_name` declarations for reusable types
- Resources use `@export` for editor-configurable properties with `@export_group` for organization
- Scene instancing uses file paths (not PackedScene references) in InstanceResource to avoid cyclic dependencies
- Scripts are co-located with their scenes (no parallel scripts/ vs scenes/ trees)
- Debug frame-stepping: `P` to pause/advance, `[ + P` to unpause

## Linting & Formatting

gdtoolkit is installed (`pip install "gdtoolkit==4.*"`). Config files: `.gdlintrc`, `.gdformatrc`.

```bash
# Lint all game scripts
python -m gdtoolkit.linter core/ systems/ game/

# Lint a single file
python -m gdtoolkit.linter path/to/file.gd

# Format (auto-fix whitespace, formatting)
python -m gdtoolkit.formatter path/to/file.gd

# Check formatting without modifying (CI mode)
python -m gdtoolkit.formatter --check core/ systems/ game/

# Complexity analysis
python -m gdtoolkit.gdradon cc systems/ game/
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

- `docs/CODEBASE_MAP.md` — Full codebase inventory
- `docs/RESTRUCTURE_PLAN.md` — Original restructure plan (now implemented)
- `docs/TOOLING.md` — Detailed linting, formatting, and debugger setup guide
- `docs/design_document/` — Game design document (Obsidian)
