## Simple animation state machine just for characters
class_name CharacterStates
extends Node

@export var enabled:bool = true
@export var resource_node:ResourceNode
@export var animation_player:AnimationPlayer
enum State {NONE, IDLE, WALK}
@export var state:State = State.NONE

const animation_list:Array[StringName] = ["idle", "idle", "walk"]
var input_resource:InputResource

## Not using automatic setter functions because they are called before _ready during initialization
func _ready()->void:
	input_resource = resource_node.get_resource("input")
	assert(input_resource != null)
	_prepare_sprite_sheet_animation()
	set_enabled(enabled)
	var init_state: = state
	state = State.NONE # force to be a different value than called
	_set_state(init_state)

	# in case used with PoolNode
	request_ready()

## Toggle processing for animation state machine
func set_enabled(value:bool)->void:
	enabled = value
	set_process(enabled)
	#print("CharacterAnimator [INFO]: set_enabled = ", enabled)

## Sets state variable and plays an animation
## Receiving the same state gets ignored
func _set_state(value:State)->void:
	if state == value:
		return
	state = value
	var animation:StringName = animation_list[state]
	animation_player.play(animation)
	#print("CharacterAnimator [INFO]: set_state = ", animation, " - ", owner.name)

## Decide which state should be active every game's frame
func _process(_delta:float)->void:
	if input_resource.axis.length_squared() > 0.001:
		_set_state(State.WALK)
	else:
		_set_state(State.IDLE)


## Ensure frame tracks don't interpolate and sprite sheet slicing matches animation keys.
func _prepare_sprite_sheet_animation() -> void:
	var sprite:Sprite2D = animation_player.get_parent() as Sprite2D
	if sprite == null:
		return

	var max_frame_index:int = -1
	for library_name:StringName in animation_player.get_animation_library_list():
		var library:AnimationLibrary = animation_player.get_animation_library(library_name)
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
				# Frame indices must be stepped. Continuous updates cause sheet scrolling.
				animation.value_track_set_update_mode(track_idx, Animation.UPDATE_DISCRETE)
				for key_idx:int in animation.track_get_key_count(track_idx):
					var key_value:Variant = animation.track_get_key_value(track_idx, key_idx)
					if typeof(key_value) == TYPE_INT or typeof(key_value) == TYPE_FLOAT:
						max_frame_index = maxi(max_frame_index, int(round(float(key_value))))

	if max_frame_index < 0:
		return

	var required_hframes:int = max_frame_index + 1
	if sprite.hframes != required_hframes:
		sprite.hframes = required_hframes
	if sprite.vframes < 1:
		sprite.vframes = 1
