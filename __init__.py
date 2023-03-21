
from . import module_loader
module_loader.unload_dhpm_modules(locals())

bl_info = {
    "name": "D-Packer",
    "author": "Dhruv Sharma",
    "version": (3, 0, 6),
    "blender": (3, 1, 0),
    "location": "",
    "description": "",
    "warning": "",
    "doc_url": "",
    "tracker_url": "",
    "category": "UV"}


inside_blender = True
 
try:
    import bpy
except:
    inside_blender = False


if inside_blender:

    from .operator_1 import *
    from .operator_misc import *
    from .panel import *
    from .prefs import *
    from .register_utils import *
    from .mode import *

    import bpy
    import mathutils

    from .scripted_pipeline import panels
    scripted_panels_modules = module_loader.import_submodules(panels)
    scripted_panels_classes = module_loader.get_registrable_classes(scripted_panels_modules, sub_class=DHPM_PT_Registerable)
    scripted_panels_classes.sort(key=lambda x: x.PANEL_PRIORITY)

    from .scripted_pipeline import operators
    scripted_operators_modules = module_loader.import_submodules(operators)
    scripted_operators_classes = module_loader.get_registrable_classes(scripted_operators_modules, sub_class=DHPM_OT_Generic)

    from .scripted_pipeline import modes
    scripted_modes_modules = module_loader.import_submodules(modes)
    scripted_modes_classes = module_loader.get_registrable_classes(scripted_modes_modules,
                                                                   sub_class=DHPM_Mode_Generic, required_vars=("MODE_ID",))
    scripted_modes_classes.sort(key=lambda x: x.MODE_PRIORITY)
    
    classes = (
        DHPM_Box,
        DHPM_DeviceSettings,
        DHPM_SavedDeviceSettings,
        DHPM_Preferences,

        DHPM_OT_SetEnginePath,

        DHPM_OT_SetPixelMarginTexSizeScene,
        DHPM_MT_SetPixelMarginTexSizeScene,
        DHPM_OT_SetPixelMarginTexSizeGroup,
        DHPM_MT_SetPixelMarginTexSizeGroup,

        DHPM_PT_Main,

        DHPM_ScriptedPipelineProperties,
        DHPM_SceneProps
    )

    def register():
        for cls in scripted_properties_classes:
            bpy.utils.register_class(cls)

        for cls in classes:
            bpy.utils.register_class(cls)

        for cls in scripted_panels_classes:
            bpy.utils.register_class(cls)

        for cls in scripted_operators_classes:
            bpy.utils.register_class(cls)

        bpy.types.Scene.dhpm_props = bpy.props.PointerProperty(type=DHPM_SceneProps)

        register_modes(scripted_modes_classes)
        register_specific(bl_info)

    def unregister():
        for cls in reversed(scripted_operators_classes):
            bpy.utils.unregister_class(cls)

        for cls in reversed(scripted_panels_classes):
            bpy.utils.unregister_class(cls)

        for cls in reversed(classes):
            bpy.utils.unregister_class(cls)

        for cls in reversed(scripted_properties_classes):
            bpy.utils.unregister_class(cls)

        del bpy.types.Scene.dhpm_props
