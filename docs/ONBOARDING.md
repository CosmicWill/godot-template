# Game Developer Onboarding Guide

Welcome to the Godot 4.6 Top-Down Shooter Template. This guide walks you through the major systems, design patterns, and workflows you need to understand before contributing.

---

## 1. Project Architecture

The codebase uses a **three-tier architecture** that separates reusable engine code from game-specific content.

```
core/       Game-engine utilities. Any Godot project can use these.
systems/    Reusable game systems (actor, weapons, damage, arena, etc.).
            Genre-specific but not tied to any single game.
game/       Game-specific content — enemies, weapons, levels, screens, resources.
            This is what changes between different games built on the same systems.
assets/     Raw media (images, music, sounds, shaders).
addons/     Editor plugins only (Kanban Tasks, Resource Manager).
```

**Rule of thumb:** If you're adding something any top-down game could use, it goes in `systems/`. If it's specific to this game (a particular enemy, a specific weapon), it goes in `game/`. If it's engine-level and genre-agnostic (math helpers, node utilities), it goes in `core/`.

Scripts are **co-located with their scenes** — no separate `scripts/` vs `scenes/` trees within `core/` or `systems/`.

---

## 2. Resource-Driven Architecture

This is the most important pattern in the project. **Systems communicate through shared Resource instances**, not direct node references or signals between distant nodes.

### Why Resources?

- Resources are **shared by reference** in Godot. Multiple nodes can hold the same `.tres` file and all see the same data.
- This decouples systems — a health bar doesn't need a reference to the player, it just reads from the same `HealthResource`.
- Resources survive scene changes when held by autoloads (`PersistentData`).

### Key Resource Types

| Resource | Location | Purpose |
|---|---|---|
| `ReferenceNodeResource` | `core/resources/` | Observable node reference. A node calls `set_reference(self)` to register; dependents call `listen(inst, callback)` to react. Auto-cleans on tree exit. Replaces global singletons for camera, player, spawn parent, etc. |
| `InstanceResource` | `core/resources/` | Scene spawner with **object pooling**. Stores a file path (not PackedScene — avoids cyclic refs). Call `instance(config_callback)` to spawn. Nodes with a `PoolNode` child get recycled instead of freed. |
| `ValueResource` | `core/resources/` | Base class with an `updated` signal. Subtypes: `BoolResource`, `IntResource`, `FloatResource`, `Vector2Resource`, `StringResource`, `DictionaryResource`, etc. Used for reactive game state. |
| `SaveableResource` | `core/resources/` | Base class for persistent data. Override `prepare_save()`, `prepare_load()`, `reset_resource()`. Saves to `user://` as `.tres` files. |
| `TransmissionResource` | `core/nodes/AreaTransmitter/` | Data payload for the AreaTransmitter system. Carries a `transmission_name` (channel key) and an error state. Used for damage, pickups, obstacles. |
| `SoundResource` | `core/resources/` | Defines how a sound plays — pitch range, volume, retrigger cooldown, pitch escalation. Play via `play(sound_player)` or `play_managed()` through the SoundManager autoload. |

### ResourceNode — The Entity Data Store

`ResourceNode` is a node that holds a **dictionary of resources** keyed by `resource_name`. It's attached to actors and entities as a central data store.

```gdscript
# Systems query it by key:
var health: HealthResource = resource_node.get_resource("health")
var input: InputResource = resource_node.get_resource("input")
var stats: ActorStatsResource = resource_node.get_resource("movement")
```

This is how different systems on the same entity communicate without direct references to each other. The `Weapon` reads from `resource_node.get_resource("damage")`, the `MoverTopDown2D` reads from `resource_node.get_resource("input")` and `resource_node.get_resource("movement")`, etc.

### Practical Example: Adding a New Stat

1. Create a new `ValueResource` subtype (e.g., `FloatResource`) as a `.tres` file in `game/resources/`.
2. Add it to the actor's `ResourceNode` in the scene editor (add a `ResourceNodeItem` entry with a `resource_name` key).
3. Any system script on that actor can now call `resource_node.get_resource("your_key")`.

---

## 3. The AreaTransmitter System (Damage, Pickups, Effects)

All damage, item pickups, and environmental effects use a **decoupled area-based data transmission system** rather than direct method calls.

### How It Works

