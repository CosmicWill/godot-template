# Enemy Creation Pipeline

Python CLI for generating all boilerplate files for a new enemy. A unified editor plugin (combining weapon + enemy editing) is planned as a future follow-up.

## Enemy Architecture Overview

Every enemy requires these pieces:

| File | Location | Purpose |
|------|----------|---------|
| Enemy scene | `game/actors/enemies/{name}/{name}.tscn` | Inherits `actor.tscn`, configures stats, sprite, AI, attack, pooling |
| InstanceResource | `game/resources/actors/{name}_instance_resource.tres` | Links enemy scene to the spawning system |
| Death VFX scene | `game/vfx/dead/{name}_dead.tscn` | Death animation with sprite, pooling, color flash |
| Death VFX InstanceResource | `game/resources/vfx/dead/{name}_dead_instance_resource.tres` | Links death VFX to spawning system |
| Placeholder sprite | `assets/images/characters/{name}_16x16_strip8.png` | 8-frame horizontal spritesheet (128x16) |
| Attack weapon (optional) | `game/weapons/{name}_attack/{name}_attack.tscn` | Dedicated attack inheriting `weapon.tscn` |
| Attack projectile IR (optional) | `game/resources/weapons/{name}_slash_instance_resource.tres` | Projectile InstanceResource for the attack |

### Inheritance chain

```
systems/actor/actor.tscn              # Base: ResourceNode, MoverTopDown2D, ActorDamage, etc.
  └── game/actors/enemies/{name}/     # Your enemy (overrides stats, sprite, adds AI + attack)
```

### Configurable properties

| Property | Set on | Description |
|----------|--------|-------------|
| HP | `HealthResource.hp/max_hp` | Hit points |
| Speed | `ActorStatsResource.max_speed` | Maximum movement speed |
| Acceleration | `ActorStatsResource.acceleration` | Movement acceleration |
| Attack distance | `BotInput.attack_distance` | Distance to trigger attack |
| Collision size | `CollisionShape2D.shape` | RectangleShape2D dimensions |
| Resistance | `DamageSetup.resistance_list` | Damage type resistance (type + value) |
| Death VFX | `ActorDamage.dead_vfx_instance_resource` | Death animation scene |

---

## Python CLI — `tools/create_enemy.py`

Generates all boilerplate files for a new enemy. No external dependencies (Python stdlib only).

### Usage

```bash
python tools/create_enemy.py <name> [options]
```

### Arguments

| Argument | Description |
|----------|-------------|
| `name` | Enemy name in snake_case (e.g. `fire_bat`) |
| `--archetype` | `melee`, `ranged`, or `boss` (default: `melee`) |
| `--hp` | Hit points (override archetype default) |
| `--speed` | Max movement speed |
| `--acceleration` | Movement acceleration |
| `--attack-distance` | Distance to trigger attack |
| `--damage` | Attack damage value |
| `--damage-type` | `physical`, `fire`, `ice`, `lightning`, `poison`, `acid`, `magnetic`, `blood`, `dark`, `arcane` |
| `--generate-attack` | Generate a dedicated attack weapon instead of reusing `zombie_attack` |
| `--collision-width` | Collision shape width |
| `--collision-height` | Collision shape height |
| `--resistance` | Damage resistance as type:value (e.g. `fire:5`) |
| `--dry-run` | Preview what would be generated without writing files |

### Archetype defaults

| Property | Melee | Ranged | Boss |
|----------|-------|--------|------|
| HP | 50 | 30 | 500 |
| Acceleration | 200 | 150 | 100 |
| Max Speed | 40 | 25 | 30 |
| Attack Distance | 10 | 80 | 15 |
| Collision Size | 8x4 | 8x4 | 24x12 |
| Damage | 10 | 8 | 25 |
| Damage Type | physical | physical | physical |

### Examples

```bash
# Basic melee chaser
python tools/create_enemy.py fire_bat --archetype melee

# Ranged enemy with custom stats
python tools/create_enemy.py archer_skeleton --archetype ranged --hp 40 --speed 20

# Boss with dedicated attack and ice damage
python tools/create_enemy.py ice_golem --archetype boss --hp 800 --generate-attack --damage-type ice

# Enemy with fire resistance
python tools/create_enemy.py fire_elemental --archetype melee --resistance fire:10

# Preview without creating files
python tools/create_enemy.py test_enemy --archetype melee --dry-run

# Override any default
python tools/create_enemy.py fast_imp --archetype melee --speed 60 --hp 20 --attack-distance 8
```

### What it generates

1. **Placeholder spritesheet** — 128x16 PNG (8 frames of 16x16, color-coded by archetype)
2. **Enemy scene** — Inherits `actor.tscn` with configured stats, AI, attack, pooling, and ActiveEnemy
3. **InstanceResource** — Links enemy scene to the spawning/pooling system
4. **Death VFX scene** — Death animation with sprite, body fall, scale shrink, and pool return
5. **Death VFX InstanceResource** — Links death VFX scene to spawning system
6. **Attack weapon** (if `--generate-attack`) — Dedicated weapon scene inheriting `weapon.tscn`
7. **Attack projectile InstanceResource** (if `--generate-attack`) — Projectile resource for the attack

### After generation

1. Open Godot to import the new files
2. Replace the placeholder sprite with real art (`assets/images/characters/{name}_16x16_strip8.png`)
3. Add `{name}_instance_resource.tres` to a `SpawnWaveList` in your arena config
4. Tune values in the editor or by re-editing the scene files

---

## Adding an enemy manually (without the CLI)

If you prefer to create enemies by hand or need a non-standard setup:

1. Create `game/actors/enemies/{name}/{name}.tscn` — right-click `actor.tscn` > "New Inherited Scene"
2. Override: collision_layer=4, collision_mask=5, ResourceNode stats (movement, health), sprite texture
3. Add animations: idle (2-frame loop) + walk (6-frame loop) in CharacterAnimator
4. Configure `ActorDamage`: set `sound_resource_dead` and `dead_vfx_instance_resource`
5. Add `enemy_ai.tscn` as child (index 15) with `resource_node` pointing to `../ResourceNode`
6. Add attack weapon instance (index 16) with `collision_mask=2` and `resource_node` path
7. Add `PoolNode` (index 17) with animation_player_list and listen_node to ActorDamage
8. Add `ActiveEnemy` node (index 18) with resource_node path
9. Create `game/resources/actors/{name}_instance_resource.tres` — InstanceResource with scene_path and ysort_reference parent
10. Create death VFX scene + InstanceResource (see `game/vfx/dead/zombie_dead.tscn` as reference)

---

## Future: Unified Editor Plugin

The Weapon Editor plugin will be extended into a unified "Content Editor" that also supports browsing, editing, and previewing enemies alongside weapons. This is planned as a follow-up.
