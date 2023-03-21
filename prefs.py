import os
import multiprocessing
from pathlib import Path
from .enums import *
from .utils import get_active_image_size, force_read_int
from .prefs_scripted_utils import scripted_pipeline_property_group
from .labels import PropConstants
from .mode import ModeType
from .box import DHPM_Box
from .register_utils import DHPM_OT_SetEnginePath
from . import module_loader
import bpy
from bpy.props import IntProperty, FloatProperty, BoolProperty, StringProperty, EnumProperty, CollectionProperty, PointerProperty
from bpy.types import AddonPreferences
from mathutils import Vector
from .scripted_pipeline import properties
scripted_properties_modules = module_loader.import_submodules(properties)
scripted_properties_classes = module_loader.get_registrable_classes(scripted_properties_modules,
                                                                    sub_class=bpy.types.PropertyGroup,
                                                                    required_vars=("SCRIPTED_PROP_GROUP_ID",))

class DHPM_DeviceSettings(bpy.types.PropertyGroup):

    enabled : BoolProperty(name='enabled', default=True)

class DHPM_SavedDeviceSettings(bpy.types.PropertyGroup):

    dev_id : StringProperty(name="", default="")
    settings : PointerProperty(type=DHPM_DeviceSettings)

def _update_active_main_mode_id(self, context):
    from .panel import DHPM_PT_Main
    from . import scripted_panels_classes

    bpy.utils.unregister_class(DHPM_PT_Main)
    bpy.utils.register_class(DHPM_PT_Main)

    for panel_cls in scripted_panels_classes:
        try:
            bpy.utils.unregister_class(panel_cls)
            bpy.utils.register_class(panel_cls)
        except:
            pass


def _update_engine_status_msg(self, context):
    from .panel import DHPM_PT_EngineStatus
    try:
        bpy.utils.unregister_class(DHPM_PT_EngineStatus)
    except:
        pass
    bpy.utils.register_class(DHPM_PT_EngineStatus)

class DHPM_SceneProps(bpy.types.PropertyGroup):
    
    active_grouping_scheme_idx : IntProperty(default=-1, min=-1)

    precision : IntProperty(
        name='Precision',
        default=500,
        min=10,
        max=10000)

    margin : FloatProperty(
        name='Margin',
        min=0.0,
        max=0.2,
        default=0.003,
        precision=3,
        step=0.1)

    pixel_margin_enable : BoolProperty(
        name='',
        default=False)

    pixel_margin : IntProperty(
        name='Pixel Margin',
        min=PropConstants.PIXEL_MARGIN_MIN,
        max=PropConstants.PIXEL_MARGIN_MAX,
        default=PropConstants.PIXEL_MARGIN_DEFAULT)

    pixel_padding : IntProperty(
        name='Pixel Padding',
        min=PropConstants.PIXEL_PADDING_MIN,
        max=PropConstants.PIXEL_PADDING_MAX,
        default=PropConstants.PIXEL_PADDING_DEFAULT)

    extra_pixel_margin_to_others : IntProperty(
        name='Pixel Margin to Others',
        min=PropConstants.EXTRA_PIXEL_MARGIN_TO_OTHERS_MIN,
        max=PropConstants.EXTRA_PIXEL_MARGIN_TO_OTHERS_MAX,
        default=PropConstants.EXTRA_PIXEL_MARGIN_TO_OTHERS_DEFAULT)

    pixel_margin_tex_size : IntProperty(
        name='Size',
        min=PropConstants.PIXEL_MARGIN_TEX_SIZE_MIN,
        max=PropConstants.PIXEL_MARGIN_TEX_SIZE_MAX,
        default=PropConstants.PIXEL_MARGIN_TEX_SIZE_DEFAULT)

    rotation_enable : BoolProperty(
        name='',
        default=PropConstants.ROTATION_ENABLE_DEFAULT)

    pre_rotation_disable : BoolProperty(
        name='',
        default=PropConstants.PRE_ROTATION_DISABLE_DEFAULT)

    fixed_scale_strategy : EnumProperty(
        items=DhpmFixedScaleStrategy.to_blend_items(),
        name='')
    
    rotation_step : IntProperty(
        name='',
        default=PropConstants.ROTATION_STEP_DEFAULT,
        min=PropConstants.ROTATION_STEP_MIN,
        max=PropConstants.ROTATION_STEP_MAX)

    tex_ratio : BoolProperty(
        name='',
        default=False)


    def get_main_mode_blend_enums(scene, context):
        prefs = get_prefs()
        modes_info = prefs.get_modes(ModeType.MAIN)

        return [(mode_id, mode_cls.enum_name(), "") for mode_id, mode_cls in modes_info]

    active_main_mode_id : EnumProperty(
        items=get_main_mode_blend_enums,
        update=_update_active_main_mode_id,
        name='',)
        
    group_method : EnumProperty(
        items=GroupingMethod.to_blend_items(),
        name='')
    
    def auto_grouping_enabled(self):

        return GroupingMethod.auto_grouping_enabled(self.group_method)

    def active_grouping_scheme(self, context):

        if self.auto_grouping_enabled():
            return None