```
AreaTransmitter2D (Area2D)      AreaReceiver2D (Area2D)
  └─ DataChannelTransmitter       registered callbacks by transmission_name
       └─ TransmissionResource
```

1. An `AreaTransmitter2D` detects overlap with an `AreaReceiver2D`.
2. It iterates its child `DataChannelTransmitter` nodes and calls `send(receiver)`.
3. Each `DataChannelTransmitter` duplicates its `TransmissionResource` and passes it to the receiver.
4. The `AreaReceiver2D` looks up its callback dictionary by `transmission_name` and invokes it.
5. If no callback matches, the transmission is marked as failed.

### Why This Pattern?

- A projectile doesn't need to know what it's hitting — it just transmits data.
- A receiver can handle multiple transmission types (damage, status effects, knockback) by registering multiple callbacks.
- The `DataChannelTransmitter` handles retry logic (`TRY_AGAIN` state) and emits `success`/`failed`/`denied` signals for VFX and sound reactions.

### Practical Example: Adding a New Damage Type

1. Create a new `TransmissionResource` `.tres` with a unique `transmission_name` (e.g., `"fire_damage"`).
2. Add a `DataChannelTransmitter` child to your `AreaTransmitter2D` and assign the resource.
3. On the target's `AreaReceiver2D`, call `add_receiver("fire_damage", your_callback)` in `_ready()`.

---

## 4. Actor System

Actors (player, enemies) are built from **composable nodes** on a shared `actor.tscn` base in `systems/actor/`.

### Core Actor Components

| Component | Purpose |
|---|---|
| `MoverTopDown2D` | Physics movement with acceleration, impulse, and overlap resolution. Reads from `InputResource` and `ActorStatsResource` via `ResourceNode`. |
| `SpriteFlip` | Flips sprite based on movement direction. |
| `DashAbility` | Dash movement with cooldown. |
| `DamageCooldown` | Invulnerability frames after taking damage. |
| `VisualInvulnerability` | Flashing effect during invulnerability. |
| `ItemDrop` | Spawns drops on death. |
| `CharacterState` | State tracking for the actor. |

### Player vs Enemy

- **Player** (`game/actors/player/`): `PlayerInput` reads real input and writes to `InputResource`. Additional scripts: `CameraPositionSetter`, `HoleRecovery`, `SafeTileTracker`, `PlayerJuice`.
- **Enemies** (`game/actors/ai/`): `BotInput` simulates input by writing to the same `InputResource`. AI scripts like `TargetFinder`, `TargetDirection`, `TargetAim`, and `ProximityAttack` drive behavior. The movement system doesn't care whether input comes from a human or an AI.

### Adding a New Enemy

1. Create a new scene inheriting or duplicating from an existing enemy in `game/actors/enemies/`.
2. Configure its `ResourceNode` with appropriate stats, health, input, and damage resources.
3. Create an `InstanceResource` `.tres` in `game/resources/actors/` pointing to the scene.
4. Add it to a `SpawnWaveList` for the arena system.

---

## 5. Weapon & Projectile System

Weapons live in `systems/weapons/` and are managed by the `WeaponManager`.

### Weapon Architecture

```
WeaponManager (manages weapon inventory, switching)
  └─ Weapon (Node2D — visibility, collision mask, damage data)
       └─ WeaponRotation (aims toward input direction)
       └─ WeaponTrigger (fires on input action)
       └─ ProjectileSpawner (uses InstanceResource to spawn projectiles)
       └─ WeaponKickback (recoil impulse)
       └─ SpreadShot (angle spread for shotguns)
```

### Projectile Architecture

```
Projectile2D (base projectile node)
  └─ ProjectileMover (velocity-based movement)
  └─ ProjectileLifetime (auto-destroy timer)
  └─ ProjectileImpact (VFX on hit)
  └─ ProjectileRotation (face movement direction)
  └─ ProjectileSetup (configures collision mask and damage)
  └─ HitLimit (destroy after N hits)
  └─ AreaTransmitter2D + DataChannelTransmitter (sends damage)
```

### Adding a New Weapon

1. Create a new weapon scene in `game/weapons/` with a `Weapon` root node.
2. Add `WeaponRotation`, `WeaponTrigger`, `ProjectileSpawner`, etc. as children.
3. Create a projectile scene with `Projectile2D` and the components you need.
4. Create `InstanceResource` `.tres` files for the projectile in `game/resources/weapons/`.
5. Create a `WeaponItemResource` and add it to the weapon inventory/database.

