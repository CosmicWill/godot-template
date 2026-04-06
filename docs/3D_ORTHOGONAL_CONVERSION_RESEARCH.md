# Research: Converting to 3D with Orthogonal Camera for Isometric Look

## Executive Summary

This document analyzes what it would take to convert the current 2D top-down shooter template into a 3D scene graph using a Camera3D with orthogonal projection to achieve the existing isometric look. The approach solves several pain points in the current 2D isometric implementation — particularly the manual axis multiplier hack for faking perspective, complex diamond-shaped collision polygons, and Y-sort depth ordering — but requires touching nearly every system in the project.

**Scope estimate:** 69 scene files, ~60 GDScript files with 2D-specific code (25 directly extending 2D node types, 72 files containing Vector2 usage), and 102 resource files. This is effectively a rewrite of the scene graph and physics layer, while preserving the resource-driven architecture and game logic.

---

## Why This Approach Solves Real Problems

The current template already fights against 2D limitations to achieve its isometric look. Converting to 3D with orthogonal projection eliminates these workarounds:

### Problems in the current 2D implementation that 3D solves

**1. The axis_multiplier hack.** `MoverTopDown2D` multiplies velocity by an `axis_multiplier_resource` (typically `Vector2(1.0, 0.5)`) to fake the isometric foreshortening on the Y axis, then divides it back out with `axis_compensation` after collision resolution. Every system that touches position or velocity must know about this distortion — projectiles, spawning, camera, AI navigation. In 3D, characters simply move on the XZ plane and the camera projection handles the visual foreshortening automatically.

**2. Diamond collision polygons.** `TileCollisionGenerator` creates `CollisionPolygon2D` nodes with diamond shapes `(0,8), (16,0), (0,-8), (-16,0)` to approximate isometric tile boundaries. These are imprecise — diagonal edges cause characters to catch on corners and slide unpredictably. In 3D, tiles become simple axis-aligned boxes or planes, and collision "just works."

**3. Y-sort depth ordering.** The template uses a separate `WallLayer_Ysorted` TileMapLayer with `y_sort_enabled = true` and `z_index = 2` to handle wall occlusion. This is fragile — entities that move vertically can pop in front of or behind walls incorrectly. In 3D, the renderer handles depth via the Z-buffer automatically; a wall that's behind the player in world space is behind the player visually, always.

**4. Isometric mouse coordinate conversion.** `PlayerInput` currently uses `get_local_mouse_position()` which returns screen-space coordinates that don't account for the isometric distortion. Aiming feels slightly off because the mouse-to-world mapping is skewed. In 3D, raycasting from the camera through the mouse position to the ground plane gives perfect world-space coordinates.

---

## The 3D Orthogonal Camera Setup

### Camera configuration

```
Camera3D
├── projection = PROJECTION_ORTHOGONAL
├── size = 135  (half of 270px viewport height, tuned for pixel density)
├── rotation_degrees = Vector3(-30, 45, 0)  ← classic isometric angles
│   or Vector3(-90, 0, 0) for pure top-down
├── far = 1000
├── near = 0.1
```

The `size` property controls how many world units fit vertically in the viewport. For the current 480×270 viewport scaled to 1280×720, a size around 135 preserves the existing pixel density when sprites are placed on 3D planes.

The classic isometric angle is roughly 30° down from horizontal with 45° rotation. For a look closer to the current template (which is more top-down than true isometric), a steeper angle like `(-60, 45, 0)` or even pure top-down `(-90, 0, 0)` works. This is entirely adjustable without touching any gameplay code — a major advantage of the 3D approach.

### World orientation

All gameplay happens on the XZ plane (Y = 0 for ground level). The Y axis becomes the "up" direction. This maps naturally to top-down design:

| Current 2D | 3D Equivalent |
|---|---|
| position.x (horizontal) | position.x (horizontal) |
| position.y (vertical/depth) | position.z (depth into screen) |
| N/A | position.y (elevation/height) |
| Vector2 | Vector3 (with y=0 for ground movement) |

---

## System-by-System Conversion Analysis

### Tier 1: Core Infrastructure (Must convert first)

