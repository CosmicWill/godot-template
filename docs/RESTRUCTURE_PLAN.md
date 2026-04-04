# Folder Restructure Plan

Normative principles (industry, software engineering, Godot): see [`STANDARDS.md`](STANDARDS.md).

## Current Problems

1. **Everything in `addons/`** — Game template code lives in `addons/top_down/`, which is meant for editor plugins. This conflates "reusable addon" with "game project".
2. **Scripts separated from scenes** — `top_down/scripts/` and `top_down/scenes/` mirror each other's structure, forcing mental mapping between parallel trees.
3. **`game/` directory is disconnected** — Empty skeleton that duplicates `top_down/` structure but has no clear integration path.
4. **Flat resource directories** — `resources/InstanceResources/` has subdirs but many resource folders are flat with naming-only organization.
5. **Typos in folder names** — `obstackles/` should be `obstacles/`, `assault_riffle` should be `assault_rifle`.
6. **No separation of core systems from game content** — Reusable systems (damage, weapons, spawning) mixed with game-specific content (specific enemies, levels).

## Proposed Structure

```
godot-template/
├── project.godot
├── default_bus_layout.tres          # Must stay at root (Godot limitation)
├── icon.svg
│
├── core/                            # Reusable game framework (was great_games_library)
│   ├── autoload/                    # Global singletons
│   │   ├── Logger.gd
│   │   ├── SoundManager.gd
│   │   ├── Music.gd
│   │   └── SteamInit.gd
│   ├── nodes/                       # Custom node types
│   │   ├── area_transmitter/        # Data transmission system
│   │   ├── navigation/              # Tilemap nav helpers
│   │   ├── resource_node/           # Dictionary resource storage
│   │   └── utility/                 # Debug, spawning helpers
│   ├── resources/                   # Base resource classes
│   │   ├── instance_resource/       # Scene pooling
│   │   ├── reference_node/          # Observable node refs
│   │   ├── saveable_resource/       # Persistence
│   │   ├── sound_resource/          # Audio config
│   │   └── value_resource/          # Typed value wrappers
│   └── static/                      # Static utility classes
│       ├── GameMath.gd
│       ├── PhysicsHelper.gd
│       ├── ThreadUtility.gd
│       └── ...
│
├── systems/                         # Reusable game systems (extracted from top_down)
│   ├── actor/                       # Actor framework
│   │   ├── actor.tscn               # Scene + script together
│   │   ├── actor.gd
│   │   ├── MoverTopDown2D.gd
│   │   ├── ActorStatsResource.gd
│   │   ├── DashAbility.gd
│   │   └── ...
│   ├── damage/                      # Damage/health system
│   │   ├── ActorDamage.gd
│   │   ├── DamageResource.gd
│   │   ├── HealthResource.gd
│   │   ├── StatusSetup.gd
│   │   └── properties/
│   ├── weapons/                     # Weapon/projectile system
│   │   ├── weapon.tscn
│   │   ├── projectile/
│   │   │   ├── Projectile2D.gd
│   │   │   ├── ProjectileSpawner.gd
│   │   │   └── ...
│   │   └── projectile.tscn
│   ├── pickups/                     # Item/pickup system
│   │   ├── ItemPickup.gd
│   │   ├── ItemResource.gd
│   │   └── ...
│   ├── arena/                       # Wave spawning system
│   │   ├── EnemyManager.gd
│   │   ├── EnemyWaveManager.gd
│   │   └── ...
│   ├── camera/                      # Camera system
│   │   ├── main_camera.tscn
│   │   ├── CameraFollow2D.gd
│   │   └── CameraShakeResource.gd   # (moved from core)
│   ├── input/                       # Input rebinding system
│   │   ├── BindingMenu.gd
│   │   ├── ActionResource.gd
│   │   └── ...
│   ├── transition/                  # Scene transition system
│   │   ├── transition.tscn
│   │   ├── TransitionManager.gd
│   │   └── transition.gdshader
│   └── ui/                          # Reusable UI components
│       ├── menu_button.tscn
│       ├── audio_slider.tscn
│       ├── ButtonAnimation.gd
│       └── ...
│
├── game/                            # Game-specific content
│   ├── actors/                      # Specific characters
│   │   ├── player/
│   │   │   ├── player.tscn
│   │   │   ├── PlayerInput.gd
│   │   │   ├── PlayerJuice.gd
│   │   │   └── ...
│   │   ├── enemies/
│   │   │   ├── zombie/
│   │   │   │   ├── zombie.tscn
│   │   │   │   └── zombie_crawler.tscn
│   │   │   ├── slime/
│   │   │   │   ├── slime.tscn
│   │   │   │   └── slime_small.tscn
│   │   │   └── boss/
│   │   │       └── big_jelly/
│   │   └── ai/
│   │       ├── BotInput.gd
│   │       ├── TargetFinder.gd
│   │       └── ...
│   ├── weapons/                     # Specific weapon instances
│   │   ├── gun/
│   │   │   └── gun.tscn
│   │   ├── shotgun/
│   │   │   └── shotgun.tscn
│   │   ├── sword/
│   │   │   └── sword.tscn
│   │   └── projectiles/             # Specific bullet variants
│   │       ├── bullet.tscn
│   │       ├── shotgun_bullet.tscn
│   │       └── ...
│   ├── levels/
│   │   ├── room_0.tscn
│   │   ├── room_start.tscn
│   │   ├── tile_layers/
│   │   └── tilesets/
│   ├── pickups/
│   │   ├── coin_pickup.tscn
│   │   ├── health_pickup.tscn
│   │   └── ...
│   ├── vfx/
│   │   ├── explosions/
│   │   ├── death/
│   │   └── particles/
│   ├── screens/                     # Game screens
│   │   ├── boot_load.tscn
│   │   ├── title.tscn
│   │   ├── pause.tscn
│   │   ├── game_over.tscn
│   │   └── control_rebinding.tscn
│   ├── hud/
│   │   ├── game_hud.tscn
│   │   ├── HealthPanel.gd
│   │   └── UiWeaponInventory.gd
│   ├── resources/                   # Game-specific resource instances (.tres)
│   │   ├── actors/                  # Stats, instance resources
│   │   ├── weapons/                 # Weapon database, projectile configs
│   │   ├── arena/                   # Wave configs, spawn points
│   │   ├── camera/                  # Shake configs, camera refs
│   │   ├── sounds/                  # Sound resource instances
│   │   ├── global/                  # Shared game state
│   │   ├── materials/               # Shader materials
│   │   └── particles/               # Particle process materials
│   └── autoloads/                   # Game-specific autoload scenes
│       ├── sound_manager.tscn
│       ├── music.tscn
│       ├── transition.tscn
│       └── persistent_data.tscn
│
├── assets/                          # All raw assets at project root
│   ├── images/
│   │   ├── characters/
│   │   ├── gui/
│   │   ├── items/
│   │   ├── input_prompts/           # (was kenney_input_prompt)
│   │   ├── projectiles/
│   │   ├── tilesets/
│   │   ├── vfx/
│   │   └── weapons/
│   ├── music/
│   ├── sounds/
│   ├── shaders/                     # All .gdshader files
│   └── fonts/
│
├── addons/                          # True editor plugins only
│   ├── kanban_tasks/
│   └── resource_manager/
│
├── docs/                            # Project documentation
│   ├── CODEBASE_MAP.md
│   └── game_design_document.md
│
└── theme/                           # GUI theme resources
    └── game_gui_theme.tres
```

