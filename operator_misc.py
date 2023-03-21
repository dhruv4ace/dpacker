import bpy
from bpy.props import IntProperty

class SetPropPropertiesMixin:

    value : IntProperty(
        name='Value',
        description='',
        default=0)


class DHPM_OT_SetPropBase(bpy.types.Operator):

    def execute(self, context):
        target = self.get_target_obj(context)

        if target is None:
            return {'CANCELLED'}

        setattr(target, self.PROP_ID, self.value)
        return {'FINISHED'}


class DHPM_MT_SetPropBase(bpy.types.Menu):

    def draw(self, context):
        layout = self.layout

        for entry in self.VALUES:
            if isinstance(entry, tuple):
                value, label = entry
            else:
                value = entry
                label = str(entry)

            operator = layout.operator(self.OPERATOR_IDNAME, text=label)
            operator.value = value


class ScenePropsTargetObjMixin:

    def get_target_obj(self, context):
        scene_props = context.scene.dhpm_props
        return scene_props


# --------------------- TEX SIZE ---------------------

class DHPM_OT_SetPixelMarginTexSizeBase(DHPM_OT_SetPropBase):

    bl_label = 'Set Texture Size'
    bl_description = "Set Texture Size to one of the suggested values"
    PROP_ID = 'pixel_margin_tex_size'
    

class DHPM_OT_SetPixelMarginTexSizeScene(DHPM_OT_SetPixelMarginTexSizeBase, ScenePropsTargetObjMixin, SetPropPropertiesMixin):

    bl_idname = 'dpacker.set_pixel_margin_tex_size_scene'


    
class DHPM_OT_SetPixelMarginTexSizeGroup(DHPM_OT_SetPixelMarginTexSizeBase, SetPropPropertiesMixin):

    bl_idname = 'dpacker.set_pixel_margin_tex_size_group'

    

class DHPM_MT_SetPixelMarginTexSizeBase(DHPM_MT_SetPropBase):

    VALUES = [
        16,
        32,
        64,
        128,
        256,
        512,
        (1024, '1K'),
        (2048, '2K'),
        (4096, '4K'),
        (8192, '8K'),
        (16384,'16K')]


class DHPM_MT_SetPixelMarginTexSizeScene(DHPM_MT_SetPixelMarginTexSizeBase):

    bl_idname = "DHPM_MT_SetPixelMarginTexSizeScene"
    bl_label = "Set Texture Size"

    OPERATOR_IDNAME = DHPM_OT_SetPixelMarginTexSizeScene.bl_idname


class DHPM_MT_SetPixelMarginTexSizeGroup(DHPM_MT_SetPixelMarginTexSizeBase):

    bl_idname = "DHPM_MT_SetPixelMarginTexSizeGroup"
    bl_label = "Set Texture Size"

    OPERATOR_IDNAME = DHPM_OT_SetPixelMarginTexSizeGroup.bl_idname
