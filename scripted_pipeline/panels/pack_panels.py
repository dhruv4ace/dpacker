from ...panel import *
from ...operator_misc import  DHPM_MT_SetPixelMarginTexSizeScene
import multiprocessing

class DHPM_PT_PackOptions(DHPM_PT_SubPanel):

    bl_idname = 'DHPM_PT_PackOptions'
    bl_label = 'Packing Options'

    PANEL_PRIORITY = 1000

    def draw_impl(self, context):
        layout = self.layout
        col = layout.column(align=True)

        col.prop(self.scene_props, "precision")
        col.prop(self.scene_props, "margin")

        box = col.box()
        box.enabled = self.prefs.FEATURE_island_rotation

class DHPM_PT_PixelMargin(DHPM_PT_SubPanel):

    bl_idname = 'DHPM_PT_PixelMargin'
    bl_label = 'Pixel Margin'
    bl_options = {'DEFAULT_CLOSED'}

    PANEL_PRIORITY = 3000

    def get_main_property(self):
        return 'pixel_margin_enable'

    def draw_impl(self, context):
        layout = self.layout
        col = layout.column(align=True)

        col.prop(self.scene_props, "pixel_margin")

        row = col.row(align=True)
        row.prop(self.scene_props, "pixel_padding")

        row = col.row(align=True)
        row.prop(self.scene_props, "extra_pixel_margin_to_others")

        row = col.row(align=True)
        self.draw_prop_with_set_menu(self.scene_props, "pixel_margin_tex_size", row, DHPM_MT_SetPixelMarginTexSizeScene)

