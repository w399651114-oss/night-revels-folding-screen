"""Native camera tracks. Both corridor variants share exactly the same walk."""

from bpy_extras.anim_utils import action_get_channelbag_for_slot
from mathutils import Vector

SCREEN_START, SCREEN_END = 217, 313
GAP_START, GAP_END = 337, 457
GAP_START_X = -6.55
FPS = 24
SPEED = 1.0


def add_walks(scene, camera):
    def track(name, stops, lens):
        first, loc, direction = stops[0]
        cam = camera(name, loc, Vector(loc) + Vector(direction), lens)
        marker = scene.timeline_markers.new(name, frame=first)
        marker.camera = cam
        for frame, loc, direction in stops:
            cam.location = loc
            cam.rotation_euler = Vector(direction).to_track_quat("-Z", "Y").to_euler()
            cam.keyframe_insert(data_path="location", frame=frame)
            cam.keyframe_insert(data_path="rotation_euler", frame=frame)
        anim = cam.animation_data
        channels = action_get_channelbag_for_slot(anim.action, anim.action_slot)
        for curve in channels.fcurves:
            for key in curve.keyframe_points:
                key.interpolation = "LINEAR"
        return cam

    track(
        "10 · 连续绕屏",
        [
            (SCREEN_START, (10.17, -1.47, 1.59), (-1.65, 1.72, -0.47)),
            (245, (9.34, -1.70, 1.59), (-2.10, 1.70, -0.48)),
            (281, (8.16, -1.70, 1.59), (-2.24, 1.83, -0.50)),
            (SCREEN_END, (7.14, -1.62, 1.59), (-2.32, 2.00, -0.55)),
        ],
        26,
    )
    direction = (-5.1, 1.70, -0.78)
    distance = (GAP_END - GAP_START) * SPEED / FPS
    track(
        "11 · 等速穿越留白",
        [
            (GAP_START, (GAP_START_X, -1.70, 1.59), direction),
            (GAP_END, (GAP_START_X - distance, -1.70, 1.59), direction),
        ],
        27,
    )
    scene.frame_end = GAP_END
