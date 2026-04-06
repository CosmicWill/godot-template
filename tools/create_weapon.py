#!/usr/bin/env python3
"""Generate boilerplate files for a new weapon in the Godot project.

Usage:
    python tools/create_weapon.py fire_staff --archetype staff --damage-type fire
    python tools/create_weapon.py crossbow --archetype gun --fire-rate 0.8
    python tools/create_weapon.py battle_axe --archetype melee --kickback 80
"""

import argparse
import os
import re
import struct
import sys
import zlib
from pathlib import Path


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parent.parent

DAMAGE_TYPES = {
    "physical": 0, "fire": 1, "ice": 2, "lightning": 3,
    "poison": 4, "acid": 5, "magnetic": 6, "blood": 7,
    "dark": 8, "arcane": 9,
}

ARCHETYPES = {
    "gun": dict(
        inherits="res://game/weapons/gun/gun.tscn",
        movement_type=0,        # PROJECTILE
        fire_rate=0.5,
        damage=10.0,
        damage_type="physical",
        kickback=30.0,
        proj_speed=120.0,
        proj_lifetime=2.0,
        hit_limit=1,
        spread=5.0,
        weapon_color=(100, 200, 100, 255),
        proj_color=(180, 255, 180, 255),
    ),
    "staff": dict(
        inherits="res://game/weapons/gun/gun.tscn",
        movement_type=0,        # PROJECTILE (straight bolt)
        fire_rate=0.8,
        damage=15.0,
        damage_type="arcane",
        kickback=0.0,
        proj_speed=80.0,
        proj_lifetime=1.5,
        hit_limit=1,
        spread=0.0,
        weapon_color=(100, 100, 255, 255),
        proj_color=(180, 180, 255, 255),
    ),
    "melee": dict(
        inherits="res://game/weapons/gun/gun.tscn",
        movement_type=0,        # PROJECTILE (short-range slash)
        fire_rate=0.3,
        damage=20.0,
        damage_type="physical",
        kickback=-30.0,
        proj_speed=60.0,
        proj_lifetime=0.27,
        hit_limit=3,
        spread=0.0,
        weapon_color=(255, 100, 100, 255),
        proj_color=(255, 180, 180, 255),
    ),
}

# Node indices in base scenes (from reading the .tscn files)
# Base projectile.tscn children of root:
#   0=ProjectileSetup 1=ProjectileMover 2=AreaTransmitter2D 3=RotatedNode
#   4=ProjectileRotation 5=ProjectileImpact 6=HitLimit 7=ProjectileLifetime
#   8=PoolNode
# RotatedNode children: 0=Sprite2D
#
# gun.tscn (inherits weapon.tscn) children of root:
#   0=RotatedNode 1=WeaponRotation 2=WeaponKickback 3=WeaponTrigger
#   4=ProjectileSpawner
# RotatedNode children: 0=Sprite2D (with AnimationPlayer child)
# WeaponTrigger children: 0=ProjectileInterval 1=AnimationTrigger
# ProjectileSpawner children: 0=SpreadShot


# ---------------------------------------------------------------------------
# PNG generation (stdlib only)
# ---------------------------------------------------------------------------

def _png_chunk(chunk_type: bytes, data: bytes) -> bytes:
    """Build a single PNG chunk with CRC."""
    chunk = chunk_type + data
    return struct.pack(">I", len(data)) + chunk + struct.pack(">I", zlib.crc32(chunk) & 0xFFFFFFFF)


def generate_png(width: int, height: int, r: int, g: int, b: int, a: int = 255) -> bytes:
    """Generate a minimal valid RGBA PNG with a solid color."""
    header = b"\x89PNG\r\n\x1a\n"
    ihdr = struct.pack(">IIBBBBB", width, height, 8, 6, 0, 0, 0)  # 8-bit RGBA
    # Scanlines: each row starts with filter byte 0 (None)
    row = b"\x00" + bytes([r, g, b, a]) * width
    raw = row * height
    idat = zlib.compress(raw)
    return header + _png_chunk(b"IHDR", ihdr) + _png_chunk(b"IDAT", idat) + _png_chunk(b"IEND", b"")


# ---------------------------------------------------------------------------
# Name helpers
# ---------------------------------------------------------------------------

def to_pascal(snake: str) -> str:
    """Convert snake_case to PascalCase."""
    return "".join(word.capitalize() for word in snake.split("_"))


def to_display(snake: str) -> str:
    """Convert snake_case to Title Case display name."""
    return " ".join(word.capitalize() for word in snake.split("_"))


# ---------------------------------------------------------------------------
# Template: projectile scene
# ---------------------------------------------------------------------------