#### 1.1 MoverTopDown2D → MoverTopDown3D

**Current:** Extends `ShapeCast2D`, moves a `CharacterBody2D`, uses Vector2 velocity with axis_multiplier compensation.

**Changes:**
- Extend `ShapeCast3D` instead of `ShapeCast2D`
- `character: CharacterBody2D` → `CharacterBody3D`
- `velocity: Vector2` → `velocity: Vector3` (with `y` always 0 for ground movement)
- Remove `axis_multiplier_resource` and `axis_compensation` entirely — the camera handles perspective
- `KinematicCollision2D` → `KinematicCollision3D`
- `CollisionShape2D` → `CollisionShape3D` (RectangleShape2D → BoxShape3D)
- `Vector2.slide()` → `Vector3.slide()`
- Collision normals become 3D (but Y component can be ignored for ground movement)

**Complexity:** Medium-high. The physics logic is sound; it's mostly type conversions. The real win is deleting the axis_multiplier hack.

**Lines affected:** ~139 lines (full rewrite of this file)

#### 1.2 AreaTransmitter/AreaReceiver System

**Current:** `AreaTransmitter2D` extends `Area2D`, connects to `area_entered` signal. `AreaReceiver2D` extends `Area2D`. `ShapeCastTransmitter2D` extends `ShapeCast2D`.

**Changes:**
- `AreaTransmitter2D` → `AreaTransmitter3D` extending `Area3D`
- `AreaReceiver2D` → `AreaReceiver3D` extending `Area3D`
- `ShapeCastTransmitter2D` → `ShapeCastTransmitter3D` extending `ShapeCast3D`
- Signal: `area_entered` → `area_entered` (same name in 3D, but parameter type changes to `Area3D`)
- `@export_flags_2d_physics` → `@export_flags_3d_physics`
- Collision shapes: all `CollisionShape2D` children → `CollisionShape3D`

**Complexity:** Medium. The transmission resource system itself (TransmissionResource, DataChannelTransmitter, DataChannelReceiver) is dimension-agnostic and needs zero changes. Only the area/shape detection layer changes.

**Files:** 3 scripts + every scene that uses AreaTransmitter2D/AreaReceiver2D (~15 scenes)

#### 1.3 Actor Scene (actor.tscn)

**Current structure that changes:**

| Current Node | 3D Replacement |
|---|---|
| CharacterBody2D (root) | CharacterBody3D |
| CollisionShape2D (RectangleShape2D 8×4) | CollisionShape3D (BoxShape3D) |
| AreaReceiver2D (Area2D) | AreaReceiver3D (Area3D) |
| Shadow (Sprite2D) | Shadow (Sprite3D or decal) |
| Body/Stretch/Sprite2D | Sprite3D on billboard or 3D model |
| MoverTopDown2D (ShapeCast2D) | MoverTopDown3D (ShapeCast3D) |
| Node2D containers | Node3D containers |

**Sprite approach for existing assets:** Use `Sprite3D` with `billboard = BILLBOARD_ENABLED` or `BILLBOARD_FIXED_Y` so sprites always face the camera. This preserves the 2D art style while living in 3D space. Alternatively, use `Sprite3D` without billboarding and orient sprites to face the camera angle manually.

#### 1.4 Vector2Resource → Vector3Resource

**Current:** `Vector2Resource` wraps a `Vector2` with signals. Used for camera position, axis multipliers, spawn positions.

**Action:** Create a `Vector3Resource` equivalent. Keep `Vector2Resource` alive for UI-only use cases (screen positions, HUD elements). Update all movement/world-position usages to Vector3Resource.

**Files referencing Vector2Resource:** ~25

---

### Tier 2: Gameplay Systems (Convert after core)

#### 2.1 Navigation System

**Current:** `AStarGrid2D` on a `TileMapLayer` grid. `TileNavigationGetter` extends `Line2D` and uses `PackedVector2Array` paths. `TileCollisionGenerator` creates diamond `CollisionPolygon2D` nodes.

**3D Options (pick one):**

