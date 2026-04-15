@tool
class_name WeaponEditorDock
extends VBoxContainer

const WEAPONS_DIR := "res://game/weapons/"

# --- UI references (set in _ready from node paths) ---
var weapon_list:ItemList
var weapon_preview:TextureRect
var projectile_preview:TextureRect
var weapon_sprite_label:Label
var projectile_sprite_label:Label
var btn_assign_weapon_sprite:Button
var btn_assign_projectile_sprite:Button
var spin_damage:SpinBox
var spin_fire_rate:SpinBox
var spin_kickback:SpinBox
var spin_speed:SpinBox
var spin_spread:SpinBox
var spin_lifetime:SpinBox
var spin_hit_limit:SpinBox
var btn_save:Button
var btn_refresh:Button
var btn_open:Button
var properties_container:VBoxContainer

# --- State ---
var weapon_entries:Array[Dictionary] = []
var selected_index:int = -1
var pending_weapon_texture:Texture2D
var pending_projectile_texture:Texture2D
var has_unsaved_changes:bool = false


func _ready() -> void:
	_build_ui()
	_connect_signals()
	_scan_weapons()


# ---------------------------------------------------------------------------
# UI Construction
# ---------------------------------------------------------------------------

func _build_ui() -> void:
	# Toolbar
	var toolbar := HBoxContainer.new()
	btn_refresh = Button.new()
	btn_refresh.text = "Refresh"
	btn_refresh.size_flags_horizontal = Control.SIZE_SHRINK_BEGIN
	toolbar.add_child(btn_refresh)

	btn_open = Button.new()
	btn_open.text = "Open in Editor"
	btn_open.size_flags_horizontal = Control.SIZE_SHRINK_BEGIN
	btn_open.disabled = true
	toolbar.add_child(btn_open)

	add_child(toolbar)

	# Weapon list
	weapon_list = ItemList.new()
	weapon_list.custom_minimum_size = Vector2(0, 120)
	weapon_list.size_flags_vertical = Control.SIZE_EXPAND_FILL
	weapon_list.max_columns = 1
	weapon_list.same_column_width = true
	add_child(weapon_list)

	add_child(HSeparator.new())

	# Scrollable properties panel
	var scroll := ScrollContainer.new()
	scroll.size_flags_vertical = Control.SIZE_EXPAND_FILL
	scroll.custom_minimum_size = Vector2(0, 200)

	properties_container = VBoxContainer.new()
	properties_container.size_flags_horizontal = Control.SIZE_EXPAND_FILL

	# Preview section
	properties_container.add_child(_make_label("Weapon Sprite"))
	weapon_preview = TextureRect.new()
	weapon_preview.custom_minimum_size = Vector2(64, 64)
	weapon_preview.stretch_mode = TextureRect.STRETCH_KEEP_ASPECT_CENTERED
	weapon_preview.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
	properties_container.add_child(weapon_preview)

	var weapon_sprite_row := HBoxContainer.new()
	weapon_sprite_label = Label.new()
	weapon_sprite_label.text = "No sprite"
	weapon_sprite_label.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	weapon_sprite_label.clip_text = true
	weapon_sprite_row.add_child(weapon_sprite_label)
	btn_assign_weapon_sprite = Button.new()
	btn_assign_weapon_sprite.text = "Assign..."
	btn_assign_weapon_sprite.disabled = true
	weapon_sprite_row.add_child(btn_assign_weapon_sprite)
	properties_container.add_child(weapon_sprite_row)

	properties_container.add_child(HSeparator.new())

	properties_container.add_child(_make_label("Projectile Sprite"))
	projectile_preview = TextureRect.new()
	projectile_preview.custom_minimum_size = Vector2(64, 64)
	projectile_preview.stretch_mode = TextureRect.STRETCH_KEEP_ASPECT_CENTERED
	projectile_preview.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
	properties_container.add_child(projectile_preview)

	var proj_sprite_row := HBoxContainer.new()
	projectile_sprite_label = Label.new()
	projectile_sprite_label.text = "No sprite"
	projectile_sprite_label.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	projectile_sprite_label.clip_text = true
	proj_sprite_row.add_child(projectile_sprite_label)
	btn_assign_projectile_sprite = Button.new()
	btn_assign_projectile_sprite.text = "Assign..."
	btn_assign_projectile_sprite.disabled = true
	proj_sprite_row.add_child(btn_assign_projectile_sprite)
	properties_container.add_child(proj_sprite_row)

	properties_container.add_child(HSeparator.new())

	# Property spinboxes
	properties_container.add_child(_make_label("Properties"))
	spin_damage = _make_spin("Damage", 0.0, 9999.0, 0.1)
	spin_fire_rate = _make_spin("Fire Rate (s)", 0.01, 10.0, 0.01)
	spin_kickback = _make_spin("Kickback", -500.0, 500.0, 1.0)
	spin_speed = _make_spin("Proj Speed", 0.0, 9999.0, 1.0)
	spin_spread = _make_spin("Spread", 0.0, 180.0, 0.5)
	spin_lifetime = _make_spin("Proj Lifetime (s)", 0.01, 30.0, 0.01)
	spin_hit_limit = _make_spin("Hit Limit", -1.0, 100.0, 1.0)

	properties_container.add_child(HSeparator.new())

	btn_save = Button.new()
	btn_save.text = "Save Changes"
	btn_save.disabled = true
	properties_container.add_child(btn_save)

	scroll.add_child(properties_container)
	add_child(scroll)

	# Start with properties hidden
	_set_properties_enabled(false)