---

## 6. Arena & Wave Spawning

The arena system in `systems/arena/` manages enemy waves.

### Flow

```
ArenaStarter (triggers fight mode)
  → fight_mode_resource (BoolResource) set to true
  → EnemyWaveManager reads wave count, tracks enemy count
  → EnemyManager → EnemySpawner
    → InstanceResource.instance(config_callback)
    → enemies spawned via ReferenceNodeResource parent
  → All enemies dead → next wave
  → All waves done → fight_mode_resource set to false
  → ArenaDoorBlock opens
```

Key resources drive the state:
- `fight_mode_resource` (BoolResource) — toggles arena combat mode
- `enemy_count_resource` (IntResource) — remaining enemies in current wave
- `remaining_wave_count_resource` (IntResource) — waves left
- `wave_number_resource` (IntResource) — current wave index

### Adding a New Arena Room

1. Use `systems/room_template/room_template.tscn` as a base.
2. Place `SpawnPoint` nodes where enemies should appear.
3. Configure `SpawnWaveList` resources defining which enemies spawn and in what order.
4. Add an `ArenaStarter` trigger and `ArenaDoorBlock` obstacles.

---

## 7. Scene Flow & Transitions

### Boot Sequence

```
boot_load.tscn
  → BootPreloader
    → Preloads scenes/materials via ThreadUtility (threaded loading)
    → Loads all SaveableResources from PersistentData.saveable_list
    → Transition.change_scene("title")
```

### Scene Transition System

`TransitionManager` (the `Transition` autoload) creates a smooth dissolve effect:

1. Captures a screenshot of the current viewport.
2. Displays it as a `TextureRect` over the scene.
3. Loads the next scene on a background thread.
4. Animates a shader dissolve from the screenshot to the new scene.

Call it from anywhere: `Transition.change_scene("res://game/screens/title.tscn")`

### Screen Scenes

| Scene | Purpose |
|---|---|
| `boot_load.tscn` | Initial loading, preloads assets |
| `title.tscn` | Main menu |
| `pause.tscn` | Pause overlay |
| `game_over.tscn` | Death screen |
| `control_rebinding.tscn` | Input remapping UI |

---

## 8. Autoloads (Global Singletons)

| Autoload | Purpose | Usage |
|---|---|---|
| `SteamInit` | Steam SDK initialization | Called automatically at startup |
| `SoundManager` | Pooled `AudioStreamPlayer` management | `sound_resource.play_managed()` |
| `Music` | Background music player | Set track via `MusicSetter` component |
| `Transition` | Scene transitions with dissolve shader | `Transition.change_scene(path)` |
| `PersistentData` | Holds `SaveableResource` list and arbitrary data dictionary | Survives scene changes, handles save/load |

---

## 9. Audio System

### SoundResource

Each sound effect is defined as a `SoundResource` `.tres` file with:
- `pitch_min` / `pitch_max` — random pitch variation
- `volume` — playback volume in dB
- `retrigger_time` — minimum time between plays (prevents stacking)
- `pitch_add` / `pitch_cooldown` — pitch escalation on rapid triggers (satisfying for combos)

**Playing sounds:**
```gdscript
# Through a dedicated SoundPlayer node on the same entity:
sound_resource.play(sound_player)

# Through the global SoundManager (pooled, fire-and-forget):
sound_resource.play_managed()
```

### Audio Buses

Three buses: **Master** → **Music**, **Sounds**. The bus layout must stay at `res://default_bus_layout.tres` (Godot limitation).

---

## 10. Save System

`SaveableResource` is the base class for all persistent data.

### How Saves Work

1. Resources that need persistence extend `SaveableResource`.
2. They're added to `PersistentData.saveable_list` in the editor.
3. On boot, `BootPreloader` calls `load_resource()` on each.
4. On save, each resource serializes to `user://resource_name.tres`.

### Implementing a New Saveable

```gdscript
class_name MyGameState
extends SaveableResource

@export var high_score: int = 0

func prepare_save() -> Resource:
    var data = duplicate()
    return data

func prepare_load(data: Resource) -> void:
    high_score = data.high_score

func reset_resource() -> void:
    high_score = 0
```

---

## 11. Physics Layers

