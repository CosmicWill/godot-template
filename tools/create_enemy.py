#!/usr/bin/env python3
"""Generate boilerplate files for a new enemy in the Godot project.

Usage:
    python tools/create_enemy.py fire_bat --archetype melee
    python tools/create_enemy.py archer_skeleton --archetype ranged --hp 40 --speed 20
    python tools/create_enemy.py ice_golem --archetype boss --hp 800 --generate-attack
    python tools/create_enemy.py test_enemy --dry-run
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
    "melee": dict(
        hp=50.0,
        acceleration=200.0,
        max_speed=40.0,
        attack_distance=10.0,
        damage=10.0,
        damage_type="physical",
        collision_width=8,
        collision_height=4,
        sprite_offset_y=-8,
        shadow_scale=1.0,
        sprite_color=(220, 80, 80, 255),
        dead_sprite_color=(180, 60, 60, 255),
    ),
    "ranged": dict(
        hp=30.0,
        acceleration=150.0,
        max_speed=25.0,
        attack_distance=80.0,
        damage=8.0,
        damage_type="physical",
        collision_width=8,
        collision_height=4,
        sprite_offset_y=-8,
        shadow_scale=1.0,
        sprite_color=(80, 120, 220, 255),
        dead_sprite_color=(60, 90, 180, 255),
    ),
    "boss": dict(
        hp=500.0,
        acceleration=100.0,
        max_speed=30.0,
        attack_distance=15.0,
        damage=25.0,
        damage_type="physical",
        collision_width=24,
        collision_height=12,
        sprite_offset_y=-16,
        shadow_scale=2.0,
        sprite_color=(180, 80, 220, 255),
        dead_sprite_color=(140, 60, 180, 255),
    ),
}


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
    row = b"\x00" + bytes([r, g, b, a]) * width
    raw = row * height
    idat = zlib.compress(raw)
    return header + _png_chunk(b"IHDR", ihdr) + _png_chunk(b"IDAT", idat) + _png_chunk(b"IEND", b"")


def generate_spritesheet_png(
    frame_width: int, frame_height: int, frame_count: int,
    r: int, g: int, b: int, a: int = 255,
) -> bytes:
    """Generate a horizontal spritesheet PNG with alternating shade per frame."""
    width = frame_width * frame_count
    height = frame_height
    header = b"\x89PNG\r\n\x1a\n"
    ihdr = struct.pack(">IIBBBBB", width, height, 8, 6, 0, 0, 0)

    raw = b""
    for _y in range(height):
        row = b"\x00"  # filter byte
        for frame in range(frame_count):
            # Alternate brightness per frame for visual distinction
            shade = 1.0 if frame % 2 == 0 else 0.75
            fr = min(255, int(r * shade))
            fg = min(255, int(g * shade))
            fb = min(255, int(b * shade))
            row += bytes([fr, fg, fb, a]) * frame_width
        raw += row

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
# Template: enemy scene (inherits actor.tscn)
# ---------------------------------------------------------------------------

def make_enemy_scene(cfg: dict) -> str:
    name = cfg["name"]
    pascal = to_pascal(name)
    hp = cfg["hp"]
    accel = cfg["acceleration"]
    speed = cfg["max_speed"]
    cw = cfg["collision_width"]
    ch = cfg["collision_height"]
    sprite_y = cfg["sprite_offset_y"]
    shadow_scale = cfg["shadow_scale"]
    attack_distance = cfg["attack_distance"]

    # Determine attack weapon path
    if cfg["generate_attack"]:
        attack_path = f"res://game/weapons/{name}_attack/{name}_attack.tscn"
    else:
        attack_path = "res://game/weapons/zombie_attack/zombie_attack.tscn"

    # Resistance section
    resistance_section = ""
    resistance_ext = ""
    resistance_sub = ""
    resistance_node = ""
    extra_load_steps = 0

    if cfg.get("resistance_type") is not None:
        extra_load_steps = 2
        resistance_ext = f"""[ext_resource type="Script" path="res://systems/damage/properties/DamageTypeResource.gd" id="ext_resist_dtype"]