func _make_label(text:String) -> Label:
	var label := Label.new()
	label.text = text
	label.add_theme_font_size_override("font_size", 13)
	return label


func _make_spin(label_text:String, min_val:float, max_val:float, step:float) -> SpinBox:
	var row := HBoxContainer.new()
	var label := Label.new()
	label.text = label_text
	label.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	row.add_child(label)

	var spin := SpinBox.new()
	spin.min_value = min_val
	spin.max_value = max_val
	spin.step = step
	spin.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	spin.editable = false
	row.add_child(spin)

	properties_container.add_child(row)
	return spin


func _set_properties_enabled(enabled:bool) -> void:
	spin_damage.editable = enabled
	spin_fire_rate.editable = enabled
	spin_kickback.editable = enabled
	spin_speed.editable = enabled
	spin_spread.editable = enabled
	spin_lifetime.editable = enabled
	spin_hit_limit.editable = enabled
	btn_save.disabled = !enabled
	btn_assign_weapon_sprite.disabled = !enabled
	btn_assign_projectile_sprite.disabled = !enabled
	btn_open.disabled = !enabled


# ---------------------------------------------------------------------------
# Signal connections
# ---------------------------------------------------------------------------

func _connect_signals() -> void:
	btn_refresh.pressed.connect(_scan_weapons)
	btn_open.pressed.connect(_on_open_pressed)
	weapon_list.item_selected.connect(_on_weapon_selected)
	btn_assign_weapon_sprite.pressed.connect(_on_assign_weapon_sprite)
	btn_assign_projectile_sprite.pressed.connect(_on_assign_projectile_sprite)
	btn_save.pressed.connect(_on_save_pressed)

	spin_damage.value_changed.connect(func(_v:float) -> void: has_unsaved_changes = true)
	spin_fire_rate.value_changed.connect(func(_v:float) -> void: has_unsaved_changes = true)
	spin_kickback.value_changed.connect(func(_v:float) -> void: has_unsaved_changes = true)
	spin_speed.value_changed.connect(func(_v:float) -> void: has_unsaved_changes = true)
	spin_spread.value_changed.connect(func(_v:float) -> void: has_unsaved_changes = true)
	spin_lifetime.value_changed.connect(func(_v:float) -> void: has_unsaved_changes = true)
	spin_hit_limit.value_changed.connect(func(_v:float) -> void: has_unsaved_changes = true)


