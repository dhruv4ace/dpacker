
from ...operator_1 import DHPM_OT_Engine, ModeIdAttributeMixin
from ...enums import *
from ...utils import *
from bpy.props import BoolProperty

class DHPM_OT_Pack(DHPM_OT_Engine, ModeIdAttributeMixin):

    bl_idname = 'dpacker.pack'
    bl_label = 'Pack'
    bl_description = 'Pack selected UV islands'
