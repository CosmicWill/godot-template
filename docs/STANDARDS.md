# Project structure and engineering standards

This document captures **industry-consistent practices**, **software engineering norms**, and **Godot official guidance** for this template. The concrete target tree and migration steps live in [`RESTRUCTURE_PLAN.md`](RESTRUCTURE_PLAN.md).

## Goals

| Goal | Practice |
|------|----------|
| **Feature ownership** | Organize by game domain (combat, inventory, level) so a slice is navigable as one place—not only by file type. |
| **Scalable navigation** | Structure stays understandable as asset and script counts grow. |
| **Stable references** | Controlled renames, consistent naming, and migration tooling for string paths (`InstanceResource.scene_path`, `load()`, etc.). |
| **Clear boundaries** | Engine-agnostic utilities, reusable gameplay frameworks, and this game’s content are separable for reuse, testing, and licensing. |

## Industry and studio conventions

- **Feature-first layout** — Prefer folders like `characters/`, `weapons/`, `levels/` over dumping everything into global `meshes/`, `textures/`, or `scripts/` trees. File format is secondary to **what the game is**.
- **Naming discipline** — Use a single project-wide convention for folders and files so search, automation, and collaboration stay predictable; add **prefixes** where they clarify asset role (e.g. texture vs sprite vs audio).
- **Third-party isolation** — Keep vendor/editor extensions identifiable and updatable separately from first-party game code.
- **Optional ownership** — For teams, a short note per major feature folder (who owns it, entry scene) reduces onboarding cost.

## Software engineering standards

- **Layered dependencies** — Lower layers do not depend on upper layers.
  - **Core** — Engine-style utilities and base resources (math helpers, save/load base types, generic nodes): **no** references to specific enemies, levels, or title-specific UI.
  - **Systems** — Reusable frameworks for this genre (damage pipeline, weapons, arena waves): may use core; **avoid** importing concrete game content where a resource or interface suffices.
  - **Game** — Content and tuning for **this** product: actors, levels, screens, game `.tres` instances.
- **Data vs code** — Prefer configurable **resources** (`.tres`, data files) for balance and tuning; keep scripts thin at boundaries.
- **Testability** — Favor small, focused scripts and resource types; push scene wiring to composition so logic can be exercised or inspected without deep scene trees where practical.
- **Reproducible validation** — CI or local checks should include project import and parse/load smoke steps (see [`TOOLING.md`](TOOLING.md) and `CLAUDE.md` Godot CLI section).

## Godot engine standards

Official reference: [Project organization](https://docs.godotengine.org/en/stable/tutorials/best_practices/project_organization.html).

- **Scene-adjacent assets** — As the project grows, group assets **close to the scenes** that use them.
- **`snake_case`** — Folders and files use `snake_case` (C# scripts follow C# class naming where used).
- **Node names** — Use **PascalCase** for node names to match the editor’s built-in style.
- **Case sensitivity** — Treat the project as case-sensitive (Linux exports and PCK behavior); avoid path casing drift.
- **`addons/`** — Keep **third-party** material here (plugins and tracked third-party assets). Exception: third-party art tied to one character may live **next to that character** if that is clearer.
- **`.gdignore`** — Use on folders that must not be imported (e.g. large docs or raw dumps) to speed import and reduce dock clutter.

## Repository target layout (summary)

These names align the repo with the principles above. Full diagram and phases: [`RESTRUCTURE_PLAN.md`](RESTRUCTURE_PLAN.md).

| Area | Role |
|------|------|
| **`core/`** | Engine-agnostic utilities (successor to `great_games_library`): autoloads, base resources, static helpers, generic nodes. |
| **`systems/`** | Reusable gameplay frameworks (actor base, damage, weapons, arena, camera, input, transition, shared UI widgets). |
| **`game/`** | This title only: specific actors, weapons, levels, screens, HUD, game resource instances. |
| **`assets/`** | Raw media (images, audio, fonts, shaders) at a predictable root. |
| **`addons/`** | **Editor plugins and true addons only** (e.g. Kanban, Resource Manager)—not the main game tree. |

**Root constraints:** `project.godot`, `default_bus_layout.tres` (must stay at project root for Godot), and other engine-required paths as documented in `RESTRUCTURE_PLAN.md`.

## Checklist after structural changes

1. No missing resources in the FileSystem dock; main scene chain runs (boot → title → gameplay as applicable).
2. Autoload paths in `project.godot` resolve.
3. Grep for obsolete prefixes (e.g. old `res://addons/...` paths) until intentional leftovers only.
4. Run gdtoolkit linter/formatter on touched script trees per `TOOLING.md`.

---

*Inventory and system map: [`CODEBASE_MAP.md`](CODEBASE_MAP.md). Tooling: [`TOOLING.md`](TOOLING.md).*
