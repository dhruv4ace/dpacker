
from .prefs import get_prefs
from .operator_1 import *
from .utils import *

import bpy
import bpy_types


DHPM_PT_SPACE_TYPE = 'IMAGE_EDITOR'
DHPM_PT_REGION_TYPE = 'UI'
DHPM_PT_CATEGORY = 'D-Packer'
DHPM_PT_CONTEXT = ''


class DHPM_PT_Generic(bpy.types.Panel):

    bl_space_type = DHPM_PT_SPACE_TYPE
    bl_region_type = DHPM_PT_REGION_TYPE
    bl_category = DHPM_PT_CATEGORY
    bl_context = DHPM_PT_CONTEXT
    bl_order = 1

    @classmethod
    def draw_enum_in_box(self, obj, prop_id, prop_name, layout, help_url_suffix=None):

        box = layout.box()
        col = box.column(align=True)
        col.label(text=prop_name + ':')
        row = col.row(align=True)
        row.prop(obj, prop_id, text='')

        if help_url_suffix:
            self._draw_help_operator(row, help_url_suffix)

        return col

    @classmethod
    def draw_prop_with_set_menu(self, obj, prop_id, layout, menu_class):
        split = layout.split(factor=0.8, align=True)

        col_s = split.row(align=True)
        col_s.prop(obj, prop_id)
        col_s = split.row(align=True)
        col_s.menu(menu_class.bl_idname, text='Set')
        
    @classmethod
    def handle_prop(self, obj, prop_name, supported, not_supported_msg, layout):

        if supported:
            layout.prop(obj, prop_name)
        else:
            layout.enabled = False
            split = layout.split(factor=0.4)
            col_s = split.column()
            col_s.prop(obj, prop_name)
            col_s = split.column()
            col_s.label(text=not_supported_msg)


    def get_main_property(self):
        return None

    def draw_header(self, context):

        main_property = self.get_main_property()
        if main_property is None:
            return

        layout = self.layout
        scene_props = context.scene.dhpm_props

        col = layout.column()
        row = col.row()
        row.prop(scene_props, main_property, text='')
        row.row()

    def draw(self, context):

        self.prefs = get_prefs()
        self.scene_props = context.scene.dhpm_props
        self.scripted_props = context.scene.dhpm_props.scripted_props
        self.active_mode = self.prefs.get_active_main_mode(self.scene_props, context)

        main_property = self.get_main_property()

        if main_property is not None:
            self.layout.enabled = getattr(self.scene_props, main_property)
        
        self.draw_impl(context)

    def prop_with_help(self, obj, prop_id, layout):

        row = layout.row(align=True)
        row.prop(obj, prop_id)
        self._draw_help_operator(row, self.HELP_URL_SUFFIX)

    def operator_with_help(self, op_idname, layout):

        row = layout.row(align=True)
        row.operator(op_idname)
        self._draw_help_operator(row, self.HELP_URL_SUFFIX)

    def handle_prop_enum(self, obj, prop_name, prop_label, supported, not_supported_msg, layout):

        prop_label_colon = prop_label + ':'

        if supported:
            layout.label(text=prop_label_colon)
        else:
            split = layout.split(factor=0.4)
            col_s = split.column()
            col_s.label(text=prop_label_colon)
            col_s = split.column()
            col_s.label(text=not_supported_msg)

        layout.prop(obj, prop_name, text='')
        layout.enabled = supported

    def messages_in_boxes(self, ui_elem, messages):

        for msg in messages:
            box = ui_elem.box()

            msg_split = split_by_chars(msg, 60)
            if len(msg_split) > 0:
                for msg_part in msg_split:
                    box.label(text=msg_part)

class EngineStatusMeta(bpy_types.RNAMeta):
    @property
    def bl_label(self):
        prefs = get_prefs()
        return prefs.engine_status_msg



class DHPM_PT_Main(DHPM_PT_Generic):

    bl_idname = 'DHPM_PT_Main'
    bl_label = 'Main Mode'
    bl_context = ''

    def draw_impl(self, context):

        layout = self.layout
        col = layout.column(align=True)

        mode_id = self.scene_props.active_main_mode_id
        mode = self.prefs.get_mode(mode_id, context)

        mode_layout = col
        mode.draw(mode_layout)


class DHPM_PT_Registerable(DHPM_PT_Generic):

    bl_order = 10
    PANEL_PRIORITY = sys.maxsize


class DHPM_PT_SubPanel(DHPM_PT_Registerable):
    
    bl_parent_id = DHPM_PT_Main.bl_idname

    @classmethod
    def poll(cls, context):
        prefs = get_prefs()
        scene_props = context.scene.dhpm_props

        try:
            return cls.bl_idname in prefs.get_mode(scene_props.active_main_mode_id, context).subpanels_base()

        except:
            return False


class DHPM_PT_IParamEdit(DHPM_PT_SubPanel):

    def get_main_property(self):
        return self.IPARAM_EDIT_UI.ENABLED_PROP_NAME

    def draw_impl(self, context):

        self.IPARAM_EDIT_UI(context, self.scene_props).draw(self.layout)