"""
        resistance_sub = f"""
[sub_resource type="Resource" id="Resource_resist"]
script = ExtResource("ext_resist_dtype")
value = {cfg['resistance_value']:.1f}
type = {DAMAGE_TYPES[cfg['resistance_type']]}
"""
        resistance_node = f"""
[node name="DamageSetup" parent="." index="13"]
resistance_list = Array[ExtResource("ext_resist_dtype")]([SubResource("Resource_resist")])
"""

    load_steps = 39 + extra_load_steps

    return f"""\
[gd_scene load_steps={load_steps} format=3]

[ext_resource type="PackedScene" path="res://systems/actor/actor.tscn" id="1_base"]
[ext_resource type="Script" path="res://core/nodes/ResourceNode/ResourceNodeItem.gd" id="2_rnitem"]
[ext_resource type="Shader" path="res://assets/shaders/color_flash.gdshader" id="3_cflash"]
[ext_resource type="Texture2D" path="res://assets/images/characters/{name}_16x16_strip8.png" id="4_tex"]
[ext_resource type="Script" path="res://systems/actor/ActorStatsResource.gd" id="5_stats"]
[ext_resource type="Script" path="res://systems/damage/HealthResource.gd" id="6_health"]
[ext_resource type="Script" path="res://systems/actor/PushResource.gd" id="7_push"]
[ext_resource type="Script" path="res://core/resources/ValueResource/BoolResource.gd" id="8_bool"]
[ext_resource type="Script" path="res://systems/input/InputResource.gd" id="9_input"]
[ext_resource type="Script" path="res://systems/damage/DamageResource.gd" id="10_dmg"]
[ext_resource type="Resource" path="res://game/resources/sounds/kill_zombie.tres" id="11_killsnd"]
[ext_resource type="Resource" path="res://game/resources/vfx/dead/{name}_dead_instance_resource.tres" id="12_deadfx"]
[ext_resource type="PackedScene" path="res://game/actors/ai/enemy_ai.tscn" id="13_ai"]
[ext_resource type="PackedScene" path="{attack_path}" id="14_attack"]
[ext_resource type="Script" path="res://core/resources/InstanceResource/PoolNode.gd" id="15_pool"]
[ext_resource type="Script" path="res://game/actors/ai/ActiveEnemy.gd" id="16_active"]
{resistance_ext}
[sub_resource type="Resource" id="Resource_stats"]
resource_name = "movement  properties"
script = ExtResource("5_stats")
acceleration = {accel:.1f}
max_speed = {speed:.1f}
version = 0
not_saved = false

[sub_resource type="Resource" id="Resource_movement"]
resource_name = "movement"
script = ExtResource("2_rnitem")
resource = SubResource("Resource_stats")
make_unique = true
description = ""

[sub_resource type="Resource" id="Resource_hp"]
resource_name = "Health resource"
script = ExtResource("6_health")
hp = {hp:.1f}
max_hp = {hp:.1f}
reset_hp = {hp:.1f}
reset_max_hp = {hp:.1f}
is_dead = false
version = 0
not_saved = false

[sub_resource type="Resource" id="Resource_health"]
resource_name = "health"
script = ExtResource("2_rnitem")
resource = SubResource("Resource_hp")
make_unique = true
description = ""

[sub_resource type="Resource" id="Resource_pushres"]
resource_name = "Push Resource"
script = ExtResource("7_push")
version = 0
not_saved = false

[sub_resource type="Resource" id="Resource_push"]
resource_name = "push"
script = ExtResource("2_rnitem")
resource = SubResource("Resource_pushres")
make_unique = true
description = ""

[sub_resource type="Resource" id="Resource_dashbool"]
resource_name = "Dash bool"
script = ExtResource("8_bool")
value = false
default_value = false
version = 0
not_saved = false

[sub_resource type="Resource" id="Resource_dash"]
resource_name = "dash"
script = ExtResource("2_rnitem")
resource = SubResource("Resource_dashbool")
make_unique = true
description = ""

