# https://chatgpt.com/c/527675ce-2bc9-4cb5-9f0e-ec693cbb2b0d

import bpy

# Text to display
text_to_display = "AGENTS OF INFERENCE"
# Frame rate (time each letter is displayed, lower value for quicker appearance)
frame_rate = 2
# Starting frame
start_frame = 1

font_path = "/Users/brian/Library/Fonts/Roboto-Regular.ttf"  # Change this to the actual path to your Roboto Regular font file

# Load the font
font = bpy.data.fonts.load(font_path)

# Create a new sequence editor if it doesn't exist
if not bpy.context.scene.sequence_editor:
    bpy.context.scene.sequence_editor_create()

# Ensure there is a SEQUENCE_EDITOR area
for area in bpy.context.screen.areas:
    if area.type == 'SEQUENCE_EDITOR':
        seq_area = area
        break
else:
    # Add a SEQUENCE_EDITOR area if not found
    bpy.ops.screen.area_split(direction='VERTICAL', factor=0.5)
    seq_area = bpy.context.screen.areas[-1]
    seq_area.type = 'SEQUENCE_EDITOR'

# Change context to VSE
override_context = bpy.context.copy()
override_context['area'] = seq_area
override_context['region'] = seq_area.regions[-1]
override_context['window'] = bpy.context.window
override_context['screen'] = bpy.context.screen

# Create a color strip for the black background
with bpy.context.temp_override(**override_context):
    bpy.ops.sequencer.effect_strip_add(
        type='COLOR',
        frame_start=start_frame,
        frame_end=start_frame + len(text_to_display) * frame_rate,
        channel=1
    )
    color_strip = bpy.context.scene.sequence_editor.sequences_all[-1]
    color_strip.color = (0, 0, 0)

# Function to create text strips
def create_text_strip(text, frame_start, frame_end, channel):
    with bpy.context.temp_override(**override_context):
        bpy.ops.sequencer.effect_strip_add(
            type='TEXT',
            frame_start=frame_start,
            frame_end=frame_end,
            channel=channel
        )
        text_strip = bpy.context.scene.sequence_editor.sequences_all[-1]
        text_strip.text = text
        text_strip.font = font
        text_strip.font_size = 120  # Adjust the font size as needed
        text_strip.align_x = 'LEFT'  # Set Anchor X to Left
        text_strip.align_y = 'CENTER'  # Center vertically
        text_strip.location.x = 0.1
        return text_strip

# Create text strips for each progressively larger substring
current_frame = start_frame + frame_rate
for i in range(1, len(text_to_display) + 1):
    create_text_strip(text_to_display[:i] + '⬤', current_frame, current_frame + frame_rate, 2)
    current_frame += frame_rate

# Set the scene end frame
bpy.context.scene.frame_end = current_frame
