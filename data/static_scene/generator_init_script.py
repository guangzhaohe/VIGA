"""Blender script for static scene initialization with Camera1 rendering."""
import bpy
import os
import sys


def _resolve_target_image_path(target_image_path):
    if not target_image_path:
        return None
    if os.path.isfile(target_image_path):
        return target_image_path
    if not os.path.isdir(target_image_path):
        return None

    preferred_names = (
        "target.png",
        "target.jpg",
        "target.jpeg",
        "visprompt1.png",
        "style1.png",
        "render1.png",
    )
    for name in preferred_names:
        candidate = os.path.join(target_image_path, name)
        if os.path.isfile(candidate):
            return candidate

    for name in sorted(os.listdir(target_image_path)):
        if name.lower().endswith((".png", ".jpg", ".jpeg")):
            return os.path.join(target_image_path, name)
    return None


def _set_render_resolution_from_target(target_image_path, long_side=512):
    target_image_path = _resolve_target_image_path(target_image_path)
    width = height = None
    if target_image_path:
        try:
            image = bpy.data.images.load(target_image_path, check_existing=True)
            width, height = image.size
        except Exception as exc:
            print(f"[WARN] Failed to read target image size from {target_image_path}: {exc}")

    if not width or not height:
        width = height = long_side

    if width >= height:
        resolution_x = long_side
        resolution_y = max(1, round(long_side * height / width))
    else:
        resolution_x = max(1, round(long_side * width / height))
        resolution_y = long_side

    bpy.context.scene.render.resolution_x = int(resolution_x)
    bpy.context.scene.render.resolution_y = int(resolution_y)
    print(f"[INFO] Render resolution set to {resolution_x}x{resolution_y}")


if __name__ == "__main__":

    code_fpath = sys.argv[6]  # Path to the code file
    if len(sys.argv) > 7:
        rendering_dir = sys.argv[7] # Path to save the rendering from camera1
    else:
        rendering_dir = None
    if len(sys.argv) > 8:
        save_blend = sys.argv[8] # Path to save the blend file
    else:
        save_blend = None
    if len(sys.argv) > 9:
        target_image_path = sys.argv[9] # Path to target image for aspect ratio
    else:
        target_image_path = None
    
    # Enable GPU rendering
    bpy.context.scene.render.engine = 'CYCLES'
    bpy.context.preferences.addons['cycles'].preferences.compute_device_type = 'CUDA'  # or 'OPTIX' if your GPU supports it
    bpy.context.preferences.addons['cycles'].preferences.get_devices()

    # Check and select the GPUs
    for device in bpy.context.preferences.addons['cycles'].preferences.devices:
        if device.type == 'GPU' and not device.use:
            device.use = True

    # Set the rendering device to GPU
    bpy.context.scene.cycles.device = 'GPU'

    # Match target image aspect ratio with the longer side normalized to 512 px.
    _set_render_resolution_from_target(target_image_path)

    # Set max samples to 1024
    bpy.context.scene.cycles.samples = 512

    # Set color mode to RGB
    bpy.context.scene.render.image_settings.color_mode = 'RGB'

    # Read and execute the code from the specified file
    with open(code_fpath, "r") as f:
        code = f.read()
    try:
        exec(code)
    except:
        raise ValueError

    # Render from camera1
    if 'Camera1' in bpy.data.objects and rendering_dir:
        bpy.context.scene.camera = bpy.data.objects['Camera1']
        bpy.context.scene.render.image_settings.file_format = 'PNG'
        bpy.context.scene.render.filepath = os.path.join(rendering_dir, 'render1.png')
        bpy.ops.render.render(write_still=True)

    # Save the blend file
    if save_blend:
        # Set the save version to 0
        bpy.context.preferences.filepaths.save_version = 0
        # Save the blend file
        bpy.ops.wm.save_as_mainfile(filepath=save_blend)