[sub_resource type="Resource" id="Resource_holebool"]
resource_name = "Hole bool"
script = ExtResource("8_bool")
value = false
default_value = false
version = 0
not_saved = false

[sub_resource type="Resource" id="Resource_hole"]
resource_name = "hole"
script = ExtResource("2_rnitem")
resource = SubResource("Resource_holebool")
make_unique = true
description = ""

[sub_resource type="Resource" id="Resource_inputres"]
resource_name = "Input resource"
script = ExtResource("9_input")
axis = Vector2(0, 0)
action_1 = false
action_2 = false
aim_direction = Vector2(0, 0)
version = 0
not_saved = false

[sub_resource type="Resource" id="Resource_input"]
resource_name = "input"
script = ExtResource("2_rnitem")
resource = SubResource("Resource_inputres")
make_unique = true
description = "Used to control actors movement by it's input node.
"

[sub_resource type="Resource" id="Resource_dmgres"]
resource_name = "Damage Resource"
script = ExtResource("10_dmg")
can_receive_damage = true
version = 0
not_saved = false

[sub_resource type="Resource" id="Resource_damage"]
resource_name = "damage"
script = ExtResource("2_rnitem")
resource = SubResource("Resource_dmgres")
make_unique = true
description = "Receives report from delt and received damage."

[sub_resource type="RectangleShape2D" id="RectangleShape2D_body"]
size = Vector2({cw}, {ch})

[sub_resource type="RectangleShape2D" id="RectangleShape2D_area"]
size = Vector2({cw}, {ch})

[sub_resource type="ShaderMaterial" id="ShaderMaterial_cflash"]
resource_local_to_scene = true
shader = ExtResource("3_cflash")
shader_parameter/overlay = Color(1, 1, 1, 1)
shader_parameter/blend = 0.0

[sub_resource type="Animation" id="Animation_reset"]
length = 0.001
tracks/0/type = "value"
tracks/0/imported = false
tracks/0/enabled = true
tracks/0/path = NodePath(".:frame")
tracks/0/interp = 1
tracks/0/loop_wrap = true
tracks/0/keys = {{
"times": PackedFloat32Array(0),
"transitions": PackedFloat32Array(1),
"update": 1,
"values": [0]
}}
tracks/1/type = "value"
tracks/1/imported = false
tracks/1/enabled = true
tracks/1/path = NodePath("..:position")
tracks/1/interp = 1
tracks/1/loop_wrap = true
tracks/1/keys = {{
"times": PackedFloat32Array(0),
"transitions": PackedFloat32Array(1),
"update": 0,
"values": [Vector2(0, 0)]
}}
tracks/2/type = "value"
tracks/2/imported = false
tracks/2/enabled = true
tracks/2/path = NodePath("..:rotation")
tracks/2/interp = 1
tracks/2/loop_wrap = true
tracks/2/keys = {{
"times": PackedFloat32Array(0),
"transitions": PackedFloat32Array(1),
"update": 0,
"values": [0.0]
}}

[sub_resource type="Animation" id="Animation_idle"]
resource_name = "idle"
length = 0.4
loop_mode = 1
tracks/0/type = "value"
tracks/0/imported = false
tracks/0/enabled = true
tracks/0/path = NodePath(".:frame")
tracks/0/interp = 1
tracks/0/loop_wrap = true
tracks/0/keys = {{
"times": PackedFloat32Array(0, 0.2),
"transitions": PackedFloat32Array(1, 1),
"update": 1,
"values": [0, 1]
}}

[sub_resource type="Animation" id="Animation_walk"]
resource_name = "walk"
length = 0.6
loop_mode = 1
tracks/0/type = "value"
tracks/0/imported = false
tracks/0/enabled = true
tracks/0/path = NodePath(".:frame")
tracks/0/interp = 1
tracks/0/loop_wrap = true
tracks/0/keys = {{
"times": PackedFloat32Array(0, 0.1, 0.2, 0.3, 0.4, 0.5),
"transitions": PackedFloat32Array(1, 1, 1, 1, 1, 1),
"update": 1,
"values": [2, 3, 4, 5, 6, 7]
}}