## Key Principles

1. **Co-locate scripts with scenes** — A scene and its script live in the same folder. No parallel `scripts/` vs `scenes/` trees.
2. **Three-tier separation:**
   - `core/` — Engine-level utilities (no game logic, any project can use)
   - `systems/` — Game system frameworks (damage, weapons, spawning — reusable across games of same genre)
   - `game/` — Content specific to this game (specific enemies, levels, weapons)
3. **`addons/` for actual plugins only** — Only Kanban Tasks and Resource Manager stay here.
4. **`assets/` at project root** — Single source of truth for all raw media files.
5. **Group by feature, not file type** — A weapon folder has its .tscn, .gd, and .tres together.

## Migration Strategy

This is a large refactor that will break all `res://` paths in .tscn and .tres files. Approach:

### Phase 1: Fix typos and naming (low risk)
- Rename `obstackles/` -> `obstacles/`
- Rename `assault_riffle` -> `assault_rifle`
- Fix any other naming inconsistencies

### Phase 2: Extract `core/` from `great_games_library/`
- Move `addons/great_games_library/` -> `core/`
- Update all `res://addons/great_games_library/` paths
- Update autoload paths in project.godot

### Phase 3: Create `systems/` from reusable `top_down/` code
- Move base actor, damage, weapon, pickup, arena, camera, input, transition systems
- Keep only the framework scripts/scenes, not specific instances

### Phase 4: Restructure `game/` as game content
- Move specific enemies, weapons, levels, screens into `game/`
- Co-locate scripts with their scenes
- Move all .tres resource instances into `game/resources/`

### Phase 5: Consolidate assets
- Move `addons/top_down/assets/` -> `assets/`
- Move shaders from `scripts/shaders/` -> `assets/shaders/`
- Update all image/audio/shader paths in resources and scenes

### Phase 6: Clean up
- Remove empty `addons/top_down/` directory
- Update project.godot (main_scene, autoloads)
- Update default_bus_layout.tres references if needed
- Verify all scenes load correctly in editor

## Risk Notes

- **Every .tscn and .tres file contains hardcoded `res://` paths** — These all need updating. Godot 4.6 uses UIDs which helps, but path references in scripts (`load()`, `preload()`, `scene_path` strings in InstanceResource) must be manually updated.
- **InstanceResource uses string paths intentionally** (to avoid cyclic refs) — All `scene_path` values in .tres files need updating.
- **`default_bus_layout.tres` must stay at project root** — Godot limitation.
- **Recommend doing this in a feature branch** with incremental commits per phase.
