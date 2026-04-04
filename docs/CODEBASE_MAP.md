# Codebase Map

## Project Stats
- **226 GDScript files** | **82 scenes** | **103 resources** | **689 images** | **24 audio files** | **8 shaders**
- **Engine:** Godot 4.6 (Forward Plus) | **Viewport:** 480x270 scaled to 1280x720
- **Entry point:** `addons/top_down/scenes/ui/screens/boot_load.tscn`

## Addon Architecture (Two Layers)

### Layer 1: `addons/great_games_library/` (56 scripts, game-agnostic)

Reusable engine utilities with no game-specific logic.

| Directory | Contents |
|-----------|----------|
| `autoload/` | Logger, Music, SoundManager, SteamInit |
| `nodes/AreaTransmitter/` | Decoupled data transmission system (6 scripts) |
| `nodes/Navigation/` | Tilemap nav helpers (4 scripts) |
| `nodes/ResourceNode/` | Dictionary-based resource storage on nodes |
| `nodes/RigidCharacterBody2D/` | Physics-based character body |
| `nodes/utility/` | Debug draw, spawn overlap fix, tile helpers (7 scripts) |
| `resources/InstanceResource/` | Scene spawner with object pooling |
| `resources/ReferenceNodeResource/` | Observable node references (4 scripts) |
| `resources/SaveableResource/` | Persistence base classes |
| `resources/SoundResource/` | Sound playback configuration (5 scripts) |
| `resources/ValueResource/` | Typed value wrappers with signals (11 scripts) |
| `static/` | Bitwise, Drawer, GameMath, InverseKinematics, PhysicsHelper, ScenePacker, ThreadUtility, VerletIntegration |

### Layer 2: `addons/top_down/` (140+ scripts, game template)

| Directory | Scripts | Purpose |
|-----------|---------|---------|
| `scripts/actor/` | 10 | Base actor behavior (movement, dash, damage cooldown, sprite flip) |
| `scripts/actor/bots/` | 11 | Enemy AI (targeting, input sim, proximity attack, slime split) |
| `scripts/actor/boss/` | 6 | Big Jelly boss behavior |
| `scripts/actor/player/` | 5 | Player input, camera, hole recovery |
| `scripts/arena/` | 10 | Wave spawning, enemy management, drop system |
| `scripts/damage/` | 10 | Damage processing, health, status effects |
| `scripts/damage/properties/` | 4 | Damage data/type/status resources |
| `scripts/game/` | 11 | Camera, transitions, persistent data, preloading |
| `scripts/input/` | 8 | Input rebinding, control textures |
| `scripts/pickups/` | 8 | Item collection, health/weapon pickups |
| `scripts/ui/` | 16 | Menu management, HUD, boot screen, pause |
| `scripts/weapon_system/` | 8 | Projectile spawning, movement, impact, lifetime |
| `scripts/vfx/` | 1 | After-image effect |

### Editor Plugins
- `addons/kanban_tasks/` — In-editor kanban board (30+ scripts)
- `addons/resource_manager/` — Resource browsing/editing (5 scripts)

## Class Hierarchy

```
SaveableResource
  +-- ValueResource
  |     +-- BoolResource, IntResource, FloatResource
  |     +-- Vector2Resource, StringValueResource
  |     +-- DictionaryResource, StringArrayResource
  |     +-- AstarGridResource, TweenValueResource
  |     +-- TransmissionResource
  +-- ActorStatsResource
  +-- HealthResource
  +-- DamageResource
  +-- ActionResource
  +-- InputResource
  +-- SceneTransitionResource
  +-- SpawnPointResource
  +-- AudioSettingsResource
  +-- GraphicsResource
  +-- ScoreResource
  +-- ItemCollectionResource
  +-- SharedResource
```

## System Interactions

```
Boot Sequence:
  boot_load.tscn -> BootPreloader -> PreloadResource (threaded)
                                  -> PersistentData.saveable_list.load_resource()
                                  -> Transition.change_scene("title")

Scene Flow:
  Title -> [Play] -> room_start -> room_0 (arena)
                                -> Game Over -> Title

Damage Flow:
  Weapon -> ProjectileSpawner -> InstanceResource.instance()
         -> Projectile2D (with AreaTransmitter2D)
         -> overlap AreaReceiver2D on target
         -> DataChannelTransmitter.send() -> TransmissionResource
         -> AreaReceiver2D.receive() -> callback by transmission_name
         -> ActorDamage processes -> HealthResource updated

Spawning Flow:
  EnemyWaveManager -> SpawnWaveList -> EnemySpawner
                   -> InstanceResource.instance(config_callback)
                   -> parent via ReferenceNodeResource
                   -> PoolNode recycles on death
```

## Physics Layers
| Layer | Name | Used By |
|-------|------|---------|
| 1 | Environment | Walls, obstacles |
| 2 | Player | Player actor |
| 3 | Enemy | Enemy actors |
| 4 | Navigation Obstacle | A* pathfinding blockers |

## Audio Buses
Master -> Music (with optional low-pass filter), Sounds

## Autoloads
| Name | Type | Source |
|------|------|--------|
| SteamInit | Script | `great_games_library/autoload/SteamInit.gd` |
| SoundManager | Scene | `top_down/scenes/autoloads/sound_manager.tscn` |
| Music | Scene | `top_down/scenes/autoloads/music.tscn` |
| Transition | Scene | `top_down/scenes/autoloads/transition.tscn` |
| PersistentData | Scene | `top_down/scenes/autoloads/persistent_data.tscn` |

## Resource Instances (103 .tres files)

Key resource directories under `addons/top_down/resources/`:
- `InstanceResources/` — 20 pooled scene configs (actors, pickups, projectiles, vfx)
- `global_resources/` — 10 shared game state resources
- `sounds/` — 15 sound configs
- `tilesets/` — 10 tileset definitions
- `CameraResources/` — 5 camera/shake configs
- `ControlTextureResource/` — 5 input prompt texture sets (gamepad variants + keyboard)
- `arena_resources/` — 6 wave/spawn state resources
- `materials/` — 6 shader materials
- `ParticleProcessMaterial/` — 6 particle configs

## `game/` Directory
Empty template structure mirroring `addons/top_down/` for user's game-specific content. Contains subdirectories for assets, resources, scenes, and scripts but no files yet.
