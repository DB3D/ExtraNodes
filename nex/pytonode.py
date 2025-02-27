# SPDX-FileCopyrightText: 2025 BD3D DIGITAL DESIGN (Dorian B.)
#
# SPDX-License-Identifier: GPL-2.0-or-later


import bpy 

from mathutils import Color, Euler, Matrix, Quaternion, Vector
from collections import namedtuple
RGBAColor = namedtuple('RGBAColor', ['r','g','b','a'])


def convert_pyvar_to_data(py_variable):
    """Convert a given python variable into data we can use to create and assign sockets"""
    #TODO do we want to support numpy as well? or else?

    value = py_variable

    #we sanatize out possible types depending on their length
    matrix_special_label = ''
    if (type(value) in {tuple, list, set, Vector, Euler, bpy.types.bpy_prop_array}):

        value = list(value)
        n = len(value)

        if (n == 1):
            value = float(value[0])

        elif (n <= 3):
            value = Vector(value + [0.0]*(3 - n))

        elif (n == 4):
            value = RGBAColor(*value)

        elif (4 < n <= 16):
            if (n < 16):
                matrix_special_label = f'List[{len(value)}]'
                nulmatrix = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
                value.extend(nulmatrix[len(value):])
            value =  Matrix([value[i*4:(i+1)*4] for i in range(4)])

        else:
            raise TypeError(f"'{type(value).__name__.title()}' of len {n} not supported")

    match value:

        case bool():
            repr_label = str(value)
            socket_type = 'NodeSocketBool'

        case int():
            repr_label = str(value)
            socket_type = 'NodeSocketInt'

        case float():
            repr_label = str(round(value,4))
            socket_type = 'NodeSocketFloat'

        case str():
            repr_label = '"'+value+'"'
            socket_type = 'NodeSocketString'

        case Vector():
            repr_label = str(tuple(round(n,4) for n in value))
            socket_type = 'NodeSocketVector'

        case Color():
            value = RGBAColor(*value,1) #add alpha channel
            repr_label = str(tuple(round(n,4) for n in value))
            socket_type = 'NodeSocketColor'

        case RGBAColor():
            repr_label = str(tuple(round(n,4) for n in value))
            socket_type = 'NodeSocketColor'

        case Quaternion():
            repr_label = str(tuple(round(n,4) for n in value))
            socket_type = 'NodeSocketRotation'

        case Matrix():
            repr_label = "MatrixValue" if (not matrix_special_label) else matrix_special_label
            socket_type = 'NodeSocketMatrix'

        case bpy.types.Object():
            repr_label = f'D.objects["{value.name}"]'
            socket_type = 'NodeSocketObject'

        case bpy.types.Collection():
            repr_label = f'D.collections["{value.name}"]'
            socket_type = 'NodeSocketCollection'

        case bpy.types.Material():
            repr_label = f'D.materials["{value.name}"]'
            socket_type = 'NodeSocketMaterial'

        case bpy.types.Image():
            repr_label = f'D.images["{value.name}"]'
            socket_type = 'NodeSocketImage'

        case _:
            raise TypeError(f"'{type(value).__name__.title()}' not supported")

    return value, repr_label, socket_type