def make_projectile_scene(cfg: dict) -> str:
    name = cfg["name"]
    pascal = to_pascal(name)
    return f"""\
[gd_scene load_steps=4 format=3]

[ext_resource type="PackedScene" path="res://systems/weapons/projectile/projectile.tscn" id="1_base"]
[ext_resource type="Script" path="res://systems/damage/properties/DamageTypeResource.gd" id="2_dtype"]
[ext_resource type="Texture2D" path="res://assets/images/projectile/{name}_projectile.png" id="3_tex"]

[sub_resource type="Resource" id="Resource_dmg"]
script = ExtResource("2_dtype")
value = {cfg['damage']:.1f}
type = {DAMAGE_TYPES[cfg['damage_type']]}

[node name="{pascal}Projectile" instance=ExtResource("1_base")]
speed = {cfg['proj_speed']:.1f}

[node name="ProjectileSetup" parent="." index="0"]
base_damage = Array[ExtResource("2_dtype")]([SubResource("Resource_dmg")])
kickback = {abs(cfg['kickback']):.1f}

[node name="ProjectileMover" parent="." index="1"]
movement_type = {cfg['movement_type']}

[node name="Sprite2D" parent="RotatedNode" index="0"]
texture = ExtResource("3_tex")

[node name="HitLimit" parent="." index="6"]
target_hit_limit = {cfg['hit_limit']}

[node name="ProjectileLifetime" parent="." index="7"]
time = {cfg['proj_lifetime']:.2f}
"""


# ---------------------------------------------------------------------------
# Template: projectile InstanceResource
# ---------------------------------------------------------------------------

def make_instance_resource(cfg: dict) -> str:
    name = cfg["name"]
    display = to_display(name)
    return f"""\
[gd_resource type="Resource" script_class="InstanceResource" format=3]

[ext_resource type="Resource" path="res://game/resources/room/ysort_reference.tres" id="1_parent"]
[ext_resource type="Script" path="res://core/resources/InstanceResource/InstanceResource.gd" id="2_script"]

[resource]
resource_name = "{display} projectile"
script = ExtResource("2_script")
scene_path = "res://game/weapons/projectiles/{name}_projectile.tscn"
parent_reference_resource = ExtResource("1_parent")
"""


# ---------------------------------------------------------------------------
# Template: weapon scene (inherits gun.tscn)
# ---------------------------------------------------------------------------

def make_weapon_scene(cfg: dict) -> str:
    name = cfg["name"]
    pascal = to_pascal(name)
    inherits = cfg["inherits"]

    # Build the DamageDataResource sub_resource
    damage_type_enum = DAMAGE_TYPES[cfg["damage_type"]]

    # SpreadShot line only if spread > 0
    spread_section = ""
    if cfg["spread"] > 0.0:
        spread_section = f"""
[node name="SpreadShot" parent="ProjectileSpawner" index="0"]
random_angle_offset = {cfg['spread']:.1f}
"""

    return f"""\
[gd_scene load_steps=6 format=3]

[ext_resource type="PackedScene" path="{inherits}" id="1_base"]
[ext_resource type="Script" path="res://systems/damage/properties/DamageTypeResource.gd" id="2_dtype"]
[ext_resource type="Texture2D" path="res://assets/images/weapon/{name}.png" id="3_tex"]
[ext_resource type="Script" path="res://systems/damage/properties/DamageDataResource.gd" id="4_ddata"]
[ext_resource type="Script" path="res://systems/damage/properties/DamageStatusResource.gd" id="5_dstat"]
[ext_resource type="Resource" path="res://game/resources/weapons/{name}_projectile_instance_resource.tres" id="6_proj"]

[sub_resource type="Resource" id="Resource_ddata"]
script = ExtResource("4_ddata")
base_damage = Array[ExtResource("2_dtype")]([])
critical_chance = 0.3
critical_multiply = 1.5
status_list = Array[ExtResource("5_dstat")]([])
hit_list = []
report_callback = Callable()
transmission_name = &""
state = -1
valid = true
version = 0
not_saved = false

[node name="{pascal}" instance=ExtResource("1_base")]
damage_data_resource = SubResource("Resource_ddata")

[node name="Sprite2D" parent="RotatedNode" index="0"]
texture = ExtResource("3_tex")

[node name="WeaponKickback" parent="." index="2"]
kickback_strength = {cfg['kickback']:.1f}

[node name="ProjectileInterval" parent="WeaponTrigger" index="0"]
interval = {cfg['fire_rate']:.2f}

[node name="ProjectileSpawner" parent="." index="4"]
projectile_instance_resource = ExtResource("6_proj")
{spread_section}"""


# ---------------------------------------------------------------------------
# Weapon database registration
# ---------------------------------------------------------------------------