# ---------------------------------------------------------------------------
# Weapon scanning
# ---------------------------------------------------------------------------

func _scan_weapons() -> void:
	weapon_entries.clear()
	weapon_list.clear()
	selected_index = -1
	_set_properties_enabled(false)

	var dir := DirAccess.open(WEAPONS_DIR)
	if dir == null:
		push_warning("WeaponEditor: Could not open " + WEAPONS_DIR)
		return

	dir.list_dir_begin()
	var dir_name := dir.get_next()
	while dir_name != "":
		if dir.current_is_dir() and dir_name != "projectiles":
			var weapon_path := WEAPONS_DIR + dir_name + "/" + dir_name + ".tscn"
			if ResourceLoader.exists(weapon_path):
				var entry := _load_weapon_entry(weapon_path, dir_name)
				if entry.size() > 0:
					weapon_entries.append(entry)
		dir_name = dir.get_next()
	dir.list_dir_end()

	# Sort alphabetically
	weapon_entries.sort_custom(func(a:Dictionary, b:Dictionary) -> bool:
		return a.get("name", "") < b.get("name", "")
	)

	for entry:Dictionary in weapon_entries:
		var icon:Texture2D = entry.get("weapon_texture")
		if icon != null:
			weapon_list.add_item(entry.get("display_name", ""), icon)
		else:
			weapon_list.add_item(entry.get("display_name", ""))


func _load_weapon_entry(scene_path:String, dir_name:String) -> Dictionary:
	var scene:PackedScene = load(scene_path) as PackedScene
	if scene == null:
		return {}

	var root:Node = scene.instantiate()
	if root == null:
		return {}

	var entry := {
		"name": dir_name,
		"display_name": root.name,
		"scene_path": scene_path,
		"weapon_texture": null,
		"weapon_texture_path": "",
		"projectile_texture": null,
		"projectile_texture_path": "",
		"projectile_scene_path": "",
		"damage": 0.0,
		"fire_rate": 0.5,
		"kickback": 0.0,
		"proj_speed": 120.0,
		"spread": 0.0,
		"lifetime": 2.0,
		"hit_limit": 1,
	}

	# Read weapon sprite
	var sprite:Sprite2D = root.get_node_or_null("RotatedNode/Sprite2D")
	if sprite != null and sprite.texture != null:
		entry["weapon_texture"] = sprite.texture
		entry["weapon_texture_path"] = sprite.texture.resource_path

	# Read kickback
	var kickback_node:Node = root.get_node_or_null("WeaponKickback")
	if kickback_node != null and "kickback_strength" in kickback_node:
		entry["kickback"] = kickback_node.kickback_strength

	# Read fire rate
	var interval_node:Node = root.get_node_or_null("WeaponTrigger/ProjectileInterval")
	if interval_node != null and "interval" in interval_node:
		entry["fire_rate"] = interval_node.interval

	# Read spread
	var spread_node:Node = root.get_node_or_null("ProjectileSpawner/SpreadShot")
	if spread_node != null and "random_angle_offset" in spread_node:
		entry["spread"] = spread_node.random_angle_offset

	# Read projectile info from spawner
	var spawner:Node = root.get_node_or_null("ProjectileSpawner")
	if spawner != null and "projectile_instance_resource" in spawner:
		var inst_res:Resource = spawner.projectile_instance_resource
		if inst_res != null and "scene_path" in inst_res:
			var proj_path:String = inst_res.scene_path
			entry["projectile_scene_path"] = proj_path
			_load_projectile_info(entry, proj_path)

	root.queue_free()
	return entry


