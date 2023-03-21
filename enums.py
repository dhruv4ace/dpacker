import bpy
from .blend import get_prefs

class OpFinishedException(Exception):
    pass

class OpAbortedException(Exception):
    pass

class EnumValue:

    @classmethod
    def to_blend_items(cls, enum_values):

        prefs = get_prefs()
        items = []

        for enum_val in enum_values:
            supported = (enum_val.req_feature == '') or getattr(prefs, 'FEATURE_' + enum_val.req_feature)

            items.append(enum_val.to_blend_item(supported))

        return items

    def __init__(self, code, name, desc='', req_feature=''):
        self.code = code
        self.name = name
        self.desc = desc
        self.req_feature = req_feature

    def to_blend_item(self, supported=True):

        if supported:
            name =  self.name
        else:
            name = self.name + ' ' 

        return (self.code, name, self.desc, int(self.code))

class DhpmOpcode:
    REPORT_VERSION = 0
    EXECUTE_SCENARIO = 1

class DhpmMessageCode:
    PHASE = 0
    VERSION = 1
    BENCHMARK = 2
    ISLANDS = 3
    OUT_ISLANDS = 4
    LOG = 5

class DhpmOutIslandsSerializationFlags:
    CONTAINS_TRANSFORM = 1
    CONTAINS_IPARAMS = 2
    CONTAINS_FLAGS = 4
    CONTAINS_VERTICES = 8

class DhpmIslandFlags:
    OVERLAPS = 1
    OUTSIDE_TARGET_BOX = 2
    ALIGNED = 4
    SELECTED = 8

class DhpmFeatureCode:
    DEMO = 0
    ISLAND_ROTATION = 1
    OVERLAP_CHECK = 2
    PACKING_DEPTH = 3
    HEURISTIC_SEARCH = 4
    PACK_RATIO = 5
    PACK_TO_OTHERS = 6
    GROUPING = 7
    LOCK_OVERLAPPING = 8
    ADVANCED_HEURISTIC = 9
    SELF_INTERSECT_PROCESSING = 10
    VALIDATION = 11
    MULTI_DEVICE_PACK = 12
    TARGET_BOX = 13
    ISLAND_ROTATION_STEP = 14
    PACK_TO_TILES = 15

class DhpmLogType:
    STATUS = 0
    INFO = 1
    WARNING = 2
    ERROR = 3
    HINT = 4

class DhpmRetCode:
    NOT_SET = -1
    SUCCESS = 0
    FATAL_ERROR = 1
    NO_SPACE = 2
    CANCELLED = 3
    INVALID_ISLANDS = 4
    NO_SIUTABLE_DEVICE = 5
    NO_UVS = 6
    INVALID_INPUT = 7
    WARNING = 8

class DhpmPhaseCode:
    RUNNING = 0
    STOPPED = 1
    DONE = 2

class DhpmFixedScaleStrategy:
    BOTTOM_TOP = EnumValue('0', 'Bottom-Top')
    LEFT_RIGHT = EnumValue('1', 'Left-Right')
    SQUARE = EnumValue('2', 'Square')

    @classmethod
    def to_blend_items(cls):
        return (cls.BOTTOM_TOP.to_blend_item(), cls.LEFT_RIGHT.to_blend_item(), cls.SQUARE.to_blend_item())

class DhpmLockOverlappingMode:
    DISABLED = EnumValue('0', 'Disabled', 'Not used')
    ANY_PART = EnumValue('1', 'Any Part')
    EXACT = EnumValue('2', 'Exact')

    @classmethod
    def to_blend_items(cls):
        return (cls.ANY_PART.to_blend_item(), cls.EXACT.to_blend_item())

class DhpmMapSerializationFlags:
    CONTAINS_FLAGS = 1
    CONTAINS_VERTS_3D = 2

class DhpmFaceInputFlags:
    SELECTED = 1

class DhpmDeviceFlags:
    SUPPORTED = 1
    SUPPORTS_GROUPS_TOGETHER = 2

class DhpmIslandIntParams:
    MAX_COUNT = 16

class OperationStatus:
    ERROR = 0
    WARNING = 1
    CORRECT = 2

class RetCodeMetadata:

    def __init__(self, op_status):
        self.op_status = op_status