[sub_resource type="AnimationLibrary" id="AnimationLibrary_char"]
_data = {{
"RESET": SubResource("Animation_reset"),
"idle": SubResource("Animation_idle"),
"walk": SubResource("Animation_walk")
}}
{resistance_sub}
[node name="{pascal}" instance=ExtResource("1_base")]
collision_layer = 4
collision_mask = 5

[node name="ResourceNode" parent="." index="0"]
list = Array[ExtResource("2_rnitem")]([SubResource("Resource_movement"), SubResource("Resource_health"), SubResource("Resource_push"), SubResource("Resource_dash"), SubResource("Resource_hole"), SubResource("Resource_input"), SubResource("Resource_damage")])

[node name="CollisionShape2D" parent="." index="1"]
shape = SubResource("RectangleShape2D_body")

[node name="AreaReceiver2D" parent="." index="2"]
collision_layer = 4

[node name="CollisionShape2D" parent="AreaReceiver2D" index="0"]
shape = SubResource("RectangleShape2D_area")

[node name="Shadow" parent="." index="3"]
scale = Vector2({shadow_scale}, {shadow_scale})

[node name="Sprite2D" parent="Body/Stretch" index="0"]
material = SubResource("ShaderMaterial_cflash")
position = Vector2(0, {sprite_y})
texture = ExtResource("4_tex")

[node name="CharacterAnimator" parent="Body/Stretch/Sprite2D" index="0"]
libraries = {{
"": SubResource("AnimationLibrary_char")
}}

[node name="ActorDamage" parent="." index="11"]
sound_resource_dead = ExtResource("11_killsnd")
dead_vfx_instance_resource = ExtResource("12_deadfx")
{resistance_node}
[node name="EnemyAi" parent="." index="15" node_paths=PackedStringArray("resource_node") instance=ExtResource("13_ai")]
resource_node = NodePath("../ResourceNode")
attack_distance = {attack_distance:.1f}

[node name="Attack" parent="." index="16" node_paths=PackedStringArray("resource_node") instance=ExtResource("14_attack")]
collision_mask = 2
resource_node = NodePath("../ResourceNode")

[node name="PoolNode" type="Node" parent="." index="17" node_paths=PackedStringArray("animation_player_list", "listen_node")]
script = ExtResource("15_pool")
animation_player_list = [NodePath("../Body/Stretch/Sprite2D/CharacterAnimator"), NodePath("../Body/Stretch/Sprite2D/ColorFlash")]
listen_node = NodePath("../ActorDamage")
signal_name = &"actor_died"

[node name="ActiveEnemy" type="Node" parent="." index="18" node_paths=PackedStringArray("resource_node")]
script = ExtResource("16_active")
resource_node = NodePath("../ResourceNode")
"""


# ---------------------------------------------------------------------------
# Template: enemy InstanceResource
# ---------------------------------------------------------------------------

def make_instance_resource(cfg: dict) -> str:
    name = cfg["name"]
    display = to_display(name)
    return f"""\
[gd_resource type="Resource" script_class="InstanceResource" format=3]

[ext_resource type="Resource" path="res://game/resources/room/ysort_reference.tres" id="1_parent"]
[ext_resource type="Script" path="res://core/resources/InstanceResource/InstanceResource.gd" id="2_script"]

[resource]
resource_name = "{display} instance resource"
script = ExtResource("2_script")
scene_path = "res://game/actors/enemies/{name}/{name}.tscn"
parent_reference_resource = ExtResource("1_parent")
"""


# ---------------------------------------------------------------------------
# Template: death VFX scene
# ---------------------------------------------------------------------------

def make_dead_scene(cfg: dict) -> str:
    name = cfg["name"]
    pascal = to_pascal(name)
    sprite_y = cfg["sprite_offset_y"]

    return f"""\
[gd_scene format=3]

[ext_resource type="Texture2D" path="res://assets/images/shadow.png" id="1_shadow"]
[ext_resource type="Script" path="res://core/resources/InstanceResource/PoolNode.gd" id="2_pool"]
[ext_resource type="Texture2D" path="res://assets/images/characters/{name}_16x16_strip8.png" id="3_tex"]

