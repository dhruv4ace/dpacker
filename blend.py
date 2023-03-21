
inside_blender = True

try:
    import bpy
except:
    inside_blender = False


def get_prefs():
    return bpy.context.preferences.addons['dpacker'].preferences