| Layer | Name | Used By |
|---|---|---|
| 1 | Environment | Walls, obstacles, floor boundaries |
| 2 | Player | Player's CharacterBody2D and hitbox |
| 3 | Enemy | Enemy CharacterBody2Ds and hitboxes |
| 4 | Navigation Obstacle | A* pathfinding blockers |

Weapons set their projectile `collision_mask` based on who they belong to — player weapons collide with layer 3 (Enemy), enemy attacks collide with layer 2 (Player).

---

## 12. Object Pooling

The `InstanceResource` system includes built-in object pooling via `PoolNode`.

### How It Works

1. Add a `PoolNode` child to any scene that gets spawned frequently (projectiles, VFX, pickups).
2. When the node should be "destroyed," call its `PoolNode` to signal recycling.
3. `InstanceResource` removes it from the scene tree and stores it in `pool_list`.
4. Next `instance()` call pulls from the pool instead of calling `scene.instantiate()`.

This is critical for projectiles and particle effects that spawn hundreds of times per second.

---

## 13. Input System

### ActionResource & InputResource

- `ActionResource` wraps Godot's input actions with rebinding support.
- `InputResource` stores the current input state (axis, actions) and is placed in the actor's `ResourceNode`.
- `PlayerInput` reads real input → writes to `InputResource`.
- `BotInput` / AI scripts write to the same `InputResource` for enemies.
- `BindingMenu` provides the UI for remapping controls at runtime.

### Control Textures

`ControlTextureResource` maps input actions to display textures for different controllers (Xbox, PlayStation, Switch, keyboard). Used by UI prompts.

---

## 14. Development Workflow

### Running the Project

Open in Godot 4.6 editor and press F5. No external build tools needed.

### Linting & Formatting

```bash
# Lint all scripts
python -m gdtoolkit.linter core/ systems/ game/

# Format a file
python -m gdtoolkit.formatter path/to/file.gd

# Check formatting without modifying
python -m gdtoolkit.formatter --check core/ systems/ game/
```

### Debugging

- `P` to pause/advance frame-by-frame, `[ + P` to unpause.
- `godot --path . --debug-collisions --debug-navigation` for visual debugging.
- LSP on port 6005, DAP on port 6006, Remote Debug on port 6007.

### Coding Conventions

- **Static typing** — type hints on all variables, parameters, and return types.
- **`class_name`** — declared on all reusable types.
- **`@export`** with **`@export_group`** — for editor-configurable properties.
- **File paths over PackedScene** — `InstanceResource` uses `scene_path: String` to avoid cyclic dependencies.

---

## 15. Common Tasks Quick Reference

| Task | Where to Look |
|---|---|
| Add a new enemy | `game/actors/enemies/`, create `InstanceResource` in `game/resources/actors/` |
| Add a new weapon | `game/weapons/`, create projectile + `InstanceResource` in `game/resources/weapons/` |
| Add a new pickup | `game/pickups/`, `systems/pickups/`, create `InstanceResource` in `game/resources/pickups/` |
| Add a new sound | Create `SoundResource` `.tres` in `game/resources/sounds/`, put audio in `assets/sounds/` |
| Add a new level | `game/levels/`, base on `systems/room_template/room_template.tscn` |
| Add a new screen | `game/screens/`, wire into scene flow via `Transition.change_scene()` |
| Add persistent data | Extend `SaveableResource`, add to `PersistentData.saveable_list` |
| Add a new UI element | `game/hud/` for in-game UI, `game/ui/` for menu screens |
| Modify arena waves | Edit `SpawnWaveList` resources, configure `EnemyWaveManager` |

---

## 16. Architecture Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                        game/                                │
│  Specific enemies, weapons, levels, screens, resources      │
│  Uses systems/ and core/ — never the other way around       │
├─────────────────────────────────────────────────────────────┤
│                       systems/                              │
│  actor, weapons, damage, arena, camera, input, pickups,     │
│  transition, obstacles, UI, VFX, triggers                   │
│  Uses core/ — never game/                                   │
├─────────────────────────────────────────────────────────────┤
│                        core/                                │
│  ReferenceNodeResource, InstanceResource, SaveableResource, │
│  ValueResource, AreaTransmitter, ResourceNode, SoundResource│
│  ThreadUtility, GameMath, PhysicsHelper                     │
│  No dependencies on systems/ or game/                       │
└─────────────────────────────────────────────────────────────┘
```

**Dependency rule:** `game/` → `systems/` → `core/`. Never upward.
