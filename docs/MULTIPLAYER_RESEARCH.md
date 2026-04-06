# Multiplayer Research

**Target:** 4-player online co-op
**Transport:** ENet (Godot built-in) + third-party relay for NAT traversal
**Join flow:** Friends-only / invite-based
**Engine:** Godot 4.6
**Status:** Research only — no implementation yet

---

## Contents

1. [Mode Selection](#1-mode-selection)
2. [Technology Stack](#2-technology-stack)
3. [Relay & Matchmaking Options](#3-relay--matchmaking-options)
4. [Authority Model](#4-authority-model)
5. [Architecture Impact Analysis](#5-architecture-impact-analysis)
6. [4-Player Specific Considerations](#6-4-player-specific-considerations)
7. [Implementation Roadmap](#7-implementation-roadmap)
8. [Save Data & Persistence](#8-save-data--persistence)
9. [Risk Register](#9-risk-register)
10. [Open Questions](#10-open-questions)

---

## 1. Mode Selection

### Target: 4-Player Online Co-op

All four players fight the same enemy waves in a shared arena. Friends-only sessions via invite code or direct invite.

**Why co-op works well with this template:**
- `TargetFinder.gd` already supports `MAX_TARGET = 10` on physics Layer 2. Multiple player bodies are detected automatically.
- `EnemySpawner` and wave system never reference player entities — player-count-agnostic already.
- `AreaTransmitter` / `AreaReceiver` damage is area-overlap based — nothing hardcodes a single target.

**Recommended phasing:**
```
Phase 0 (optional)   Local co-op — 2–4 players, gamepads, shared screen
                     Validates multi-entity architecture without networking.

Phase 1              Online co-op — 2 players first (easier to test)
                     Core networking infrastructure.

Phase 2              Scale to 4 players
                     Camera, HUD, spawn count, session size.
```

---

## 2. Technology Stack

### Transport: ENet via Godot MultiplayerAPI

`ENetMultiplayerPeer` is Godot's built-in reliable UDP transport. It integrates directly with `MultiplayerAPI`, `@rpc`, `MultiplayerSpawner`, and `MultiplayerSynchronizer` — no additional addons required for the game-networking layer.

```gdscript
# Host
var peer := ENetMultiplayerPeer.new()
peer.create_server(PORT, MAX_PLAYERS)
multiplayer.multiplayer_peer = peer

# Client
var peer := ENetMultiplayerPeer.new()
peer.create_client(host_address, PORT)
multiplayer.multiplayer_peer = peer
```

**Pros:**
- No extra dependencies beyond Godot itself
- Well-documented; first-class Godot support
- Lower latency than WebSocket (UDP vs TCP)
- Works cleanly with all Godot multiplayer primitives

**Cons:**
- ENet alone requires a reachable IP address. Direct peer-to-peer over the internet usually requires port forwarding.
- No built-in NAT punch-through or relay
- No built-in lobby/session discovery

**Solution:** Use a third-party relay and matchmaking service to handle NAT traversal and session management. The game still uses ENet for all gameplay data. See Section 3.

---

### Godot Multiplayer Primitives

These are used regardless of relay choice:

| Primitive | Purpose |
|---|---|
| `MultiplayerAPI` | Core API — manages peers, authority, RPCs |
| `@rpc` annotations | Remote procedure calls between peers |
| `MultiplayerSpawner` | Replicates node instantiation across all peers |
| `MultiplayerSynchronizer` | Continuously syncs node properties to all peers |
| `set_multiplayer_authority(peer_id)` | Assigns ownership of a node to a specific peer |
| `is_multiplayer_authority()` | Check if the local peer owns this node |
| `multiplayer.get_unique_id()` | Local peer's ID (1 = server/host) |

---

## 3. Relay & Matchmaking Options

ENet needs a known address to connect to. For internet play without port forwarding, all players connect to a **relay server** (a machine with a public IP). The relay forwards packets between peers or acts as an authoritative game server.

Three options are evaluated below.

---

### Option A: Nakama (Recommended)

[Nakama](https://heroiclabs.com/nakama/) is an open-source game backend by Heroic Labs. It handles accounts, matchmaking, real-time messaging, leaderboards, and storage. It can be self-hosted or used via their cloud (Heroic Cloud).

**How it integrates with ENet:**

Nakama does NOT replace ENet. It acts as the **lobby/session layer**:

```
Nakama (WebSocket)   →  Session management: create room, invite code, player list
                        Players signal "ready" via Nakama

ENet (UDP)          →  All gameplay data once the session starts
                        All 4 players ENet-connect to host or dedicated relay server
```

**Flow:**
1. Player A creates a Nakama match → gets a match ID (invite code)
2. Player A shares code with friends (out-of-band: Discord, Steam chat, etc.)
3. Players B/C/D join Nakama match using the code
4. Nakama signals all players when session is full/ready
5. Host opens an ENet server (or connects to a relay)
6. All players ENet-connect and gameplay starts

**Gotcha: Nakama does not relay ENet UDP packets.** Its real-time layer is WebSocket-based. For actual ENet gameplay traffic to reach all players, you still need either:
- All players connecting to a **host who has a public IP or port forward** (listen server)
- All players connecting to a **dedicated Godot headless server** (recommended)

**Godot 4 SDK:** Nakama has an official Godot client SDK (`nakama-godot`) supporting GDScript and C#. Last confirmed stable with Godot 4.x.

**Cost:** Free tier (Heroic Cloud) supports low traffic. Self-hosting is free (needs a VPS to run the server).

---

### Option B: Photon Realtime

[Photon Realtime](https://www.photonengine.com/realtime) is a relay-as-a-service. It handles NAT traversal and relays packets through Photon's servers — no dedicated server needed.

**Key difference from Nakama:** Photon actually relays the **game packets**, not just lobby management. Players connect to Photon's relay servers; Photon forwards UDP between them.

**Godot 4 support:**
- Photon Fusion (their modern SDK) is Unity-only.
- Photon PUN2 has a community Godot port, but it is not officially supported and maintenance is uncertain.
- Using Photon Realtime (low-level SDK) with Godot requires binding the native C++ SDK via GDExtension — significant upfront work.

**Verdict:** Poor fit for Godot 4.6. The Unity-first focus means Godot support is community-maintained and fragile.

---

### Option C: Self-Hosted Godot Relay Server

Run a **Godot headless server** on a cheap VPS ($5–10/month, e.g. Digital Ocean, Hetzner). All 4 players ENet-connect to this server. The server runs game logic (authoritative host model). A simple REST or WebSocket API on the same VPS handles lobby management (create room, join by code).

**Pros:**
- Full control over relay and game logic
- ENet throughout — no protocol mixing
- No third-party service dependency
- The same Godot codebase runs as the server (export with `--headless`)

**Cons:**
- Operational cost ($5–10/month server)
- You maintain the server infrastructure
- Need to handle server scaling if more than one session runs simultaneously (unlikely for 4-player friends-only)

**Godot headless server export:**
```bash
godot --headless --path . --export-release "Linux/X11" server.x86_64
./server.x86_64 --headless
```

**Verdict:** Best long-term architecture for a shipped product. Pairs cleanly with ENet and authoritative game logic. A simple lobby API (even a single Node.js or Python endpoint) is enough for friends-only sessions.

---

### Comparison

| | Nakama | Photon | Self-hosted Relay |
|---|---|---|---|
| ENet for gameplay | ✅ (still need relay for NAT) | ❌ (uses own transport) | ✅ |
| NAT traversal | ❌ (relay for lobby only) | ✅ | ✅ (server has public IP) |
| Godot 4 support | ✅ Official SDK | ⚠️ Community only | ✅ Native |
| Cost | Free tier / self-host | Free tier (limited) | ~$5/month VPS |
| Lobby/matchmaking | ✅ Built-in | ✅ Built-in | Manual (simple API needed) |
| Game data relay | ❌ WebSocket only | ✅ | ✅ |
| Ops burden | Low (cloud) / Medium (self-host) | Low | Medium |

### Recommended Combination

**Nakama (cloud free tier) for lobby + Self-hosted Godot relay server for ENet gameplay.**

Or more simply: **Self-hosted Godot headless server** handles both relay and lobby. It's the fewest moving parts for a friends-only game with up to 4 concurrent players.

The game does not need Nakama if the session model is:
- Host starts a session → server generates a 6-character room code
- Host shares code via Discord/Steam chat
- Up to 3 friends enter the code → connect to the session

That lobby logic is ~50 lines of GDScript on the server side.

---

## 4. Authority Model

### Options

**Option A: Authoritative Server/Host**
Server runs all game simulation. Clients send inputs; server sends authoritative state.

```
Client → inputs → Server
Server simulates physics, enemy AI, damage, pickups
Server → positions, health, game state → all clients
```

**Pros:** Cheat-resistant. No state divergence. Simpler to reason about.
**Cons:** Input latency for clients equals network RTT. For a fast-paced dodge/dash game, 60–100ms RTT is perceptible. Requires client-side prediction to feel good (significant extra complexity).

---

**Option B: Client Authority on Own Player**
Each client is authoritative over their own player (position, dash, aim). Server/host is authoritative over enemies, world state, damage resolution.

```
Client → own position + aim → broadcast to all peers
Server/host → enemy positions, wave state, damage validation → all clients
```

**Pros:** Zero input lag for local player. Simpler to implement than full prediction.
**Cons:** Clients can "cheat" their own position. Acceptable for a co-op game with trusted friends.

---

### Recommendation for This Template

**Option B — client authority on own player** — is the right starting point for a friends-only co-op game. The game has no PvP; cheating against enemies in your own session has no meaningful consequence.

**Responsibility split:**

| Subsystem | Authority |
|---|---|
| Local player position / velocity / dash | Client (own peer) |
| Local player aim direction | Client |
| Player damage taken | Host validates (enemy hit checks), client applies |
| Projectile spawning | Client spawns locally; replicates via `MultiplayerSpawner` |
| Projectile hit registration | Client reports to host; host validates |
| Enemy AI + movement | Host/server only |
| Wave state (fight_mode, wave_number) | Host/server only |
| Score | Host/server only |
| Pickups (coin/health spawning + collection) | Host/server authoritative (prevent double-collect) |

If PvP modes are added later, revisit with full authoritative server + client-side prediction.

---

## 5. Architecture Impact Analysis

### Impact Key
- 🟢 **Green** — Works as-is
- 🟡 **Yellow** — Minor change, low risk
- 🟠 **Orange** — Moderate refactoring
- 🔴 **Red** — Major change, high risk

---

### 5.1 Global Player Reference — 🔴 Red

**Files:** `core/resources/ReferenceNodeResource/ReferenceNodeResource.gd`, `game/resources/global/player_reference.tres`

`ReferenceNodeResource.node` holds **one node**. With 4 players, this breaks: camera, pickup homing, game-over detection, and coin collection all assume a single player.

**Change:** Create `PlayerRegistry` — a dictionary of player nodes keyed by peer ID. Keep `player_reference.tres` as a convenience alias for the local player (backwards-compatible for single-player code paths).

```gdscript
# systems/multiplayer/PlayerRegistry.gd
class_name PlayerRegistry
extends Node

var players: Dictionary = {}  # peer_id -> Node2D

func register(peer_id: int, node: Node2D) -> void:
    players[peer_id] = node

func unregister(peer_id: int) -> void:
    players.erase(peer_id)

func get_closest(from: Vector2) -> Node2D:
    var nearest: Node2D
    var nearest_dist := INF
    for node in players.values():
        var d := from.distance_squared_to(node.global_position)
        if d < nearest_dist:
            nearest_dist = d
            nearest = node
    return nearest

func get_local() -> Node2D:
    return players.get(multiplayer.get_unique_id())
```

---

### 5.2 Shared Player Health (`make_unique = false`) — 🟡 Yellow

**File:** `game/actors/player/player.tscn`

The health `ResourceNodeItem` has `make_unique = false` — all player instances share one `HealthResource`. With 4 players this means one player taking damage affects all players' health bars.

**Change:** Set `make_unique = true` on the health `ResourceNodeItem` in `player.tscn`. `ResourceNode._ready()` already handles duplication when this flag is set.

**Audit needed:** Check whether any code loads `game/resources/health/player_health.tres` directly instead of going through a player's `ResourceNode`. Those accesses would still see the shared resource.

---

### 5.3 Static Enemy Tracking — 🟡 Yellow

**File:** `game/actors/ai/ActiveEnemy.gd`

`static var root`, `static var active_instances` are globally shared. In co-op, all 4 players fight the same enemies — this is **correct**. Static shared state is fine.

**Change:** Gate `EnemySpawner._process()` behind `multiplayer.is_server()` so only the host/server runs spawn logic. Clients receive enemies via `MultiplayerSpawner`.

```gdscript
func _process(delta: float) -> void:
    if not multiplayer.is_server():
        return
    # ... existing spawn logic
```

---

### 5.4 Single InputResource — 🟠 Orange

**File:** `game/actors/player/PlayerInput.gd`

Reads from global `Input` singleton — no device filtering. Designed for one player.

**For online multiplayer:** Each player only runs `PlayerInput` for their own character. Remote player nodes receive state via `MultiplayerSynchronizer`; their `InputResource` is populated by a `NetworkInputProxy` from synced data. Gate with:

```gdscript
func _ready() -> void:
    if not is_multiplayer_authority():
        set_physics_process(false)
        return
```

**For local co-op (Phase 0):** `Input.get_axis()` is device-agnostic. Need device-indexed input: add `@export var device_id: int = 0` and route all input through `_input(event)` checking `event.device == device_id`. ActionResource needs per-player action name prefixes or the same actions registered per device.

---

### 5.5 Global Game State — 🟢 Green

**Resources:** `fight_mode_resource.tres`, `wave_number_resource.tres`, `enemy_count_resource.tres`, `score_resource.tres`

Shared world state is **correct** for co-op. All 4 players experience the same waves.

**Change:** Add `GameStateSync` node to the arena scene. Host writes; a `MultiplayerSynchronizer` replicates to clients. No changes to existing resource classes.

---

### 5.6 Camera — 🟠 Orange

**Files:** `systems/camera/CameraFollow2D.gd`, `game/actors/player/CameraPositionSetter.gd`

**For online co-op:** Each client runs `CameraPositionSetter` for their local player only. Camera follows only their player. **No change needed for online.**

**For local co-op (shared screen, 4 players):** Need a multi-target camera. Compute centroid of all player positions; adjust zoom so all players remain visible. This is a new `CameraMultiTarget` script replacing `CameraFollow2D` for local mode.

---

### 5.7 Pickup Targeting — 🟡 Yellow

**File:** `systems/pickups/CollectingPoint.gd`

Coins home to `player_reference.node.global_position`.

**Change:** Two lines — replace with nearest-player lookup:

```gdscript
# Before
var target := player_reference.node.global_position

# After
var target := PlayerRegistry.get_closest(moved_node.global_position).global_position
```

---

### 5.8 Audio Singletons — 🟢 Green

Each client plays sounds based on local events. `SoundManager` and `Music` are local. **No changes needed.**

---

### 5.9 Scene Transitions — 🟠 Orange

**Files:** `systems/transition/TransitionManager.gd`, `game/scripts/PlayerSpawner.gd`

`TransitionManager` uses `get_tree().change_scene_to_packed()` locally. With 4 players, scene changes must be coordinated.

**Changes:**
1. Host triggers scene change via RPC (`call_local, reliable`) so all peers load the same scene simultaneously.
2. `PlayerSpawner` must spawn all connected players, not just one. `MultiplayerSpawner` in arena/room scenes handles remote player instantiation.
3. Transition visual (shader dissolve) remains local — each client plays their own animation.

```gdscript
@rpc("authority", "call_local", "reliable")
func change_scene(path: String) -> void:
    Transition.go(path)
```

---

### 5.10 Damage Owner — 🟢 Green

`DamageResource.owner` is per-entity via `DamageSetup`. Kill attribution naturally identifies the source. **No changes needed.**

---

### 5.11 InstanceResource vs MultiplayerSpawner — 🔴 Red

**File:** `core/resources/InstanceResource/InstanceResource.gd`

`InstanceResource.instance()` calls `add_child.call_deferred()` directly. It bypasses `MultiplayerSpawner`, which must control instantiation of networked nodes to assign consistent network IDs across all peers.

**Recommended approach: Hybrid classification**

| Entity type | Approach |
|---|---|
| Players | `MultiplayerSpawner` |
| Enemies | `MultiplayerSpawner` |
| Pickups (coins, health, items) | `MultiplayerSpawner` (host-authoritative collection) |
| Projectiles | `MultiplayerSpawner` (client-spawned, replicated) |
| VFX (explosions, blood, after-images) | `InstanceResource` (local-only, cosmetic) |
| Damage numbers | `InstanceResource` (local-only, cosmetic) |
| Death animations | `InstanceResource` (local-only, cosmetic) |
| Sound instances | `InstanceResource` (local-only) |

Networked entities use `MultiplayerSpawner` and must not use `PoolNode` recycling (Godot's `MultiplayerSpawner` requires fresh instantiation per spawn). Local-only entities keep `InstanceResource` with pooling unchanged.

---

### Summary Table

| System | Impact | Key Change |
|---|---|---|
| player_reference (single node) | 🔴 Red | PlayerRegistry keyed by peer ID |
| Shared player health | 🟡 Yellow | `make_unique = true` in player.tscn |
| Static enemy tracking | 🟡 Yellow | Gate EnemySpawner on `is_server()` |
| Single InputResource | 🟠 Orange | Disable PlayerInput on non-authority nodes |
| Global game state | 🟢 Green | Sync read-only to clients via Synchronizer |
| Camera | 🟠 Orange | Online: no change. Local: multi-target camera |
| Pickup targeting | 🟡 Yellow | Switch to PlayerRegistry.get_closest() |
| Audio singletons | 🟢 Green | No change |
| Scene transitions | 🟠 Orange | RPC-based coordinated load |
| Damage owner | 🟢 Green | No change |
| InstanceResource vs MultiplayerSpawner | 🔴 Red | Hybrid: MultiplayerSpawner for gameplay entities, InstanceResource for cosmetics |

---

## 6. 4-Player Specific Considerations

These are concerns that arise specifically from scaling from 2 to 4 players, beyond the general multiplayer architecture changes.

### 6.1 HUD — 4 Player Displays

The current HUD (`game/hud/game_hud.tscn`) is designed for one player. With 4 players, every connected client needs to see:
- Their own health bar
- Their own weapon/ammo display
- Optionally: other players' health (small indicators)

**Approach:**
- Local player's HUD stays as-is (full bottom panel)
- Other players' health shown as small portrait indicators (common co-op pattern)
- Per-client: HUD reads from `PlayerRegistry.get_local()` for the main display
- Mini-indicators: HUD listens to `PlayerRegistry.players` and creates one small widget per remote player

### 6.2 Spawn Points — 4 Slots

`PlayerSpawner` currently spawns one player at a fixed position. Rooms need 4 distinct spawn positions — either separated positions in the scene or calculated offsets.

**Approach:** Add 4 `PlayerSpawnPoint` markers to room scenes. `PlayerSpawner` assigns each peer to one spawn point in order of connection.

### 6.3 Camera — 4-Player Shared Screen (Local Co-op)

For 4 players on one screen, the camera must keep all players visible while they spread out.

**Common pattern:**
```gdscript
# CameraMultiTarget.gd
func _physics_process(delta: float) -> void:
    var positions := PlayerRegistry.players.values().map(func(p): return p.global_position)
    var center := positions.reduce(func(a, b): return a + b) / positions.size()
    var max_dist := positions.map(func(p): return center.distance_to(p)).max()
    global_position = global_position.lerp(center, lerp_speed * delta)
    zoom = Vector2.ONE * clamp(BASE_ZOOM / (max_dist / ZOOM_SCALE + 1.0), MIN_ZOOM, MAX_ZOOM)
```

For online 4-player: each client has their own camera following only their character. No shared-screen logic needed.

### 6.4 Network Traffic at 4 Players

With client authority on own player:
- 4 players each broadcasting position + aim at 60Hz
- `MultiplayerSynchronizer` default sync rate is configurable (can throttle to 20–30Hz for position, keep damage/events reliable)

**Properties to sync per player** (can reduce bandwidth by lowering sync rate):
| Property | Sync rate | Channel |
|---|---|---|
| `position` | 20–30Hz, unreliable | Continuous |
| `aim_direction` | 20–30Hz, unreliable | Continuous |
| `health.hp` | On-change, reliable | Event |
| `is_dashing` | On-change, reliable | Event |

Weapons/projectiles: `MultiplayerSpawner` fires reliably on spawn, no continuous sync needed.

### 6.5 Game Over with 4 Players

**Current:** `GameOverDetect` watches a single player's health.

**With 4 players — design decision needed:**
- **All dead:** Game over when all 4 players are dead. Last player standing can still fight.
- **Any dead:** Game over when the first player dies. More punishing.
- **Respawn:** Dead players respawn after a delay or when the wave ends.

The current `GameOverDetect` needs to become aware of `PlayerRegistry`. The simplest implementation: game over when `PlayerRegistry.players` is empty (all player nodes gone).

---

## 7. Implementation Roadmap

### Phase 0: Local Co-op (Optional — No Networking)

Validates multi-entity architecture. Recommended before adding networking.

1. Fix health: `make_unique = true` in player.tscn
2. Create `PlayerRegistry` autoload
3. Update `CollectingPoint` → `PlayerRegistry.get_closest()`
4. Update `GameOverDetect` → check all players dead
5. Add device-ID filtering to `PlayerInput`
6. Modify `PlayerSpawner` to spawn N players at distinct spawn points
7. Add 4 spawn point markers to room scenes
8. Implement `CameraMultiTarget` (centroid + zoom)
9. Add per-player HUD indicators
10. Test with 2–4 gamepads

---

### Phase 1: Online Co-op (2 Players First)

Build and test with 2 players before scaling to 4.

**1.1 Server infrastructure**
- Export Godot project as headless Linux server
- Set up VPS (Digital Ocean, Hetzner) or use local machine for testing
- Simple lobby API: create room (→ room code), join room (→ host address + port), list players in room

**1.2 NetworkManager (`systems/multiplayer/NetworkManager.gd`)**
```gdscript
func host_game(port: int) -> void:
    var peer := ENetMultiplayerPeer.new()
    peer.create_server(port, MAX_PLAYERS)
    multiplayer.multiplayer_peer = peer
    multiplayer.peer_connected.connect(_on_peer_connected)
    multiplayer.peer_disconnected.connect(_on_peer_disconnected)

func join_game(address: String, port: int) -> void:
    var peer := ENetMultiplayerPeer.new()
    peer.create_client(address, port)
    multiplayer.multiplayer_peer = peer
```

**1.3 Lobby Screen (`game/screens/lobby.tscn`)**
- Input field: enter room code
- Player list: show connected players with ready states
- Host: "Start Game" button (enabled when all ready)
- Simple 6-character room code display for sharing

**1.4 Player Spawning**
- Add `MultiplayerSpawner` to room/arena scenes, configured with player scene path
- On `peer_connected` (server side): call `MultiplayerSpawner.spawn()` with spawn position config
- Spawned player node: `set_multiplayer_authority(peer_id)`
- `PlayerRegistry.register(peer_id, node)` called from player's `_ready()`

**1.5 Player Sync (`MultiplayerSynchronizer` on player scene)**
```
Synced properties:
  position          (unreliable, 20Hz)
  aim_direction     (unreliable, 20Hz)
  health.hp         (reliable, on-change) ← note: needs wrapper property
```

Gate `PlayerInput._physics_process` behind `is_multiplayer_authority()`.

**1.6 Enemy Sync**
- `EnemySpawner._process()` gated on `multiplayer.is_server()`
- Add `MultiplayerSpawner` for enemies in arena scene
- Add `MultiplayerSynchronizer` on enemy base scene: sync `position`, `health`
- Enemy AI runs on server only

**1.7 Game State Sync**
- `GameStateSync` node with `MultiplayerSynchronizer`: syncs `fight_mode`, `wave_number`, `enemy_count`, `score`
- Host writes; clients read-only

**1.8 Scene Transitions**
- RPC-based coordinated scene changes (see Section 5.9)
- Post-load: server signals all clients when to unpause

**1.9 Disconnect Handling**
- `peer_disconnected` → `PlayerRegistry.unregister(peer_id)` → remove player node
- Display "Player X disconnected" toast
- If server disconnects: show error and return to lobby

---

### Phase 2: Scale to 4 Players

With Phase 1 stable:

1. Increase `MAX_PLAYERS` constant from 2 to 4
2. Add 4 spawn point markers to all room scenes
3. Add per-player mini HUD indicators (small health bars for remote players)
4. Implement 4-player `CameraMultiTarget` (online: N/A — each client has own camera)
5. Tune `MultiplayerSynchronizer` sync rates for 4× traffic
6. Update `GameOverDetect` for configurable game-over condition (all-dead vs any-dead)
7. Load-test: run 4 clients + server, measure bandwidth and frame time

---

## 8. Save Data & Persistence

### Current System

`PersistentData.gd` stores `SaveableResource` instances. `SteamInit.gd` sets `SaveableResource.save_type = STEAM` when Steam is present (though Steam save path is not yet implemented). Currently falls back to local `user://` file saving.

### Settings (Always Per-Machine)

Audio, graphics, and key binding settings are stored locally on each machine. These are **never synchronized**. Each player uses their own settings. **No changes needed.**

### Session vs Persistent Progression

**Decision needed before implementation:**

| Model | Description | Complexity |
|---|---|---|
| Per-session | Weapons/score reset each run. No cross-session persistence for multiplayer. | Low |
| Per-player persistent | Each player keeps unlocks/progress. Synced to their own local save. | Medium |
| Shared session persistent | Session state saved to host. All players share unlock progression. | High |

**Recommendation:** Start with **per-session** (reset each run). Fits the template's wave-arena structure. Simplifies multiplayer significantly — no save sync required.

### If Persistent Progression Is Added

- Each client loads their local save on game start (already works)
- At session start, each client broadcasts their relevant state (weapon unlocks, stats) to host via RPC
- Host holds the authoritative session state for all players
- At session end, host sends each client their updated state → client saves locally
- The `SaveableResource.SaveType.STEAM` path should be implemented if using Steam Cloud Saves

### Score & Leaderboards

If a leaderboard is added:
- Score is tracked on the host/server
- At session end, each player's contribution is tallied
- Per-player score is submitted locally from each client (avoids one client submitting on behalf of others)

---

## 9. Risk Register

| Risk | Severity | Likelihood | Mitigation |
|---|---|---|---|
| `InstanceResource` pooling incompatible with `MultiplayerSpawner` | High | High | Classify entities as networked vs local-only. Networked entities use `MultiplayerSpawner` only (no pooling). |
| `MultiplayerSynchronizer` cannot sync Resource properties via `ResourceNode` dict paths | High | Medium | Expose synced properties as wrapper properties directly on the node. E.g., `var hp: float` on CharacterBody2D that reads/writes through ResourceNode. |
| Physics non-determinism (`MoverTopDown2D` + `move_and_slide`) | High | High | Use client authority on own player — clients don't re-simulate each other's physics. Server only simulates enemies. |
| No stable entity ID for non-`MultiplayerSpawner` entities | Medium | Medium | All networked entities must go through `MultiplayerSpawner` to get Godot-assigned network IDs. |
| NAT traversal with ENet (peer-to-peer) | Medium | High | Use dedicated headless relay server with public IP. Players ENet-connect to server, not directly to each other. |
| Scene transition desync (clients load different scenes or out of order) | Medium | Low | Use `call_local` RPC for scene load. Add ready-check before unpausing. |
| 4 players × 60Hz sync = bandwidth budget exceeded | Low | Low | Throttle `MultiplayerSynchronizer` to 20–30Hz for position. Use `on_change` / reliable for events. |
| Host disconnects = session ends | Low | Medium | Acceptable for friends-only sessions. Document as known limitation. Host migration is high complexity, not worth it for v1. |

---

## 10. Open Questions

### Technical

1. **`MultiplayerSynchronizer` + `ResourceNode`:** Can the synchronizer follow a path like `$ResourceNode:dictionary:health:hp`? Or must synced state be direct node properties? This determines whether wrapper properties are needed on player/enemy nodes and how much the ResourceNode architecture has to change for networked entities.

2. **`MultiplayerSpawner` + `PoolNode`:** The `PoolNode` recycling system in `InstanceResource` returns nodes to a pool instead of freeing them. Can `MultiplayerSpawner` use pooled nodes, or does it require `instantiate()` fresh every time? If the latter, object pooling must be disabled for all networked entities.

3. **`@rpc` on non-node objects:** `InputResource` and other Resources are not Nodes. RPCs in Godot 4 can only be defined on Node subclasses. All network calls must therefore be on Nodes — Resources can only be updated as a result of RPC calls on nodes, not called directly. Confirm this constraint doesn't require major restructuring.

4. **Dedicated server export — SteamInit conflict:** `SteamInit.gd` quits the game if Steam is not running (`initialize_response["status"] > 0` → `get_tree().quit()`). A headless server process won't have Steam running. The server must skip Steam initialization. Needs a build flag or feature tag: `if not OS.has_feature("dedicated_server"): # init Steam`.

5. **Nakama Godot SDK — Godot 4.6 compatibility:** The `nakama-godot` SDK was tested against Godot 4.x. Verify it works with 4.6 before committing to Nakama for lobby management.

### Design

6. **Game over condition for 4 players:** All dead? Any dead? Respawn? This affects `GameOverDetect` and the session flow significantly.

7. **Pickup ownership:** When a coin or health pack drops mid-wave, can any player collect it? Or does it auto-assign to the nearest player? Currently coins home to nearest player — this works for 4 players as-is once `CollectingPoint` uses `PlayerRegistry.get_closest()`.

8. **Friendly fire:** Can player projectiles hit other players? The `AreaTransmitter` / physics layer system makes this a single mask change. Intentional design decision.

9. **Session rejoin:** If a player disconnects mid-session, can they reconnect and continue? Or does disconnection mean they're out? For v1, out is simpler.

10. **Room code distribution:** With no built-in lobby system, how do players share the room code? Discord/Steam chat is the assumed answer for friends-only. Is that acceptable UX?

### Infrastructure

11. **App ID:** `SteamInit` uses app_id `480` (Spacewar test). For a real Steam game, all Steam features (leaderboards, friends, etc.) need a real App ID. When does this project get one?

12. **Dedicated server hosting:** If using a VPS relay server — what region? Single region (e.g. US East) or multi-region? For a friends-only game with known players, a single region is fine initially.

---

## Appendix: New Files by Phase

### Phase 0 (Local Co-op)
```
systems/multiplayer/PlayerRegistry.gd
game/actors/player/CameraMultiTarget.gd
```

### Phase 1 (Online Co-op)
```
systems/multiplayer/NetworkManager.gd
systems/multiplayer/PlayerNetworkSync.gd
systems/multiplayer/GameStateSync.gd
systems/multiplayer/NetworkInputProxy.gd
game/screens/lobby.tscn
game/screens/LobbyManager.gd
```

### Scenes modified in Phase 1
```
systems/actor/actor.tscn                + MultiplayerSynchronizer
game/actors/player/player.tscn         + multiplayer_authority setup, hp wrapper property
game/actors/enemies/*/enemy.tscn       + MultiplayerSynchronizer
systems/arena/arena_entry.tscn         + MultiplayerSpawner (players + enemies)
game/levels/room_0.tscn etc.           + 4 spawn point markers
game/scripts/PlayerSpawner.gd          multi-player spawn logic
systems/transition/TransitionManager.gd  RPC-based scene change
core/autoload/SteamInit.gd             skip init on dedicated server
```