func _load_projectile_info(entry:Dictionary, proj_scene_path:String) -> void:
	if !ResourceLoader.exists(proj_scene_path):
		return

	var proj_scene:PackedScene = load(proj_scene_path) as PackedScene
	if proj_scene == null:
		return

	var proj_root:Node = proj_scene.instantiate()
	if proj_root == null:
		return

	# Speed from root Projectile2D
	if "speed" in proj_root:
		entry["proj_speed"] = proj_root.speed

	# Projectile sprite
	var proj_sprite:Sprite2D = proj_root.get_node_or_null("RotatedNode/Sprite2D")
	if proj_sprite != null and proj_sprite.texture != null:
		entry["projectile_texture"] = proj_sprite.texture
		entry["projectile_texture_path"] = proj_sprite.texture.resource_path

	# Damage from ProjectileSetup
	var setup:Node = proj_root.get_node_or_null("ProjectileSetup")
	if setup != null and "base_damage" in setup:
		var dmg_array:Array = setup.base_damage
		if dmg_array.size() > 0 and "value" in dmg_array[0]:
			entry["damage"] = dmg_array[0].value

	# Hit limit
	var hit_node:Node = proj_root.get_node_or_null("HitLimit")
	if hit_node != null and "target_hit_limit" in hit_node:
		entry["hit_limit"] = hit_node.target_hit_limit

	# Lifetime
	var life_node:Node = proj_root.get_node_or_null("ProjectileLifetime")
	if life_node != null and "time" in life_node:
		entry["lifetime"] = life_node.time

	proj_root.queue_free()


# ---------------------------------------------------------------------------
# Selection & preview
# ---------------------------------------------------------------------------

func _on_weapon_selected(index:int) -> void:
	if index < 0 or index >= weapon_entries.size():
		return

	selected_index = index
	has_unsaved_changes = false
	pending_weapon_texture = null
	pending_projectile_texture = null
	var entry:Dictionary = weapon_entries[index]

	# Update previews
	weapon_preview.texture = entry.get("weapon_texture")
	projectile_preview.texture = entry.get("projectile_texture")

	weapon_sprite_label.text = _short_path(entry.get("weapon_texture_path", ""))
	projectile_sprite_label.text = _short_path(entry.get("projectile_texture_path", ""))

	# Update spinboxes (block signals to avoid marking as unsaved)
	_set_spin_silent(spin_damage, entry.get("damage", 0.0))
	_set_spin_silent(spin_fire_rate, entry.get("fire_rate", 0.5))
	_set_spin_silent(spin_kickback, entry.get("kickback", 0.0))
	_set_spin_silent(spin_speed, entry.get("proj_speed", 120.0))
	_set_spin_silent(spin_spread, entry.get("spread", 0.0))
	_set_spin_silent(spin_lifetime, entry.get("lifetime", 2.0))
	_set_spin_silent(spin_hit_limit, entry.get("hit_limit", 1))

	_set_properties_enabled(true)


func _set_spin_silent(spin:SpinBox, value:float) -> void:
	spin.set_value_no_signal(value)


func _short_path(path:String) -> String:
	if path.is_empty():
		return "No sprite"
	return path.get_file()


# ---------------------------------------------------------------------------
# Sprite assignment
# ---------------------------------------------------------------------------

func _on_assign_weapon_sprite() -> void:
	var dialog := EditorFileDialog.new()
	dialog.file_mode = EditorFileDialog.FILE_MODE_OPEN_FILE
	dialog.access = EditorFileDialog.ACCESS_RESOURCES
	dialog.filters = PackedStringArray(["*.png ; PNG Images"])
	dialog.current_dir = "res://assets/images/weapon/"
	dialog.file_selected.connect(func(path:String) -> void:
		var tex:Texture2D = load(path) as Texture2D
		if tex != null:
			pending_weapon_texture = tex
			weapon_preview.texture = tex
			weapon_sprite_label.text = path.get_file()
			has_unsaved_changes = true
		dialog.queue_free()
	)
	dialog.canceled.connect(dialog.queue_free)
	add_child(dialog)
	dialog.popup_centered(Vector2i(600, 400))


