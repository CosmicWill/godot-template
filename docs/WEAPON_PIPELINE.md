# Weapon Creation Pipeline

Two tools for creating and editing weapons: a Python CLI for generating boilerplate and a Godot editor plugin for assigning assets and tuning properties.

## Weapon Architecture Overview

Every weapon requires these pieces:

| File | Location | Purpose |
|------|----------|---------|
| Weapon scene | `game/weapons/{name}/{name}.tscn` | Inherits `gun.tscn`, configures fire rate, kickback, sprite, projectile |
| Projectile scene | `game/weapons/projectiles/{name}_projectile.tscn` | Inherits base `projectile.tscn`, configures movement, damage, speed |
| Projectile InstanceResource | `game/resources/weapons/{name}_projectile_instance_resource.tres` | Links projectile scene to the spawning system with parent reference |
| Weapon sprite | `assets/images/weapon/{name}.png` | Weapon visual |
| Projectile sprite | `assets/images/projectile/{name}_projectile.png` | Projectile visual |
| Database entry | `game/resources/weapons/weapon_database.tres` | Registers weapon for inventory/selection |

### Inheritance chain

```
systems/weapons/weapon.tscn           # Base: rotation, trigger, spawner, kickback
  └── game/weapons/gun/gun.tscn       # Configured with animations, sound
        └── game/weapons/{name}/      # Your weapon (overrides sprite, stats, projectile)
```

All three archetypes (gun, staff, melee) inherit from `gun.tscn` and differ only in configuration.

### Configurable properties

| Property | Set on | Description |
|----------|--------|-------------|
| Damage | `ProjectileSetup.base_damage` | Array of DamageTypeResource (value + type enum) |
| Damage type | `DamageTypeResource.type` | PHYSICAL=0, FIRE=1, ICE=2, LIGHTNING=3, POISON=4, ACID=5, MAGNETIC=6, BLOOD=7, DARK=8, ARCANE=9 |
| Fire rate | `ProjectileInterval.interval` | Seconds between shots |
| Kickback | `WeaponKickback.kickback_strength` | Knockback on shooter (negative = pull forward) |
| Projectile speed | `Projectile2D.speed` | Movement speed |
| Projectile lifetime | `ProjectileLifetime.time` | Seconds before despawn |
| Hit limit | `HitLimit.target_hit_limit` | Max targets per projectile (-1 = infinite) |
| Spread | `SpreadShot.random_angle_offset` | Random angle variation per shot |
| Movement type | `ProjectileMover.movement_type` | 0=PROJECTILE, 1=SHAPECAST, 2=RAYCAST, 3=LERP_SPEED, 4=LERP_TIME |

---

## Python CLI — `tools/create_weapon.py`

Generates all boilerplate files for a new weapon. No external dependencies (Python stdlib only).

### Usage

```bash
python tools/create_weapon.py <name> [options]
```

### Arguments

| Argument | Description |
|----------|-------------|
| `name` | Weapon name in snake_case (e.g. `fire_staff`) |
| `--archetype` | `gun`, `staff`, or `melee` (default: `gun`) |
| `--damage-type` | `physical`, `fire`, `ice`, `lightning`, `poison`, `acid`, `magnetic`, `blood`, `dark`, `arcane` |
| `--fire-rate` | Seconds between shots |
| `--damage` | Base damage value |
| `--kickback` | Knockback strength (negative = pull forward) |
| `--speed` | Projectile speed |
| `--lifetime` | Projectile lifetime in seconds |
| `--hit-limit` | Max targets per projectile |
| `--spread` | Random angle spread in degrees |
| `--dry-run` | Preview what would be generated without writing files |

### Archetype defaults

| Property | Gun | Staff | Melee |
|----------|-----|-------|-------|
| Fire rate | 0.5s | 0.8s | 0.3s |
| Damage | 10.0 | 15.0 | 20.0 |
| Damage type | physical | arcane | physical |
| Kickback | 30.0 | 0.0 | -30.0 |
| Proj speed | 120.0 | 80.0 | 60.0 |
| Proj lifetime | 2.0s | 1.5s | 0.27s |
| Hit limit | 1 | 1 | 3 |
| Spread | 5.0 | 0.0 | 0.0 |