RETCODE_METADATA = {
    DhpmRetCode.NOT_SET : RetCodeMetadata(
        op_status=None
    ),
    DhpmRetCode.SUCCESS : RetCodeMetadata(
        op_status=OperationStatus.CORRECT
    ),
    DhpmRetCode.FATAL_ERROR : RetCodeMetadata(
        op_status=OperationStatus.ERROR
    ),
    DhpmRetCode.NO_SPACE : RetCodeMetadata(
        op_status=OperationStatus.WARNING
    ),
    DhpmRetCode.CANCELLED : RetCodeMetadata(
        op_status=OperationStatus.CORRECT
    ),
    DhpmRetCode.INVALID_ISLANDS : RetCodeMetadata(
        op_status=OperationStatus.ERROR
    ),
    DhpmRetCode.NO_SIUTABLE_DEVICE : RetCodeMetadata(
        op_status=OperationStatus.ERROR
    ),
    DhpmRetCode.NO_UVS : RetCodeMetadata(
        op_status=OperationStatus.WARNING
    ),
    DhpmRetCode.INVALID_INPUT : RetCodeMetadata(
        op_status=OperationStatus.ERROR
    ),
    DhpmRetCode.WARNING : RetCodeMetadata(
        op_status=OperationStatus.WARNING
    )
}

class GroupingMethod:
    MATERIAL = EnumValue('0', 'Material')
    # SIMILARITY = EnumValue('1', 'Similarity', Labels.GROUP_METHOD_SIMILARITY_DESC)
    MESH = EnumValue('2', 'Mesh Part')
    OBJECT = EnumValue('3', 'Object')
    MANUAL = EnumValue('4', 'Grouping Scheme (Manual)')
    TILE = EnumValue('5', 'Tile')

    @classmethod
    def to_blend_items(cls):
        return (cls.MATERIAL.to_blend_item(),
                cls.MESH.to_blend_item(),
                cls.OBJECT.to_blend_item(),
                cls.TILE.to_blend_item(),
                cls.MANUAL.to_blend_item())

    @classmethod
    def auto_grouping_enabled(cls, g_method):
        return g_method != cls.MANUAL.code

class TexelDensityGroupPolicy:
    INDEPENDENT = EnumValue(
        '0', 'Independent')

    UNIFORM = EnumValue(
        '1', 'Uniform')

    CUSTOM = EnumValue(
        '2', 'Custom')

    @classmethod
    def to_blend_items(cls):
        return (cls.INDEPENDENT.to_blend_item(), cls.UNIFORM.to_blend_item(), cls.CUSTOM.to_blend_item())

    @classmethod
    def to_blend_items_auto(cls):
        return (cls.INDEPENDENT.to_blend_item(), cls.UNIFORM.to_blend_item())

class GroupLayoutMode:
    AUTOMATIC = EnumValue('0', 'Automatic')
    MANUAL = EnumValue('1', 'Manual')
    AUTOMATIC_HORI = EnumValue('2', 'Automatic (Horizontal)')
    AUTOMATIC_VERT = EnumValue('3', 'Automatic (Vertical)')

    @classmethod
    def to_blend_items(cls):
        return\
            (cls.AUTOMATIC.to_blend_item(),
             cls.AUTOMATIC_HORI.to_blend_item(),
             cls.AUTOMATIC_VERT.to_blend_item(),
             cls.MANUAL.to_blend_item())

    @classmethod
    def to_blend_items_auto(cls):
        return (mode.to_blend_item() for mode in cls.automatic_modes())

    @classmethod
    def automatic_modes(cls):
        return\
            (cls.AUTOMATIC,
             cls.AUTOMATIC_HORI,
             cls.AUTOMATIC_VERT)

    @classmethod
    def is_automatic(cls, mode_code):
        return mode_code in (mode.code for mode in cls.automatic_modes())

    @classmethod
    def supports_tiles_in_row(cls, mode_code):
        return\
            mode_code == cls.AUTOMATIC.code

    @classmethod
    def supports_tile_count(cls, mode_code):
        return cls.is_automatic(mode_code)

class RunScenario:
    _SCENARIOS = {}

    @classmethod
    def add_scenario(cls, scenario):
        cls._SCENARIOS[scenario['id']] = scenario

    @classmethod
    def get_scenario(cls, scenario_id, default=None):
        return cls._SCENARIOS.get(scenario_id, default)