def update_weapon_database(cfg: dict) -> None:
    """Append a new WeaponItemResource entry to weapon_database.tres."""
    db_path = PROJECT_ROOT / "game" / "resources" / "weapons" / "weapon_database.tres"
    content = db_path.read_text(encoding="utf-8")

    name = cfg["name"]
    display = to_display(name)
    texture_path = f"res://assets/images/weapon/{name}.png"
    scene_path = f"res://game/weapons/{name}/{name}.tscn"

    # --- Find next ext_resource ID ---
    ext_ids = re.findall(r'\[ext_resource .+? id="(\d+)_', content)
    next_ext_num = max(int(x) for x in ext_ids) + 1 if ext_ids else 1
    tex_ext_id = f"{next_ext_num}_gen"

    # --- Find next sub_resource ID suffix ---
    # Use a simple incrementing suffix to avoid collisions
    sub_ids = re.findall(r'\[sub_resource .+? id="Resource_(\w+)"', content)
    new_sub_id = f"Resource_gen{name}"

    # --- Add ext_resource for the weapon texture ---
    # Insert before the first [sub_resource or [resource] line
    tex_ext_line = (
        f'[ext_resource type="Texture2D" path="{texture_path}" id="{tex_ext_id}"]\n'
    )
    # Find insertion point: after last ext_resource line
    last_ext_match = None
    for m in re.finditer(r'^\[ext_resource .+\]$', content, re.MULTILINE):
        last_ext_match = m
    if last_ext_match:
        insert_pos = last_ext_match.end()
        content = content[:insert_pos] + "\n" + tex_ext_line + content[insert_pos:]
    else:
        raise RuntimeError("Could not find ext_resource entries in weapon_database.tres")

    # --- Add sub_resource for the WeaponItemResource ---
    # WeaponItemResource script ext_resource ID - find it
    wir_match = re.search(
        r'\[ext_resource .+?WeaponItemResource\.gd.+?id="([^"]+)"', content
    )
    if not wir_match:
        raise RuntimeError("Could not find WeaponItemResource script in weapon_database.tres")
    wir_id = wir_match.group(1)

    new_sub_block = f"""
[sub_resource type="Resource" id="{new_sub_id}"]
resource_name = "{display}"
script = ExtResource("{wir_id}")
icon = ExtResource("{tex_ext_id}")
scene_path = "{scene_path}"
unlocked = true
"""

    # Insert before [resource] line
    resource_match = re.search(r'^\[resource\]$', content, re.MULTILINE)
    if not resource_match:
        raise RuntimeError("Could not find [resource] section in weapon_database.tres")
    content = content[:resource_match.start()] + new_sub_block + "\n" + content[resource_match.start():]

    # --- Update the list array to include the new sub_resource ---
    list_match = re.search(r'(list = Array\[.+?\]\()(\[.+?\])(\))', content)
    if not list_match:
        raise RuntimeError("Could not find list array in weapon_database.tres")

    existing_items = list_match.group(2)
    # Add our new sub_resource reference
    new_items = existing_items.rstrip("]") + f', SubResource("{new_sub_id}")]'
    content = content[:list_match.start(1)] + list_match.group(1) + new_items + ")" + content[list_match.end():]

    # --- Update load_steps ---
    # We added 1 ext_resource + 1 sub_resource = 2 more
    load_match = re.search(r'load_steps=(\d+)', content)
    if load_match:
        old_steps = int(load_match.group(1))
        content = content[:load_match.start()] + f"load_steps={old_steps + 2}" + content[load_match.end():]

    db_path.write_text(content, encoding="utf-8")


# ---------------------------------------------------------------------------
# File writing
# ---------------------------------------------------------------------------

def write_file(path: Path, content, binary: bool = False) -> None:
    """Write a file, creating parent directories as needed."""
    path.parent.mkdir(parents=True, exist_ok=True)
    if binary:
        path.write_bytes(content)
    else:
        path.write_text(content, encoding="utf-8")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def build_config(args: argparse.Namespace) -> dict:
    """Merge CLI args with archetype defaults into a single config dict."""
    archetype = ARCHETYPES[args.archetype]
    cfg = dict(archetype)  # copy defaults
    cfg["name"] = args.name
    cfg["archetype"] = args.archetype

    # CLI overrides
    if args.damage_type is not None:
        cfg["damage_type"] = args.damage_type
    if args.fire_rate is not None:
        cfg["fire_rate"] = args.fire_rate
    if args.damage is not None:
        cfg["damage"] = args.damage
    if args.kickback is not None:
        cfg["kickback"] = args.kickback
    if args.speed is not None:
        cfg["proj_speed"] = args.speed
    if args.lifetime is not None:
        cfg["proj_lifetime"] = args.lifetime
    if args.hit_limit is not None:
        cfg["hit_limit"] = args.hit_limit
    if args.spread is not None:
        cfg["spread"] = args.spread

    return cfg