### Examples

```bash
# Basic gun with defaults
python tools/create_weapon.py plasma_gun --archetype gun

# Fire staff with custom damage
python tools/create_weapon.py fire_staff --archetype staff --damage-type fire --damage 25

# Fast melee weapon
python tools/create_weapon.py daggers --archetype melee --fire-rate 0.15 --kickback -10

# Preview without creating files
python tools/create_weapon.py test_weapon --archetype gun --dry-run

# Override any default
python tools/create_weapon.py crossbow --archetype gun --fire-rate 1.2 --damage 30 --speed 200
```

### What it generates

1. **Placeholder sprites** — 16x16 weapon and 8x8 projectile PNGs (color-coded by archetype)
2. **Projectile scene** — Inherits base `projectile.tscn` with configured damage, speed, movement, lifetime
3. **InstanceResource** — Links projectile scene to the spawning/pooling system
4. **Weapon scene** — Inherits `gun.tscn` with configured fire rate, kickback, sprite, projectile reference
5. **Database registration** — Adds entry to `weapon_database.tres` so the weapon appears in inventory

### After generation

1. Open Godot to import the new files
2. Replace placeholder sprites with real art (via the Weapon Editor plugin or manually)
3. Tune values in the editor or by re-editing the scene files

---

## Godot Editor Plugin — Weapon Editor

Browse, preview, and edit weapon properties and sprites from within the Godot editor.

### Setup

1. Go to **Project > Project Settings > Plugins**
2. Find **Weapon Editor** and set it to **Enabled**
3. The dock panel appears in the right panel

### Location

```
addons/weapon_editor/
├── plugin.cfg
├── weapon_editor_plugin.gd
├── weapon_editor_dock.tscn
└── weapon_editor_dock.gd
```

### Features

| Feature | Description |
|---------|-------------|
| **Weapon list** | Scans `game/weapons/` and lists all weapons with thumbnail icons |
| **Sprite preview** | Shows current weapon and projectile sprites when a weapon is selected |
| **Assign sprites** | Click "Assign..." to open a file dialog and pick a new sprite from `assets/images/` |
| **Property editing** | SpinBoxes for Damage, Fire Rate, Kickback, Projectile Speed, Spread, Lifetime, Hit Limit |
| **Save** | Writes changes back to the weapon and projectile scene files using Godot's PackedScene/ResourceSaver |
| **Open in Editor** | Opens the selected weapon's scene in the main editor |
| **Refresh** | Re-scans the weapons directory (use after generating new weapons via CLI) |

### Workflow

1. Generate a weapon with the CLI: `python tools/create_weapon.py ice_wand --archetype staff --damage-type ice`
2. Open Godot and click **Refresh** in the Weapon Editor dock
3. Select the new weapon from the list
4. Click **Assign...** next to "Weapon Sprite" to pick your art from the filesystem
5. Click **Assign...** next to "Projectile Sprite" for the projectile art
6. Adjust damage, fire rate, and other properties via the SpinBoxes
7. Click **Save Changes**

---

## Adding a weapon manually (without the CLI)

If you prefer to create weapons by hand or need a non-standard setup:

1. Create `game/weapons/{name}/{name}.tscn` — right-click `gun.tscn` > "New Inherited Scene"
2. Override: sprite texture, `ProjectileInterval.interval`, `WeaponKickback.kickback_strength`
3. Create `game/weapons/projectiles/{name}_projectile.tscn` — inherit from `systems/weapons/projectile/projectile.tscn`
4. Override: `Projectile2D.speed`, `ProjectileSetup.base_damage`, `ProjectileMover.movement_type`, sprite, `ProjectileLifetime.time`, `HitLimit.target_hit_limit`
5. Create `game/resources/weapons/{name}_projectile_instance_resource.tres` — InstanceResource with `scene_path` pointing to your projectile and `parent_reference_resource` set to `ysort_reference.tres`
6. Point `ProjectileSpawner.projectile_instance_resource` in your weapon scene to the new InstanceResource
7. Add a `WeaponItemResource` entry to `game/resources/weapons/weapon_database.tres` with name, icon, scene_path, and unlocked state