func _on_assign_projectile_sprite() -> void:
	var dialog := EditorFileDialog.new()
	dialog.file_mode = EditorFileDialog.FILE_MODE_OPEN_FILE
	dialog.access = EditorFileDialog.ACCESS_RESOURCES
	dialog.filters = PackedStringArray(["*.png ; PNG Images"])
	dialog.current_dir = "res://assets/images/projectile/"
	dialog.file_selected.connect(func(path:String) -> void:
		var tex:Texture2D = load(path) as Texture2D
		if tex != null:
			pending_projectile_texture = tex
			projectile_preview.texture = tex
			projectile_sprite_label.text = path.get_file()
			has_unsaved_changes = true
		dialog.queue_free()
	)
	dialog.canceled.connect(dialog.queue_free)
	add_child(dialog)
	dialog.popup_centered(Vector2i(600, 400))


# ---------------------------------------------------------------------------
# Save
# ---------------------------------------------------------------------------

func _on_save_pressed() -> void:
	if selected_index < 0 or selected_index >= weapon_entries.size():
		return

	var entry:Dictionary = weapon_entries[selected_index]

	# --- Save weapon scene ---
	var weapon_scene:PackedScene = load(entry["scene_path"]) as PackedScene
	if weapon_scene == null:
		push_error("WeaponEditor: Failed to load weapon scene")
		return

	var weapon_root:Node = weapon_scene.instantiate()

	# Apply weapon sprite
	if pending_weapon_texture != null:
		var sprite:Sprite2D = weapon_root.get_node_or_null("RotatedNode/Sprite2D")
		if sprite != null:
			_apply_sprite_texture_preserving_sheet(sprite, pending_weapon_texture)

	# Apply kickback
	var kickback_node:Node = weapon_root.get_node_or_null("WeaponKickback")
	if kickback_node != null:
		kickback_node.kickback_strength = spin_kickback.value

	# Apply fire rate
	var interval_node:Node = weapon_root.get_node_or_null("WeaponTrigger/ProjectileInterval")
	if interval_node != null:
		interval_node.interval = spin_fire_rate.value

	# Apply spread
	var spread_node:Node = weapon_root.get_node_or_null("ProjectileSpawner/SpreadShot")
	if spread_node != null:
		spread_node.random_angle_offset = spin_spread.value

	# Pack and save weapon
	var new_weapon_scene := PackedScene.new()
	new_weapon_scene.pack(weapon_root)
	var err := ResourceSaver.save(new_weapon_scene, entry["scene_path"])
	weapon_root.queue_free()

	if err != OK:
		push_error("WeaponEditor: Failed to save weapon scene: " + str(err))
		return

	# --- Save projectile scene ---
	var proj_path:String = entry.get("projectile_scene_path", "")
	if !proj_path.is_empty() and ResourceLoader.exists(proj_path):
		var proj_scene:PackedScene = load(proj_path) as PackedScene
		if proj_scene != null:
			var proj_root:Node = proj_scene.instantiate()

			# Apply projectile sprite
			if pending_projectile_texture != null:
				var proj_sprite:Sprite2D = proj_root.get_node_or_null("RotatedNode/Sprite2D")
				if proj_sprite != null:
					_apply_sprite_texture_preserving_sheet(proj_sprite, pending_projectile_texture)

			# Apply speed
			if "speed" in proj_root:
				proj_root.speed = spin_speed.value

			# Apply damage
			var setup:Node = proj_root.get_node_or_null("ProjectileSetup")
			if setup != null and "base_damage" in setup:
				var dmg_array:Array = setup.base_damage
				if dmg_array.size() > 0 and "value" in dmg_array[0]:
					dmg_array[0].value = spin_damage.value

			# Apply hit limit
			var hit_node:Node = proj_root.get_node_or_null("HitLimit")
			if hit_node != null:
				hit_node.target_hit_limit = int(spin_hit_limit.value)

			# Apply lifetime
			var life_node:Node = proj_root.get_node_or_null("ProjectileLifetime")
			if life_node != null:
				life_node.time = spin_lifetime.value

			# Pack and save projectile
			var new_proj_scene := PackedScene.new()
			new_proj_scene.pack(proj_root)
			ResourceSaver.save(new_proj_scene, proj_path)
			proj_root.queue_free()

	has_unsaved_changes = false
	pending_weapon_texture = null
	pending_projectile_texture = null

	# Refresh the entry
	_scan_weapons()

	# Re-select the same weapon
	for i:int in weapon_entries.size():
		if weapon_entries[i].get("name", "") == entry.get("name", ""):
			weapon_list.select(i)
			_on_weapon_selected(i)
			break

	print("WeaponEditor: Saved ", entry.get("display_name", ""))