[sub_resource type="Animation" id="Animation_reset"]
length = 0.001
tracks/0/type = "value"
tracks/0/imported = false
tracks/0/enabled = true
tracks/0/path = NodePath(".:frame")
tracks/0/interp = 1
tracks/0/loop_wrap = true
tracks/0/keys = {{
"times": PackedFloat32Array(0),
"transitions": PackedFloat32Array(1),
"update": 1,
"values": [0]
}}
tracks/1/type = "value"
tracks/1/imported = false
tracks/1/enabled = true
tracks/1/path = NodePath("..:position")
tracks/1/interp = 1
tracks/1/loop_wrap = true
tracks/1/keys = {{
"times": PackedFloat32Array(0),
"transitions": PackedFloat32Array(1),
"update": 0,
"values": [Vector2(0, 0)]
}}
tracks/2/type = "value"
tracks/2/imported = false
tracks/2/enabled = true
tracks/2/path = NodePath("..:rotation")
tracks/2/interp = 1
tracks/2/loop_wrap = true
tracks/2/keys = {{
"times": PackedFloat32Array(0),
"transitions": PackedFloat32Array(1),
"update": 0,
"values": [0.0]
}}

[sub_resource type="Animation" id="Animation_died"]
resource_name = "died"
length = 7.0
tracks/0/type = "value"
tracks/0/imported = false
tracks/0/enabled = true
tracks/0/path = NodePath("..:position")
tracks/0/interp = 1
tracks/0/loop_wrap = true
tracks/0/keys = {{
"times": PackedFloat32Array(0, 0.266667, 0.5),
"transitions": PackedFloat32Array(2, 0.5, 1),
"update": 0,
"values": [Vector2(0, 0), Vector2(0, -8), Vector2(7, -3)]
}}
tracks/1/type = "value"
tracks/1/imported = false
tracks/1/enabled = true
tracks/1/path = NodePath("..:rotation")
tracks/1/interp = 1
tracks/1/loop_wrap = true
tracks/1/keys = {{
"times": PackedFloat32Array(0, 0.266667, 0.5),
"transitions": PackedFloat32Array(1, 0.5, 1),
"update": 0,
"values": [0.0, 0.0, -1.5708]
}}
tracks/2/type = "animation"
tracks/2/imported = false
tracks/2/enabled = true
tracks/2/path = NodePath("ColorFlash")
tracks/2/interp = 1
tracks/2/loop_wrap = true
tracks/2/keys = {{
"clips": PackedStringArray("flash"),
"times": PackedFloat32Array(0)
}}
tracks/3/type = "value"
tracks/3/imported = false
tracks/3/enabled = true
tracks/3/path = NodePath("../..:scale")
tracks/3/interp = 1
tracks/3/loop_wrap = true
tracks/3/keys = {{
"times": PackedFloat32Array(5, 6),
"transitions": PackedFloat32Array(2, 1),
"update": 0,
"values": [Vector2(1, 1), Vector2(0, 0)]
}}
tracks/4/type = "method"
tracks/4/imported = false
tracks/4/enabled = true
tracks/4/path = NodePath("../../../PoolNode")
tracks/4/interp = 1
tracks/4/loop_wrap = true
tracks/4/keys = {{
"times": PackedFloat32Array(6),
"transitions": PackedFloat32Array(1),
"values": [{{
"args": [],
"method": &"pool_return"
}}]
}}

[sub_resource type="AnimationLibrary" id="AnimationLibrary_char"]
_data = {{
&"RESET": SubResource("Animation_reset"),
&"died": SubResource("Animation_died")
}}

[sub_resource type="Animation" id="Animation_flash_reset"]
length = 0.001
tracks/0/type = "value"
tracks/0/imported = false
tracks/0/enabled = true
tracks/0/path = NodePath("..:scale")
tracks/0/interp = 1
tracks/0/loop_wrap = true
tracks/0/keys = {{
"times": PackedFloat32Array(0),
"transitions": PackedFloat32Array(1),
"update": 0,
"values": [Vector2(1, 1)]
}}

