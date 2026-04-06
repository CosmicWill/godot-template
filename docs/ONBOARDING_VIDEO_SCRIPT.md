# Onboarding Guide — Educational Video Script (15 min)
*Spoken narration for “Godot 4.6 Top-Down Shooter Template” — derived from `docs/ONBOARDING.md`*

**Target runtime:** ~15 minutes at a steady teaching pace (~140–150 wpm)  
**Tone:** Clear, friendly, tutorial-style — not hypey, minimal “algorithm bait.”

**Text-to-speech:** Use [`ONBOARDING_VIDEO_SCRIPT.tts.txt`](ONBOARDING_VIDEO_SCRIPT.tts.txt) instead of this file. It removes markdown, spells symbols for speech, splits CamelCase where helpful, and uses section markers (`===`) your TTS tool can split on.

---

## Cold open (0:00–0:35)

If you’re jumping into this repo — fixing bugs, adding content, or onboarding a teammate — you need a **mental map** first.

This isn’t “random scenes wired together.” It’s **three folder layers**, **shared Resources as state**, and **overlap-based data** instead of spaghetti node references.

By the end: you’ll know **where to put work**, how **`ResourceNode`** ties systems together, why **AreaTransmitter** exists, and what flips **fight mode** in an arena.

[ON-SCREEN: Title — “Godot Template — Architecture in One Pass”]

---

## Part 1 — Folders & the dependency rule (0:35–2:00)

**Three tiers:** **`core`**, **`systems`**, **`game`**.

**`core`** — engine-agnostic helpers: math, base resource types, utilities. Any Godot project could reuse them.

**`systems`** — reusable *game* systems: actor, weapons, damage, arena, camera, input, UI blocks. Top-down shooter genre — **not** this game’s specific slime or gun art.

**`game`** — *this* game: enemies, levels, screens, and the `.tres` files that tune everything.

**`assets`** — raw media. **`addons`** — editor plugins only.

**Rule of thumb:** reusable top-down → **`systems`**. This game’s boss or level → **`game`**. Generic glue → **`core`**.

**Scripts sit next to scenes** — no parallel `scripts/` vs `scenes/` trees in `core` or `systems`.

**Hard rule:** dependencies flow **`game` → `systems` → `core`** only — never upward.

[ON-SCREEN: Stack — `game` / `systems` / `core`, arrows down]

---

## Part 2 — Resources & ResourceNode (2:00–5:15)

**Main pattern:** systems talk through **shared Resource instances**, not long-distance node grabs.

Resources are **shared by reference** — same `.tres`, same data everywhere. HUD can mirror **health** without owning the player node. **`PersistentData`** plus autoloads let some of this **survive scene changes**.

**Types you’ll constantly see:**

- **`ReferenceNodeResource`** — “where’s the camera / player / spawn parent?” Register with `set_reference`, listen with `listen`; cleans up on exit.
- **`InstanceResource`** — spawn from a **string path** (not PackedScene — avoids cycles) + **pooling** via `PoolNode`.
- **`ValueResource`** — reactive state (`BoolResource`, `IntResource`, …) with `updated`.
- **`SaveableResource`** — save / load / reset hooks.
- **`TransmissionResource`** — payload for AreaTransmitter (damage, pickups, …).
- **`SoundResource`** — pitch, volume, retrigger, escalation — `play()` or `play_managed()`.

**`ResourceNode`** on an actor is a **named dictionary** of resources. Systems `get_resource("health")`, `get_resource("input")` — **weapon** and **mover** never reference each other directly.

**New stat in one line:** new `ValueResource` `.tres` → add **`ResourceNodeItem`** in editor → `get_resource("key")` from any script on that actor.

That’s the **spine** of the template.

---

## Part 3 — AreaTransmitter (5:15–6:45)

Damage, pickups, and environmental effects use **Area2D overlap**, not `get_collider()` callbacks everywhere.

**Transmitter** side: **`AreaTransmitter2D`** + child **`DataChannelTransmitter`** nodes, each with a **`TransmissionResource`** and a **`transmission_name`**.

**Receiver** side: **`AreaReceiver2D`** maps that name to a **callback**. No match → failed transmission; channels can still drive **VFX / audio** via success / failed / denied.

**New damage channel:** one `TransmissionResource` named e.g. `"fire_damage"` → wire a **`DataChannelTransmitter`** → on the target, **`add_receiver("fire_damage", callback)`** in `_ready()`.

---

## Part 4 — Actors, weapons, arena (6:45–10:30)

