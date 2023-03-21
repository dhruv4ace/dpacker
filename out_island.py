
from .connection import (
        force_read_int,
        force_read_floats,
        force_read_ints,
        read_int_array,
        force_read_elems
    )
from .island_params import IParamInfo
from .enums import DhpmOutIslandsSerializationFlags, DhpmIslandIntParams

from mathutils import Matrix


class OutIsland:

    def __init__(self, idx, transform, iparam_values, flags, face_order, vertices):
        self.idx = idx
        self.transform = transform
        self.iparam_values = iparam_values
        self.flags = flags
        self.face_order = face_order
        self.vertices = vertices


class OutIslands:

    def __init__(self, out_islands_msg):

        self.islands = []
        self.dirty_iparam_indices = []

        TRANSFORM_FLOAT_LEN = 9

        island_count = force_read_int(out_islands_msg)
        serialization_flags = force_read_int(out_islands_msg)

        contains_transform = (serialization_flags & DhpmOutIslandsSerializationFlags.CONTAINS_TRANSFORM) > 0
        contains_iparams = (serialization_flags & DhpmOutIslandsSerializationFlags.CONTAINS_IPARAMS) > 0
        contains_flags = (serialization_flags & DhpmOutIslandsSerializationFlags.CONTAINS_FLAGS) > 0
        contains_vertices = (serialization_flags & DhpmOutIslandsSerializationFlags.CONTAINS_VERTICES) > 0

        if contains_iparams:
            self.dirty_iparam_indices = read_int_array(out_islands_msg)

        island_indicies = force_read_ints(out_islands_msg, island_count)

        if contains_transform:
            transform_array_raw = force_read_floats(out_islands_msg, TRANSFORM_FLOAT_LEN * island_count)
        else:
            transform_array_raw = None

        if contains_iparams:
            iparam_values_array_raw = force_read_elems(out_islands_msg, IParamInfo.PARAM_TYPE_MARK, DhpmIslandIntParams.MAX_COUNT * island_count)
        else:
            iparam_values_array_raw = None

        if contains_flags:
            flags_array_raw = force_read_ints(out_islands_msg, island_count)
        else:
            flags_array_raw = None

        if contains_vertices:
            face_order_array_raw = []
            vertices_array_raw = []
            
            for i_idx in range(island_count):
                face_order = read_int_array(out_islands_msg)
                face_order_array_raw.append(face_order)

                vert_count = force_read_int(out_islands_msg)
                vert_coords_raw = force_read_floats(out_islands_msg, 2*vert_count)
                vertices = [(vert_coords_raw[2*v_idx], vert_coords_raw[2*v_idx+1]) for v_idx in range(vert_count)]
                vertices_array_raw.append(vertices)

        else:
            face_order_array_raw = None
            vertices_array_raw = None

        for i in range(island_count):

            if transform_array_raw is not None:
                transform_raw = transform_array_raw[TRANSFORM_FLOAT_LEN * i : TRANSFORM_FLOAT_LEN * (i + 1)]
                transform = Matrix([transform_raw[0:3], transform_raw[3:6], transform_raw[6:9]])
            else:
                transform = None

            if iparam_values_array_raw is not None:
                iparam_values = iparam_values_array_raw[DhpmIslandIntParams.MAX_COUNT * i : DhpmIslandIntParams.MAX_COUNT * (i + 1)]
            else:
                iparam_values = None

            if flags_array_raw is not None:
                flags = flags_array_raw[i]
            else:
                flags = None

            if face_order_array_raw is not None:
                face_order = face_order_array_raw[i]
            else:
                face_order = None

            if vertices_array_raw is not None:
                vertices = vertices_array_raw[i]
            else:
                vertices = None

            self.islands.append(OutIsland(island_indicies[i], transform, iparam_values, flags, face_order, vertices))
