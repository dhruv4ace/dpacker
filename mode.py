from .blend import get_prefs
import sys
from collections import defaultdict
import _bpy
import bpy
from bpy.props import StringProperty

class ModeType:
    HIDDEN = 0
    MAIN = 1
    AUX = 2

class OperatorMetadata:

    def __init__(self, idname, label=None, properties=None, scale_y=1.0):
        self.idname = idname
        self.label = _bpy.ops.get_rna_type(idname).name if label is None else label
        self.properties = properties
        self.scale_y = scale_y

    def set_properties(self, op):
        if self.properties is None:
            return

        for prop, prop_value in self.properties:
            setattr(op, prop, prop_value)

class DHPM_Mode_Generic:

    MODE_PRIORITY = sys.maxsize
    MODE_TYPE = ModeType.HIDDEN
    MODE_HELP_URL_SUFFIX = None

    def subpanels_base(self):

        output = self.subpanels()
        return output

    def subpanels(self):

        return []

    def __init__(self, context):

        self.context = context
        self.scene_props = context.scene.dhpm_props
        self.prefs = get_prefs()
        self.op = None

    def pre_operation(self):
        pass

    def init_op(self, op):

        self.op = op
        self.pre_operation()

    def append_mode_name_to_op_label(self):
        return False

    def grouping_enabled(self):

        return False

    def group_target_box_editing(self):

        return False

    def draw_operator(self, layout, op_metadata):

        row = layout.row(align=True)
        row.scale_y = op_metadata.scale_y
        label = op_metadata.label
        if self.append_mode_name_to_op_label() and self.prefs.append_mode_name_to_op_label:
            label = "{} ({})".format(label, self.MODE_NAME)
        op = row.operator(op_metadata.idname, text=label)
        if (hasattr(op, 'mode_id')):
            op.mode_id = self.MODE_ID

        op_metadata.set_properties(op)

    def operators(self):

        output = []
        if hasattr(self, 'OPERATOR_IDNAME'):
            output.append(OperatorMetadata(self.OPERATOR_IDNAME))

        return output

    def draw(self, layout):

        operators = self.operators()

        if len(operators) == 0:
            return

        for op_metadata in operators:
            self.draw_operator(layout, op_metadata)

class DHPM_Mode_Main(DHPM_Mode_Generic):

    MODE_TYPE = ModeType.MAIN

    @classmethod
    def enum_name(cls):
        return "{} [{}]".format(cls.MODE_NAME, cls.MODE_CATEGORY.NAME)

class DHPM_ModeCategory_Packing:

    PRIORITY = 1000
    NAME = 'Packing'
   