**Actors** build on **`systems/actor/actor.tscn`**: **MoverTopDown2D** (reads **`InputResource`** + stats), **SpriteFlip**, **DashAbility**, **DamageCooldown**, **VisualInvulnerability**, **ItemDrop**, **CharacterState**.

**Same input pipe for player and AI:** **`PlayerInput`** vs **`BotInput`** + helpers like **TargetFinder** / **ProximityAttack** — both write **`InputResource`**. Movement stays dumb; that’s the point.

**New enemy:** scene in **`game/actors/enemies`**, wire **`ResourceNode`**, **`InstanceResource`** in **`game/resources/actors/`**, add to **`SpawnWaveList`**.

**Weapons:** **`WeaponManager`** → **`Weapon`** (rotation, trigger, **`ProjectileSpawner`** + **`InstanceResource`**, kickback, spread). **Projectiles** stack mover, lifetime, impact, setup, hit limit, **`AreaTransmitter`** for damage.

**New weapon:** **`game/weapons`**, **`Projectile2D`** scene, projectile **`InstanceResource`** under **`game/resources/weapons/`**, **`WeaponItemResource`** + inventory.

**Arena:** **`ArenaStarter`** sets **`fight_mode_resource`**. **`EnemyWaveManager`** / **`EnemySpawner`** spawn through **`InstanceResource`** into a parent from **`ReferenceNodeResource`**. Waves finish → **`fight_mode_resource`** off → doors open. **`ValueResource`s** track fight mode, counts, wave index.

**New room:** base **`room_template`**, **SpawnPoints**, **`SpawnWaveList`**, **`ArenaStarter`**, **`ArenaDoorBlock`**.

---

## Part 5 — Boot, globals, audio, saves (10:30–12:30)

**Boot:** **`boot_load.tscn`** → **BootPreloader** (threaded preload) → load **`SaveableResource`s** from **`PersistentData.saveable_list`** → **`Transition.change_scene`** to title.

**Transitions:** **`Transition`** autoload — screenshot overlay, **background load**, shader dissolve. Call **`Transition.change_scene(path)`** anywhere.

**Screens** live under **`game/screens`** — title, pause, game over, rebinding, etc.

**Autoloads:** **SteamInit**, **SoundManager** (pooled audio), **Music**, **Transition**, **PersistentData** (saveables + extra dict).

**Audio:** **`SoundResource`** `.tres` files; buses stay in **`default_bus_layout.tres`** — Master → Music, Sounds.

**Saves:** extend **`SaveableResource`**, register in **`PersistentData`**, implement **`prepare_save` / `prepare_load` / `reset_resource`**, files under **`user://`**.

---

## Part 6 — Layers, pooling, input, workflow (12:30–14:15)

**Physics layers:** 1 Environment, 2 Player, 3 Enemy, 4 Navigation obstacle. **Projectile masks** follow **who owns the weapon** — player hits enemy layer, enemies hit player.

**Pooling:** frequent spawns get **`PoolNode`** — **`InstanceResource`** reuses instances instead of **`instantiate()`** every frame; essential for bullets and VFX.

**Input:** **`ActionResource`** + rebinding UI; **`InputResource`** on the actor; **`ControlTextureResource`** for prompt icons.

**Dev:** Godot **4.6**, **F5**; **gdtoolkit** lint/format (commands in **`ONBOARDING.md`**); **`P`** frame-step; **`[ + P`** unpause; LSP **6005**, DAP **6006**, remote **6007**. Style: **static typing**, **`class_name`**, **`@export` groups**, **`InstanceResource` uses paths**.

---

## Part 7 — Where to look & outro (14:15–15:00)

**Stuck?** Enemy → **`game/actors/enemies`** + actor **`InstanceResource`**. Weapon → **`game/weapons`** + weapon resources. Pickup → **`game/pickups`**. Sound → **`game/resources/sounds`**. Level → **`game/levels`**, **`room_template`**. Screen → **`game/screens`** + **`Transition`**. Persistence → **`SaveableResource`** + **`PersistentData`**. UI → **`game/hud`** / **`game/ui`**. Waves → **`SpawnWaveList`** + **`EnemyWaveManager`**.

Remember: **`game` → `systems` → `core`** — one direction only.

Don’t memorize every file — remember **folders**, **ResourceNode**, and **AreaTransmitter**. For tables and code, open **`docs/ONBOARDING.md`**.

Thanks for watching — build in the right layer.

[ON-SCREEN: “Full reference: `docs/ONBOARDING.md`”]

---

## Optional B-roll (short)

Folder tree · `ResourceNode` inspector · transmitter/receiver scene · `InstanceResource` `.tres` · `SpawnWaveList`

---

*End of script.*
