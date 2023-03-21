from ...prefs_scripted_utils import ScriptParams
from ...mode import DHPM_Mode_Main, DHPM_ModeCategory_Packing, OperatorMetadata
from ..operators.pack_operator import DHPM_OT_Pack
from ...box import DEFAULT_TARGET_BOX
from ...utils import get_active_image_ratio
from ..panels.pack_panels import (
        DHPM_PT_PackOptions,
        DHPM_PT_PixelMargin,
    ) 

class DHPM_Mode_Pack(DHPM_Mode_Main):
    
    MODE_CATEGORY = DHPM_ModeCategory_Packing
    OPERATOR_IDNAME = DHPM_OT_Pack.bl_idname

    
    def subpanels(self):

        output = []
        output.append(DHPM_PT_PackOptions.bl_idname)
        output.append(DHPM_PT_PixelMargin.bl_idname)

        return output

    def pre_operation(self):
        
        self.target_boxes = self.get_target_boxes()

    def append_mode_name_to_op_label(self):
        return True

    def packing_operation(self):

        return True

    def get_group_method(self):

        return self.scene_props.group_method

    def use_main_target_box(self):

        return True

    def get_main_target_box(self):

        if not self.use_main_target_box():
            return None
        
        return DEFAULT_TARGET_BOX

    def get_target_boxes(self):

        main_box = self.get_main_target_box()

        if main_box is None:
            return None

        return [main_box]

    def validate_params(self):
 
        pass
    
    def setup_script_params(self):

        self.validate_params()

        script_params = ScriptParams()

        script_params.add_param('precision', self.scene_props.precision)
        script_params.add_param('margin', self.scene_props.margin)

        if self.prefs.pixel_margin_enabled(self.scene_props):
            script_params.add_param('pixel_margin', self.scene_props.pixel_margin)
            script_params.add_param('pixel_margin_tex_size', self.prefs.pixel_margin_tex_size(self.scene_props, self.context))

            if self.prefs.add_pixel_margin_to_others_enabled(self.scene_props):
                script_params.add_param('extra_pixel_margin_to_others', self.scene_props.extra_pixel_margin_to_others)

            if self.prefs.pixel_padding_enabled(self.scene_props):
                script_params.add_param('pixel_padding', self.scene_props.pixel_padding)

        if self.prefs.FEATURE_island_rotation:
            script_params.add_param('rotation_enable', self.scene_props.rotation_enable)
            script_params.add_param('pre_rotation_disable', self.scene_props.pre_rotation_disable)
            script_params.add_param('rotation_step', self.scene_props.rotation_step)

        if self.target_boxes is not None:

            script_params.add_param('target_boxes', [box.coords_tuple() for box in self.target_boxes])

        return script_params

class DHPM_Mode_SingleTile(DHPM_Mode_Pack):

    MODE_ID = 'pack.single_tile'
    MODE_NAME = 'Single Tile'
    MODE_PRIORITY = 1000

    SCENARIO_ID = 'pack.general'