[sub_resource type="Animation" id="Animation_flash"]
resource_name = "flash"
length = 0.5
tracks/0/type = "value"
tracks/0/imported = false
tracks/0/enabled = true
tracks/0/path = NodePath("..:scale")
tracks/0/interp = 1
tracks/0/loop_wrap = true
tracks/0/keys = {{
"times": PackedFloat32Array(0, 0.5),
"transitions": PackedFloat32Array(0.5, 1),
"update": 0,
"values": [Vector2(0.75, 1.2), Vector2(1, 1)]
}}

[sub_resource type="AnimationLibrary" id="AnimationLibrary_flash"]
_data = {{
&"RESET": SubResource("Animation_flash_reset"),
&"flash": SubResource("Animation_flash")
}}

[node name="{pascal}Dead" type="Node2D"]

[node name="Shadow" type="Sprite2D" parent="."]
modulate = Color(0.0196078, 0.0352941, 0.0784314, 0.454902)
texture = ExtResource("1_shadow")

[node name="Body" type="Node2D" parent="."]
scale = Vector2(1e-05, 1e-05)

[node name="Stretch" type="Node2D" parent="Body"]

[node name="Sprite2D" type="Sprite2D" parent="Body/Stretch"]
position = Vector2(0, {sprite_y})
texture = ExtResource("3_tex")
hframes = 8

[node name="CharacterAnimator" type="AnimationPlayer" parent="Body/Stretch/Sprite2D"]
libraries/ = SubResource("AnimationLibrary_char")
autoplay = &"died"

[node name="ColorFlash" type="AnimationPlayer" parent="Body/Stretch/Sprite2D"]
libraries/ = SubResource("AnimationLibrary_flash")

[node name="PoolNode" type="Node" parent="." node_paths=PackedStringArray("ready_nodes", "animation_player_list")]
script = ExtResource("2_pool")
ready_nodes = [NodePath("../Body/Stretch/Sprite2D/CharacterAnimator")]
animation_player_list = [NodePath("../Body/Stretch/Sprite2D/CharacterAnimator"), NodePath("../Body/Stretch/Sprite2D/ColorFlash")]
"""


# ---------------------------------------------------------------------------
# Template: death VFX InstanceResource
# ---------------------------------------------------------------------------

def make_dead_instance_resource(cfg: dict) -> str:
    name = cfg["name"]
    display = to_display(name)
    return f"""\
[gd_resource type="Resource" script_class="InstanceResource" format=3]

[ext_resource type="Resource" path="res://game/resources/room/ysort_reference.tres" id="1_parent"]
[ext_resource type="Script" path="res://core/resources/InstanceResource/InstanceResource.gd" id="2_script"]

[resource]
resource_name = "{name} dead"
script = ExtResource("2_script")
scene_path = "res://game/vfx/dead/{name}_dead.tscn"
parent_reference_resource = ExtResource("1_parent")
"""


# ---------------------------------------------------------------------------
# Template: attack weapon scene (optional, inherits weapon.tscn)
# ---------------------------------------------------------------------------

def make_attack_scene(cfg: dict) -> str:
    name = cfg["name"]
    pascal = to_pascal(name)
    damage_type_enum = DAMAGE_TYPES[cfg["damage_type"]]

    return f"""\
[gd_scene load_steps=8 format=3]

[ext_resource type="PackedScene" path="res://systems/weapons/weapon.tscn" id="1_base"]
[ext_resource type="Script" path="res://systems/damage/properties/DamageTypeResource.gd" id="2_dtype"]
[ext_resource type="Script" path="res://systems/damage/properties/DamageDataResource.gd" id="3_ddata"]
[ext_resource type="Script" path="res://systems/damage/properties/DamageStatusResource.gd" id="4_dstat"]
[ext_resource type="Resource" path="res://game/resources/weapons/{name}_slash_instance_resource.tres" id="5_proj"]