class DHPM_Preferences(AddonPreferences):
    bl_idname = __package__

    MAX_TILES_IN_ROW = 1000

    modes_dict = None

    def pixel_margin_enabled(self, scene_props):
        return scene_props.pixel_margin_enable

    def add_pixel_margin_to_others_enabled(self, scene_props):
        return scene_props.extra_pixel_margin_to_others > 0

    def pixel_padding_enabled(self, scene_props):
        return scene_props.pixel_padding > 0
           
    def heuristic_supported(self, scene_props):

        return True, ''

    def heuristic_enabled(self, scene_props):
        return self.heuristic_supported(scene_props)[0] and scene_props.heuristic_enable

    def heuristic_timeout_enabled(self, scene_props):
        return self.heuristic_enabled(scene_props) and scene_props.heuristic_search_time > 0

    def advanced_heuristic_available(self, scene_props):
        return self.FEATURE_advanced_heuristic and self.heuristic_enabled(scene_props)

    def pack_to_others_supported(self, scene_props):

        return True, ''

    def pack_ratio_supported(self):
        return self.FEATURE_pack_ratio and self.FEATURE_target_box

    def pack_ratio_enabled(self, scene_props):
        return self.pack_ratio_supported() and scene_props.tex_ratio

    def pixel_margin_tex_size(self, scene_props, context):
        if self.pack_ratio_enabled(scene_props):
            img_size = get_active_image_size(context)
            tex_size = img_size[1]
        else:
            tex_size = scene_props.pixel_margin_tex_size

        return tex_size

    def fixed_scale_supported(self, scene_props):

        return True, ''

    def fixed_scale_enabled(self, scene_props):
        return self.fixed_scale_supported(scene_props)[0] and scene_props.fixed_scale

    def normalize_islands_supported(self, scene_props):
        if self.fixed_scale_enabled(scene_props):
            return False, "(Not supported with 'Fixed Scale' enabled)"

        return True, ''

    def normalize_islands_enabled(self, scene_props):
        return self.normalize_islands_supported(scene_props)[0] and scene_props.normalize_islands

    def reset_box_params(self):
        self.box_rendering = False
        self.group_scheme_boxes_editing = False
        self.custom_target_box_editing = False
        self.boxes_dirty = False

    def reset_feature_codes(self):
        self.FEATURE_demo = False
        self.FEATURE_island_rotation = True
        self.FEATURE_overlap_check = True
        self.FEATURE_packing_depth = True
        self.FEATURE_heuristic_search = True
        self.FEATURE_pack_ratio = True
        self.FEATURE_pack_to_others = True
        self.FEATURE_grouping = True
        self.FEATURE_lock_overlapping = True
        self.FEATURE_advanced_heuristic = True
        self.FEATURE_self_intersect_processing = True
        self.FEATURE_validation = True
        self.FEATURE_multi_device_pack = True
        self.FEATURE_target_box = True
        self.FEATURE_island_rotation_step = True
        self.FEATURE_pack_to_tiles = True

    def reset_stats(self):

        for dev in self.device_array():
            dev.reset()

    def reset(self):
        self.engine_path = ''
        self.enabled = True
        self.engine_initialized = False
        self.engine_status_msg = ''
        self.thread_count = multiprocessing.cpu_count()
        self.operation_counter = -1
        self.write_to_file = False
        self.seed = 0
        
        self.reset_stats()
        self.reset_device_array()
        self.reset_box_params()
        self.reset_feature_codes()


    def get_mode(self, mode_id, context):
        if self.modes_dict is None:
            raise RuntimeError("Mods are not initialized.")
        try:
            return next(m(context) for m_list in self.modes_dict.values() for (m_id, m) in m_list if m_id == mode_id)
        except StopIteration:
            raise KeyError("The '{}' mode not found".format(mode_id))

    def get_modes(self, mode_type):
        return self.modes_dict[mode_type]

    def get_active_main_mode(self, scene_props, context):
        return self.get_mode(scene_props.active_main_mode_id, context)

    # Supporeted features
    FEATURE_demo : BoolProperty(
        name='',
        description='',
        default=False)

    FEATURE_island_rotation : BoolProperty(
        name='',
        description='',
        default=False)

    FEATURE_overlap_check : BoolProperty(
        name='',
        description='',
        default=False)

    FEATURE_packing_depth : BoolProperty(
        name='',
        description='',
        default=False)

    FEATURE_heuristic_search : BoolProperty(
        name='',
        description='',
        default=False)

    FEATURE_advanced_heuristic : BoolProperty(
        name='',
        description='',
        default=False)

    FEATURE_pack_ratio : BoolProperty(
        name='',
        description='',
        default=False)

    FEATURE_pack_to_others : BoolProperty(
        name='',
        description='',
        default=False)

    FEATURE_grouping : BoolProperty(
        name='',
        description='',
        default=False)

    FEATURE_lock_overlapping : BoolProperty(
        name='',
        description='',
        default=False)

    FEATURE_self_intersect_processing : BoolProperty(
        name='',
        description='',
        default=False)

    FEATURE_validation : BoolProperty(
        name='',
        description='',
        default=False)

    FEATURE_multi_device_pack : BoolProperty(
        name='',
        description='',
        default=False)

    FEATURE_target_box : BoolProperty(
        name='',
        description='',
        default=False)

    FEATURE_island_rotation_step : BoolProperty(
        name='',
        description='',
        default=False)

    FEATURE_pack_to_tiles : BoolProperty(
        name='',
        description='',
        default=False)

    operation_counter : IntProperty(
        name='',
        description='',
        default=-1)

    box_rendering : BoolProperty(
        name='',
        description='',
        default=False)

    boxes_dirty : BoolProperty(
        name='',
        description='',
        default=False)

    group_scheme_boxes_editing : BoolProperty(
        name='',
        description='',
        default=False)

    custom_target_box_editing : BoolProperty(
        name='',
        description='',
        default=False)

    engine_retcode : IntProperty(
        name='',
        description='',
        default=0)

    engine_path : StringProperty(
        name='',
        description='',
        default='')

    engine_initialized : BoolProperty(
        name='',
        description='',
        default=False)

    engine_status_msg : StringProperty(
        name='',
        description='',
        default='',
        update=_update_engine_status_msg)

    thread_count : IntProperty(
        name='',
        description='',
        default=multiprocessing.cpu_count(),
        min=1,
        max=multiprocessing.cpu_count())

    seed : IntProperty(
        name='',
        default=0,
        min=0,
        max=10000)

    test_param : IntProperty(
        name = '',
        default=0,
        min=0,
        max=10000)

    write_to_file : BoolProperty(
        name = '',
        description='',
        default=False)

    wait_for_debugger : BoolProperty(
        name = '',
        description='',
        default=False)

    append_mode_name_to_op_label : BoolProperty(
        name = '',
        default=False)

    box_render_line_width : FloatProperty(
        name = '',
        default=4.0,
        min=1.0,
        max=10.0,
        step=5.0)


    dev_array = []
    saved_dev_settings : CollectionProperty(type=DHPM_SavedDeviceSettings)

    def device_array(self):
        return type(self).dev_array

    def reset_device_array(self):
        type(self).dev_array = []


    def get_main_preset_path(self):
        preset_path = os.path.join(self.get_userdata_path(), 'presets')
        Path(preset_path).mkdir(parents=True, exist_ok=True)
        return preset_path

    def get_grouping_schemes_preset_path(self):
        preset_path = os.path.join(self.get_userdata_path(), 'grouping_schemes')
        Path(preset_path).mkdir(parents=True, exist_ok=True)
        return preset_path



@scripted_pipeline_property_group("scripted_props",
                                  DHPM_SceneProps, scripted_properties_classes,
                                  (DHPM_SceneProps, DHPM_Preferences))
class DHPM_ScriptedPipelineProperties(bpy.types.PropertyGroup):
    pass