def generate_weapon(cfg: dict, dry_run: bool = False) -> None:
    """Generate all files for a new weapon."""
    name = cfg["name"]

    files = {
        f"assets/images/weapon/{name}.png": (
            generate_png(16, 16, *cfg["weapon_color"]), True
        ),
        f"assets/images/projectile/{name}_projectile.png": (
            generate_png(8, 8, *cfg["proj_color"]), True
        ),
        f"game/weapons/projectiles/{name}_projectile.tscn": (
            make_projectile_scene(cfg), False
        ),
        f"game/resources/weapons/{name}_projectile_instance_resource.tres": (
            make_instance_resource(cfg), False
        ),
        f"game/weapons/{name}/{name}.tscn": (
            make_weapon_scene(cfg), False
        ),
    }

    if dry_run:
        print(f"[DRY RUN] Weapon: {to_display(name)} ({cfg['archetype']})")
        print(f"  Damage: {cfg['damage']} {cfg['damage_type']}")
        print(f"  Fire rate: {cfg['fire_rate']}s  |  Speed: {cfg['proj_speed']}")
        print(f"  Kickback: {cfg['kickback']}  |  Spread: {cfg['spread']}")
        print(f"  Lifetime: {cfg['proj_lifetime']}s  |  Hit limit: {cfg['hit_limit']}")
        print()
        print("Files that would be created:")
        for rel_path in files:
            abs_path = PROJECT_ROOT / rel_path
            exists = abs_path.exists()
            status = "EXISTS - would overwrite" if exists else "new"
            print(f"  {rel_path}  ({status})")
        print(f"  game/resources/weapons/weapon_database.tres  (would update)")
        return

    # Check for existing weapon
    weapon_dir = PROJECT_ROOT / "game" / "weapons" / name
    if weapon_dir.exists():
        print(f"Error: weapon directory already exists: game/weapons/{name}/", file=sys.stderr)
        print("Use a different name or remove the existing weapon first.", file=sys.stderr)
        sys.exit(1)

    # Write all files
    for rel_path, (content, binary) in files.items():
        abs_path = PROJECT_ROOT / rel_path
        write_file(abs_path, content, binary=binary)
        print(f"  Created: {rel_path}")

    # Register in weapon database
    update_weapon_database(cfg)
    print(f"  Updated: game/resources/weapons/weapon_database.tres")

    print()
    print(f"Weapon '{to_display(name)}' created successfully!")
    print(f"Next steps:")
    print(f"  1. Open Godot to import the new files")
    print(f"  2. Replace placeholder sprites in assets/images/weapon/{name}.png")
    print(f"     and assets/images/projectile/{name}_projectile.png")
    print(f"  3. Tweak values in the Weapon Editor plugin or directly in the scenes")


def main():
    parser = argparse.ArgumentParser(
        description="Generate a new weapon for the Godot project.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""\
Examples:
  %(prog)s fire_staff --archetype staff --damage-type fire
  %(prog)s crossbow --archetype gun --fire-rate 0.8
  %(prog)s battle_axe --archetype melee --kickback 80
  %(prog)s test_weapon --archetype gun --dry-run
        """,
    )

    parser.add_argument("name", help="Weapon name in snake_case (e.g. fire_staff)")
    parser.add_argument(
        "--archetype", choices=["gun", "staff", "melee"], default="gun",
        help="Weapon archetype (default: gun)",
    )
    parser.add_argument(
        "--damage-type", choices=list(DAMAGE_TYPES.keys()), default=None,
        help="Damage element type (default: per archetype)",
    )
    parser.add_argument("--fire-rate", type=float, default=None, help="Seconds between shots")
    parser.add_argument("--damage", type=float, default=None, help="Base damage value")
    parser.add_argument("--kickback", type=float, default=None, help="Knockback strength (negative = pull)")
    parser.add_argument("--speed", type=float, default=None, help="Projectile speed")
    parser.add_argument("--lifetime", type=float, default=None, help="Projectile lifetime in seconds")
    parser.add_argument("--hit-limit", type=int, default=None, help="Max targets per projectile")
    parser.add_argument("--spread", type=float, default=None, help="Random angle spread")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be generated without writing")

    args = parser.parse_args()

    # Validate name
    if not re.match(r'^[a-z][a-z0-9_]*$', args.name):
        parser.error("Name must be snake_case (lowercase letters, digits, underscores)")

    cfg = build_config(args)
    generate_weapon(cfg, dry_run=args.dry_run)


if __name__ == "__main__":
    main()