[sub_resource type="Resource" id="Resource_ddata"]
script = ExtResource("3_ddata")
base_damage = Array[ExtResource("2_dtype")]([])
critical_chance = 0.3
critical_multiply = 1.5
status_list = Array[ExtResource("4_dstat")]([])
hit_list = []
report_callback = Callable()
transmission_name = &""
state = -1
valid = true
version = 0
not_saved = false

[node name="{pascal}Attack" instance=ExtResource("1_base")]
damage_data_resource = SubResource("Resource_ddata")

[node name="RotatedNode" parent="." index="0"]
visible = false

[node name="ProjectileSpawner" parent="." index="4"]
projectile_instance_resource = ExtResource("5_proj")

[node name="SpreadShot" parent="ProjectileSpawner" index="0"]
random_angle_offset = 0.0
"""


# ---------------------------------------------------------------------------
# Template: attack projectile InstanceResource (optional)
# ---------------------------------------------------------------------------

def make_attack_projectile_instance(cfg: dict) -> str:
    name = cfg["name"]
    display = to_display(name)
    return f"""\
[gd_resource type="Resource" script_class="InstanceResource" format=3]

[ext_resource type="Resource" path="res://game/resources/room/ysort_reference.tres" id="1_parent"]
[ext_resource type="Script" path="res://core/resources/InstanceResource/InstanceResource.gd" id="2_script"]