**Option A: NavigationMesh3D (recommended).** Godot 4's `NavigationServer3D` with `NavigationRegion3D` and `NavigationAgent3D`. Bake a navigation mesh over the 3D level geometry. Agents get `get_next_path_position()` returning Vector3. This is the most "native" 3D approach and handles complex geometry automatically.

**Option B: Keep AStarGrid2D for logic, project to 3D.** The pathfinding grid itself is 2D (tile coordinates). Keep AStarGrid2D but convert output paths from Vector2 to Vector3 (setting Y=0). This minimizes changes but doesn't leverage 3D navigation features.

**Recommendation:** Option A for new development, Option B as a migration stepping stone.

**Files affected:** `AstarGridResource.gd`, `TileNavigationGetter.gd`, `TileNavigationSetter.gd`, `TileCollisionGenerator.gd`, `TileAstargridObstacle.gd`, `TargetDirection.gd`

#### 2.2 Weapon & Projectile System

**Current:** `Projectile2D` extends `Node2D`. `ProjectileMover` uses `ShapeCast2D`, `RayCast2D`, `PhysicsRayQueryParameters2D`, and `World2D` for bounce detection. Weapon rotation uses `direction.angle()` for 2D rotation.

**Changes:**
- `Projectile2D` → `Projectile3D` extending `Node3D`
- All Vector2 direction/destination fields → Vector3
- `ShapeCast2D` → `ShapeCast3D`, `RayCast2D` → `RayCast3D`
- `PhysicsRayQueryParameters2D` → `PhysicsRayQueryParameters3D`
- `World2D` → `World3D` (for `direct_space_state`)
- `Vector2.bounce()` → `Vector3.bounce()` (works identically)
- Weapon rotation: `rotation = direction.angle()` → rotation around Y axis: `rotation.y = atan2(direction.x, direction.z)`
- Projectile sprites: `Sprite2D` → `Sprite3D` (billboard or oriented)

**Files:** `Projectile2D.gd`, `ProjectileMover.gd`, `ProjectileSpawner.gd`, `ProjectileRotation.gd`, `LerpProjectileTrajectory.gd`, `SubProjectileManager.gd`, `WeaponRotation.gd`, `WeaponKickback.gd`, `Weapon.gd`, `WeaponManager.gd`

#### 2.3 Camera System

**Current:** `CameraFollow2D` extends `Camera2D`, lerps `global_position` toward a `Vector2Resource` target.