# ---------------------------------------------------------------------------
# Open in editor
# ---------------------------------------------------------------------------

func _on_open_pressed() -> void:
	if selected_index < 0 or selected_index >= weapon_entries.size():
		return
	var entry:Dictionary = weapon_entries[selected_index]
	EditorInterface.open_scene_from_path(entry["scene_path"])


func _apply_sprite_texture_preserving_sheet(sprite:Sprite2D, texture:Texture2D) -> void:
	var old_hframes:int = max(sprite.hframes, 1)
	var old_vframes:int = max(sprite.vframes, 1)
	sprite.texture = texture

	# Keep explicit sheet slicing that was already configured.
	sprite.hframes = old_hframes
	sprite.vframes = old_vframes

	# If no slicing is set but frame animation exists, infer horizontal frames.
	if old_hframes == 1 and old_vframes == 1:
		var inferred_hframes:int = _infer_hframes_from_sprite_animation(sprite)
		if inferred_hframes > 1:
			sprite.hframes = inferred_hframes
			sprite.vframes = 1

	# Validate that the texture can actually support the frame count.
	# A single-frame texture assigned to a multi-frame sprite would produce
	# cropped/blank frames — reset slicing when the texture is too small.
	if texture != null and (sprite.hframes > 1 or sprite.vframes > 1):
		var tex_width:int = texture.get_width()
		var tex_height:int = texture.get_height()
		var frame_width:int = tex_width / sprite.hframes
		var frame_height:int = tex_height / sprite.vframes
		if frame_width < 1 or frame_height < 1:
			sprite.hframes = 1
			sprite.vframes = 1
			push_warning("WeaponEditor: Texture too small for %dx%d sheet slicing, reset to 1x1" % [old_hframes, old_vframes])


func _infer_hframes_from_sprite_animation(sprite:Sprite2D) -> int:
	var max_frame:int = -1
	for child:Node in sprite.get_children():
		var anim_player:AnimationPlayer = child as AnimationPlayer
		if anim_player == null:
			continue
		for library_name:StringName in anim_player.get_animation_library_list():
			var library:AnimationLibrary = anim_player.get_animation_library(library_name)
			if library == null:
				continue
			for animation_name:StringName in library.get_animation_list():
				var animation:Animation = library.get_animation(animation_name)
				if animation == null:
					continue
				for track_idx:int in animation.get_track_count():
					if animation.track_get_type(track_idx) != Animation.TYPE_VALUE:
						continue
					if animation.track_get_path(track_idx) != NodePath(".:frame"):
						continue
					for key_idx:int in animation.track_get_key_count(track_idx):
						var key_value:Variant = animation.track_get_key_value(track_idx, key_idx)
						if typeof(key_value) == TYPE_INT or typeof(key_value) == TYPE_FLOAT:
							max_frame = maxi(max_frame, int(round(float(key_value))))
	return max_frame + 1