[resource]
resource_name = "{display} slash"
script = ExtResource("2_script")
scene_path = "res://systems/weapons/projectile/projectile.tscn"
parent_reference_resource = ExtResource("1_parent")
"""


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
    cfg["generate_attack"] = args.generate_attack

    # CLI overrides
    if args.hp is not None:
        cfg["hp"] = args.hp
    if args.speed is not None:
        cfg["max_speed"] = args.speed
    if args.acceleration is not None:
        cfg["acceleration"] = args.acceleration
    if args.attack_distance is not None:
        cfg["attack_distance"] = args.attack_distance
    if args.damage is not None:
        cfg["damage"] = args.damage
    if args.damage_type is not None:
        cfg["damage_type"] = args.damage_type
    if args.collision_width is not None:
        cfg["collision_width"] = args.collision_width
    if args.collision_height is not None:
        cfg["collision_height"] = args.collision_height

    # Resistance parsing
    cfg["resistance_type"] = None
    cfg["resistance_value"] = 0.0
    if args.resistance is not None:
        parts = args.resistance.split(":")
        if len(parts) != 2:
            print("Error: --resistance must be in format type:value (e.g. fire:5)", file=sys.stderr)
            sys.exit(1)
        rtype = parts[0].lower()
        if rtype not in DAMAGE_TYPES:
            print(f"Error: unknown resistance type '{rtype}'. Valid: {', '.join(DAMAGE_TYPES.keys())}", file=sys.stderr)
            sys.exit(1)
        cfg["resistance_type"] = rtype
        cfg["resistance_value"] = float(parts[1])

    return cfg


def generate_enemy(cfg: dict, dry_run: bool = False) -> None:
    """Generate all files for a new enemy."""
    name = cfg["name"]

    files = {
        f"assets/images/characters/{name}_16x16_strip8.png": (
            generate_spritesheet_png(16, 16, 8, *cfg["sprite_color"]), True
        ),
        f"game/vfx/dead/{name}_dead.tscn": (
            make_dead_scene(cfg), False
        ),
        f"game/resources/vfx/dead/{name}_dead_instance_resource.tres": (
            make_dead_instance_resource(cfg), False
        ),
        f"game/resources/actors/{name}_instance_resource.tres": (
            make_instance_resource(cfg), False
        ),
        f"game/actors/enemies/{name}/{name}.tscn": (
            make_enemy_scene(cfg), False
        ),
    }

    # Optional attack weapon files
    if cfg["generate_attack"]:
        files[f"game/weapons/{name}_attack/{name}_attack.tscn"] = (
            make_attack_scene(cfg), False
        )
        files[f"game/resources/weapons/{name}_slash_instance_resource.tres"] = (
            make_attack_projectile_instance(cfg), False
        )

    if dry_run:
        print(f"[DRY RUN] Enemy: {to_display(name)} ({cfg['archetype']})")
        print(f"  HP: {cfg['hp']}  |  Speed: {cfg['max_speed']}  |  Accel: {cfg['acceleration']}")
        print(f"  Attack distance: {cfg['attack_distance']}  |  Damage: {cfg['damage']} {cfg['damage_type']}")
        print(f"  Collision: {cfg['collision_width']}x{cfg['collision_height']}")
        if cfg["resistance_type"]:
            print(f"  Resistance: {cfg['resistance_type']}:{cfg['resistance_value']}")
        print(f"  Generate attack: {cfg['generate_attack']}")
        print()
        print("Files that would be created:")
        for rel_path in files:
            abs_path = PROJECT_ROOT / rel_path
            exists = abs_path.exists()
            status = "EXISTS - would overwrite" if exists else "new"
            print(f"  {rel_path}  ({status})")
        return

    # Check for existing enemy
    enemy_dir = PROJECT_ROOT / "game" / "actors" / "enemies" / name
    if enemy_dir.exists():
        print(f"Error: enemy directory already exists: game/actors/enemies/{name}/", file=sys.stderr)
        print("Use a different name or remove the existing enemy first.", file=sys.stderr)
        sys.exit(1)

    # Write all files
    for rel_path, (content, binary) in files.items():
        abs_path = PROJECT_ROOT / rel_path
        write_file(abs_path, content, binary=binary)
        print(f"  Created: {rel_path}")

    print()
    print(f"Enemy '{to_display(name)}' created successfully!")
    print(f"Next steps:")
    print(f"  1. Open Godot to import the new files")
    print(f"  2. Replace placeholder sprite: assets/images/characters/{name}_16x16_strip8.png")
    print(f"  3. Add {name}_instance_resource.tres to a SpawnWaveList in your arena config")
    print(f"  4. Tweak stats directly in the enemy scene or via the editor")


def main():
    parser = argparse.ArgumentParser(
        description="Generate a new enemy for the Godot project.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""\
Examples:
  %(prog)s fire_bat --archetype melee
  %(prog)s archer_skeleton --archetype ranged --hp 40 --speed 20
  %(prog)s ice_golem --archetype boss --hp 800 --generate-attack --damage-type ice
  %(prog)s test_enemy --dry-run
        """,
    )

    parser.add_argument("name", help="Enemy name in snake_case (e.g. fire_bat)")
    parser.add_argument(
        "--archetype", choices=["melee", "ranged", "boss"], default="melee",
        help="Enemy archetype (default: melee)",
    )
    parser.add_argument("--hp", type=float, default=None, help="Hit points")
    parser.add_argument("--speed", type=float, default=None, help="Max movement speed")
    parser.add_argument("--acceleration", type=float, default=None, help="Movement acceleration")
    parser.add_argument("--attack-distance", type=float, default=None, help="Distance to trigger attack")
    parser.add_argument("--damage", type=float, default=None, help="Attack damage value")
    parser.add_argument(
        "--damage-type", choices=list(DAMAGE_TYPES.keys()), default=None,
        help="Damage element type (default: per archetype)",
    )
    parser.add_argument(
        "--generate-attack", action="store_true",
        help="Generate a dedicated attack weapon instead of reusing zombie_attack",
    )
    parser.add_argument("--collision-width", type=int, default=None, help="Collision shape width")
    parser.add_argument("--collision-height", type=int, default=None, help="Collision shape height")
    parser.add_argument(
        "--resistance", default=None,
        help="Damage resistance as type:value (e.g. fire:5)",
    )
    parser.add_argument("--dry-run", action="store_true", help="Show what would be generated without writing")

    args = parser.parse_args()

    # Validate name
    if not re.match(r'^[a-z][a-z0-9_]*$', args.name):
        parser.error("Name must be snake_case (lowercase letters, digits, underscores)")

    cfg = build_config(args)
    generate_enemy(cfg, dry_run=args.dry_run)


if __name__ == "__main__":
    main()