**Changes:**
- Extend `Camera3D` with `projection = PROJECTION_ORTHOGONAL`
- Target position becomes `Vector3Resource`
- The camera follows by offsetting its position while maintaining the fixed rotation (isometric angle)
- Camera shake: `CameraShakeResource` currently stores Vector2 offsets → needs Vector3 (or just offset the camera's 3D position)

**Advantage:** Camera angle is now a single property. Want to zoom? Change `size`. Want a different angle? Change rotation. No gameplay code changes needed.

#### 2.4 Input System

**Current:** `PlayerInput` uses `get_local_mouse_position()` for aim direction (Vector2). Movement axis is Vector2 from WASD/gamepad.

**Changes for aiming:**
```gdscript
# Current 2D approach:
var aim_direction:Vector2 = position_node.get_local_mouse_position()

# 3D approach - raycast from camera through mouse to ground plane:
var mouse_pos:Vector2 = get_viewport().get_mouse_position()
var camera:Camera3D = get_viewport().get_camera_3d()
var from:Vector3 = camera.project_ray_origin(mouse_pos)
var dir:Vector3 = camera.project_ray_normal(mouse_pos)
var ground_y:float = 0.0
var t:float = (ground_y - from.y) / dir.y
var world_pos:Vector3 = from + dir * t
var aim_direction:Vector3 = (world_pos - player.global_position).normalized()
```

**Changes for movement:** Movement input stays as Vector2 from the gamepad/keyboard, but maps to XZ: `Vector3(input.x, 0, input.y)`. If using an angled camera, the input directions need to be rotated to match the camera's visual axes — otherwise pressing "up" moves the character into the screen rather than visually upward.

**Files:** `PlayerInput.gd`, `InputResource.gd`, `BotInput.gd`

#### 2.5 Tile/Level System

**Current:** `TileMapLayer` nodes for floor, obstacles, and walls. `TileCollisionGenerator` creates diamond collision polygons.

**3D Approaches:**

**Option A: GridMap (Godot's 3D tilemap).** Replace TileMapLayer with `GridMap`. Create a `MeshLibrary` from the existing tile art (as textured planes or low-poly meshes). GridMap supports collision shapes per cell natively. This is the closest 3D equivalent to TileMapLayer.

**Option B: Procedural mesh generation.** Keep tile data in a custom resource and generate 3D collision/mesh at runtime. More control, more work.

**Option C: Static 3D scenes.** Design levels as 3D scenes in the editor with CSG or imported meshes. Most flexible visually but loses the tile workflow.

**Recommendation:** GridMap (Option A) preserves the tile-based level design workflow and is well-supported in Godot 4.

**Impact on TileCollisionGenerator:** Eliminated entirely. GridMap handles collisions per cell with axis-aligned boxes — no more diamond polygon generation.

#### 2.6 VFX System

**Current:** `AfterImageVFX` extends `Node2D` with `Sprite2D`. `ParticleStarter` extends `GPUParticles2D`.

**Changes:**
- `AfterImageVFX`: `Node2D` → `Node3D`, `Sprite2D` → `Sprite3D`
- `ParticleStarter`: `GPUParticles2D` → `GPUParticles3D`
- All particle `.tres` materials need recreation for 3D (ParticleProcessMaterial works in both but emission shapes differ)
- Screen-space effects (`ScreenEffects` CanvasLayer) remain 2D — these overlay the camera and don't need conversion

#### 2.7 Enemy AI

**Current:** `TargetDirection` uses `RayCast2D` for line-of-sight. `TargetAim` and `TargetFinder` compute Vector2 directions.

**Changes:**
- `RayCast2D` → `RayCast3D`
- All Vector2 direction math → Vector3 (with Y=0)
- Navigation path following → NavigationAgent3D or projected AStarGrid2D paths
- `direction.angle()` → `atan2(direction.x, direction.z)` for facing

**Files:** `TargetDirection.gd`, `TargetAim.gd`, `TargetFinder.gd`, `BotInput.gd`, `BigJellyChase.gd`, `BigJellyJumpDamage.gd`, `BigJellyShootSlime.gd`, `BigJellySlimeSpawner.gd`, `JumpMove.gd`, `SlimeSplit.gd`, `CriticalDamageReplace.gd`

---

### Tier 3: Supporting Systems (Minimal or no changes)

These systems are already dimension-agnostic or UI-only:

| System | Changes Needed |
|---|---|
| **ResourceNode** | None — stores resources by name, no spatial code |
| **TransmissionResource** | None — pure data payload |
| **DataChannelTransmitter/Receiver** | None — string-keyed callbacks |
| **HealthResource / DamageResource** | None — numerical systems |
| **SaveableResource / PersistentData** | None — serialization only |
| **SoundManager / Music** | None — audio is spatial-independent (unless adding 3D positional audio later) |
| **InstanceResource** | Minimal — scene_path strings still work; parent reference nodes change type |
| **Transition system** | None — uses CanvasLayer (screen-space) |
| **UI / HUD** | None — remains in CanvasLayer/Control nodes |
| **ActorStatsResource** | None — stores scalar values (speed, acceleration) |
| **PoolNode** | None — manages node lifecycle, not spatial |
| **GameEnums** | None |
| **Boot/preload sequence** | None — scene loading is format-agnostic |

---

## 2D Asset Adaptation Strategy

### Sprites → 3D

There are three approaches for using existing 2D art in a 3D scene:

**Approach 1: Sprite3D (recommended for this project)**
- Place `Sprite3D` nodes where `Sprite2D` was used
- Set `billboard = BILLBOARD_FIXED_Y` so sprites always face the camera but stay upright
- Existing sprite sheets, animation frames, hframes/vframes all work identically on Sprite3D
- `Sprite3D.pixel_size` controls world-space scaling (default 0.01 = 1 pixel = 0.01 units)
- Existing `AnimationPlayer` tracks targeting Sprite2D properties (frame, flip_h, modulate) work on Sprite3D with the same property names

**Approach 2: Textured quads**
- Use `MeshInstance3D` with `QuadMesh` and a `StandardMaterial3D` with the sprite texture
- More control over material properties (transparency, shading)
- Better for static environmental art

**Approach 3: Keep 2D rendering via SubViewport**
- Render 2D sprites in a `SubViewport` and display the result on a `Sprite3D`
- Maximum compatibility with existing 2D code
- Performance overhead; not recommended for many entities

### Shadows

**Current:** Each actor has a `Shadow` Sprite2D (dark ellipse, low alpha).

**3D options:**
- `Sprite3D` on the ground plane (same approach, works well with orthogonal camera)
- `Decal` node — Godot 4's built-in decal system, projects a texture onto geometry below
- Actual `DirectionalLight3D` shadows — most realistic but may not match the pixel art style

### Particles

**Current:** `GPUParticles2D` with various materials.

**3D conversion:** `GPUParticles3D` with `ParticleProcessMaterial`. Most properties map directly. Emission shapes change from 2D rects/circles to 3D boxes/spheres. Billboard particles (which always face the camera) maintain the 2D look.

### Tilesets

**Current:** `TileSet` resources with isometric tiles (diamond shapes, 16×8 or 32×16 pixel tiles).

**3D conversion to GridMap:**
1. Create textured planes (or thin boxes) for each tile type
2. Build a `MeshLibrary` from these meshes
3. Place tiles on the XZ plane in GridMap
4. Collision shapes become simple BoxShape3D per cell

The existing tile art can be applied as textures to planes, maintaining the visual style.

---

## What Gets Simpler in 3D

1. **No more axis_multiplier/axis_compensation** — the camera projection handles foreshortening
2. **No more diamond collision polygons** — axis-aligned boxes work correctly
3. **No more Y-sort layer management** — Z-buffer handles depth automatically
4. **No more manual isometric coordinate conversion** — `map_to_local` / `local_to_map` become straightforward grid lookups
5. **Elevation becomes trivial** — jumping, flying enemies, multi-floor levels just use the Y axis
6. **Mouse aiming is accurate** — camera ray-to-ground-plane intersection gives true world coordinates
7. **Camera angle is adjustable** — change rotation for different perspective feels without touching gameplay

## What Gets More Complex in 3D

1. **Pixel-perfect rendering** — orthogonal 3D can have sub-pixel jitter; needs careful `size` tuning and possibly a `SubViewport` at native resolution
2. **Sprite billboarding** — needs configuration per Sprite3D; rotation during animations (like the weapon sprite) requires additional setup
3. **3D physics overhead** — slightly higher CPU cost than 2D physics for the same entity count (but the template's entity counts are small)
4. **Shader compatibility** — `color_flash.gdshader` and other 2D shaders need porting to 3D shader type (`shader_type spatial` instead of `shader_type canvas_item`)
5. **Editor workflow** — 3D level editing is less intuitive than 2D tile painting; GridMap helps but isn't as polished as the TileMap editor
6. **Lighting** — 3D scenes need at minimum an `Environment` and a `DirectionalLight3D` to look correct; 2D scenes need neither

---

## Migration Strategy

### Phase 1: Proof of Concept (1-2 weeks)

Build a minimal 3D room with one actor to validate the approach:

1. Create a `Camera3D` with orthogonal projection and test angles
2. Create one `CharacterBody3D` actor with a `Sprite3D` (player sprite, billboard)
3. Port `MoverTopDown3D` — movement on XZ plane, no axis multiplier
4. Create a simple floor (MeshInstance3D with plane) and walls (BoxShape3D)
5. Implement mouse-to-ground-plane raycasting for aiming
6. Validate that the look and feel matches the current game

**Success criteria:** Player can move, collide with walls, and aim at the mouse cursor with correct world-space mapping.

### Phase 2: Core Systems (2-3 weeks)

Port the foundational systems:

1. `AreaTransmitter3D` / `AreaReceiver3D` — the transmission backbone
2. Projectile system — spawning, movement, bounce, damage
3. One enemy type (zombie) with AI navigation
4. Basic weapon (gun) with rotation and firing
5. Health/damage system integration

### Phase 3: Content Migration (2-3 weeks)

Port all game content:

1. All enemy types (zombie, slime, crawler, boss)
2. All weapons (gun, shotgun, assault rifle, sword)
3. All pickups (coin, health, item)
4. VFX (particles, after-image, explosions, death animations)
5. Level scenes (room_start, room_0) using GridMap or manual placement
6. Arena/wave system, spawning

### Phase 4: Polish & Edge Cases (1-2 weeks)

1. Port all shaders to `shader_type spatial`
2. Camera shake in 3D
3. Screen effects (flash, transition)
4. HUD connections (weapon display, health panel)
5. Pause, game over, title screens (these are mostly UI/CanvasLayer, minimal changes)
6. Performance profiling — compare 2D vs 3D frame times
7. Pixel-perfect rendering tuning

### Total Estimated Effort: 6-10 weeks

---

## File Impact Summary

| Category | File Count | Change Type |
|---|---|---|
| Scripts extending 2D nodes | 25 | Full rewrite (new base class) |
| Scripts using Vector2 for world positions | ~47 | Modify (Vector2 → Vector3 for world, keep Vector2 for screen) |
| Scene files (.tscn) | 69 | Rebuild (new node types) |
| Resource files (.tres) | ~50 of 102 | Update (scene paths, Vector2 → Vector3 values) |
| Shaders | 8 | Port (canvas_item → spatial) |
| Dimension-agnostic scripts | ~95 | No changes |
| UI/CanvasLayer scenes | ~10 | No changes |

### Key files to convert (priority order)

1. `systems/actor/MoverTopDown2D.gd` — core movement
2. `core/nodes/AreaTransmitter/AreaTransmitter2D.gd` — damage/pickup detection
3. `core/nodes/AreaTransmitter/AreaReceiver2D.gd` — damage/pickup reception
4. `core/nodes/AreaTransmitter/ShapeCastTransmitter2D.gd` — alternative transmission
5. `systems/actor/actor.tscn` — base actor scene
6. `systems/weapons/projectile/ProjectileMover.gd` — projectile physics
7. `systems/weapons/projectile/Projectile2D.gd` — projectile base
8. `systems/camera/CameraFollow2D.gd` — camera system
9. `game/actors/player/PlayerInput.gd` — mouse aiming
10. `core/nodes/Navigation/TileNavigationGetter.gd` — pathfinding

---

## Recommendation

The conversion is a significant undertaking (6-10 weeks) but the template's architecture makes it more feasible than a typical 2D-to-3D port. The resource-driven design means roughly half the codebase (ResourceNode, transmission resources, health/damage resources, save system, sound, UI) needs zero or minimal changes.

The biggest wins are eliminating the axis_multiplier hack (which currently pollutes every movement-related system), getting proper depth ordering for free, and unlocking elevation gameplay (jumping, flying, multi-floor) that would be extremely painful in 2D isometric.

**The recommended approach:** Start with Phase 1 as a parallel experiment in a new branch. If the proof of concept validates the look and feel within a week, proceed with the full migration. If the pixel-art aesthetic doesn't translate well to 3D orthogonal projection (sub-pixel jitter, sprite scaling issues), the investment is minimal.

---

## References

- [Isometric 3D Toolkit for Godot 4.x](https://github.com/marinho/isometric-3d-toolkit) — C# reference implementation
- [IsometricExample3D](https://github.com/frokk/IsometricExample3D) — GDScript example with player controller
- [Rendering Isometric Sprites Using Godot](https://kenney.nl/knowledge-base/learning/rendering-isometric-sprites-using-godot) — Kenney's guide on isometric sprite setup
- [Godot Forum: Camera3D Top-Down Setup](https://forum.godotengine.org/t/camera3d-topdown-setup/97561) — Community discussion
- [Godot Forum: Pixel Perfect Orthographic Camera](https://forum.godotengine.org/t/pixel-perfect-orthographic-camera-and-physics-side-effects/47415) — Physics side effects discussion
- [Rendering a 2D Game in 3D](https://medium.com/@recallsingularity/rendering-a-2d-game-in-3d-bd24ddbee6eb) — General approach article
