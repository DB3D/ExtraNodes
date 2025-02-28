# SPDX-FileCopyrightText: 2025 BD3D DIGITAL DESIGN (Dorian B.)
#
# SPDX-License-Identifier: GPL-2.0-or-later

# NOTE this module gather all kind of math function for sockets
#  when executing these functions, it will create and link new nodes automatically, from sockets to sockets.

# TODO it would be nice that we could support a python float value so we directly set a default value.


import bpy 
import inspect

from ..utils.node_utils import link_sockets, frame_nodes

sfloat = bpy.types.NodeSocketFloat


NODE_YOFF, NODE_XOFF = 120, 70
_USER_FUNCTIONS = [] #don't import that directly, use get_user_functions, thanks.


def usernamespace(func):
    """decorator to easily store function names on an orderly manner at runtime"""
    _USER_FUNCTIONS.append(func)
    return func

def get_user_functions(return_types='float'):
    """get all functions and their names, depending on function types"""

    filtered_functions = []
    match return_types:
        case 'float':
            filtered_functions = [f for f in _USER_FUNCTIONS if inspect.signature(f).return_annotation is sfloat]
        case _:
            raise Exception("notSupported")

    return filtered_functions

# nodetree setter functions starting from below

def _floatmath(operation_type:str, sock1:sfloat, sock2:sfloat=None, sock3:sfloat=None,) -> sfloat:
    """generic operation for adding a float math node and linking"""

    ng = sock1.id_data
    last = ng.nodes.active

    location = (0,200,)
    if (last):
        location = (last.location.x+last.width+NODE_XOFF, last.location.y-NODE_YOFF,)

    node = ng.nodes.new('ShaderNodeMath')
    node.operation = operation_type
    node.use_clamp = False
    
    node.location = location
    ng.nodes.active = node #Always set the last node active for the final link
            
    link_sockets(sock1, node.inputs[0])
    if (sock2):
        link_sockets(sock2, node.inputs[1])
    if (sock3):
        link_sockets(sock3, node.inputs[2])

    return node.outputs[0]

@usernamespace
def add(a:sfloat, b:sfloat,) -> sfloat:
    """Addition.\nEquivalent to the '+' symbol."""
    return _floatmath('ADD',a,b)

@usernamespace
def sub(a:sfloat, b:sfloat,) -> sfloat:
    """Subtraction.\nEquivalent to the '-' symbol."""
    return _floatmath('SUBTRACT',a,b)

@usernamespace
def mult(a:sfloat, b:sfloat,) -> sfloat:
    """Multiplications.\nEquivalent to the '*' symbol."""
    return _floatmath('MULTIPLY',a,b)

@usernamespace
def div(a:sfloat, b:sfloat,) -> sfloat:
    """Division.\nEquivalent to the '/' symbol."""
    return _floatmath('DIVIDE',a,b)

@usernamespace
def pow(a:sfloat, n:sfloat,) -> sfloat:
    """A Power n.\nEquivalent to the 'a**n' and '²' symbol."""
    return _floatmath('POWER',a,n)

@usernamespace
def log(a:sfloat, b:sfloat,) -> sfloat:
    """Logarithm A base B."""
    return _floatmath('LOGARITHM',a,b)

@usernamespace
def sqrt(a:sfloat,) -> sfloat:
    """Square Root of A."""
    return _floatmath('SQRT',a)

@usernamespace
def invsqrt(a:sfloat,) -> sfloat:
    """1/ Square Root of A."""
    return _floatmath('INVERSE_SQRT',a)

def _floatmath_nroot(sock1:sfloat, sock2:sfloat,) -> sfloat:
    """special operation to calculate custom root x**(1/n)"""

    ng = sock1.id_data
    last = ng.nodes.active

    location = (0,200,)
    if (last):
        location = (last.location.x+last.width+NODE_XOFF, last.location.y-NODE_YOFF,)

    divnode = ng.nodes.new('ShaderNodeMath')
    divnode.operation = 'DIVIDE'
    divnode.use_clamp = False

    divnode.location = location
    ng.nodes.active = divnode #Always set the last node active for the final link

    divnode.inputs[0].default_value = 1.0
    link_sockets(sock2, divnode.inputs[1])

    pnode = ng.nodes.new('ShaderNodeMath')
    pnode.operation = 'POWER'
    pnode.use_clamp = False

    last = divnode
    location = (last.location.x+last.width+NODE_XOFF, last.location.y-NODE_YOFF,)

    pnode.location = location
    ng.nodes.active = pnode #Always set the last node active for the final link

    link_sockets(sock1, pnode.inputs[0])
    link_sockets(divnode.outputs[0], pnode.inputs[1])
    frame_nodes(ng, divnode, pnode, label='nRoot')
    
    return pnode.outputs[0]

@usernamespace
def nroot(a:sfloat, n:sfloat,) -> sfloat:
    """A Root N. a**(1/n.)"""
    return _floatmath_nroot(a,n,)

@usernamespace
def abs(a:sfloat,) -> sfloat:
    """Absolute of A."""
    return _floatmath('ABSOLUTE',a)

def _floatmath_neg(sock1:sfloat,) -> sfloat:
    """special operation for negative -1 -x ect"""

    ng = sock1.id_data
    last = ng.nodes.active

    location = (0,200,)
    if (last):
        location = (last.location.x+last.width+NODE_XOFF, last.location.y-NODE_YOFF,)

    node = ng.nodes.new('ShaderNodeMath')
    node.operation = 'SUBTRACT'
    node.use_clamp = False
    node.label = 'Negate'

    node.location = location
    ng.nodes.active = node #Always set the last node active for the final link

    node.inputs[0].default_value = 0.0
    link_sockets(sock1, node.inputs[1])
    
    return node.outputs[0]

@usernamespace
def neg(a:sfloat,) -> sfloat:
    """Negate the value of A.\nEquivalent to the symbol '-x.'"""
    return _floatmath_neg(a)

@usernamespace
def min(a:sfloat, b:sfloat,) -> sfloat:
    """Minimum between A & B."""
    return _floatmath('MINIMUM',a,b)

@usernamespace
def smin(a:sfloat, b:sfloat, dist:sfloat,) -> sfloat:
    """Minimum between A & B considering a smoothing distance."""
    return _floatmath('SMOOTH_MIN',a,b,dist)

@usernamespace
def max(a:sfloat, b:sfloat,) -> sfloat:
    """Maximum between A & B."""
    return _floatmath('MAXIMUM',a,b)

@usernamespace
def smax(a:sfloat, b:sfloat, dist:sfloat,) -> sfloat:
    """Maximum between A & B considering a smoothing distance."""
    return _floatmath('SMOOTH_MAX',a,b,dist)

@usernamespace
def round(a:sfloat,) -> sfloat:
    """Round a Float to an Integer."""
    return _floatmath('ROUND',a)

@usernamespace
def floor(a:sfloat,) -> sfloat:
    """Floor a Float to an Integer."""
    return _floatmath('FLOOR',a)

@usernamespace
def ceil(a:sfloat,) -> sfloat:
    """Ceil a Float to an Integer."""
    return _floatmath('CEIL',a)

@usernamespace
def trunc(a:sfloat,) -> sfloat:
    """Trunc a Float to an Integer."""
    return _floatmath('TRUNC',a)

@usernamespace
def frac(a:sfloat,) -> sfloat:
    """Fraction.\nThe fraction part of A."""
    return _floatmath('FRACT',a)

@usernamespace
def mod(a:sfloat, b:sfloat,) -> sfloat:
    """Modulo.\nEquivalent to the '%' symbol."""
    return _floatmath('MODULO',a,b)

@usernamespace
def fmod(a:sfloat, b:sfloat,) -> sfloat:
    """Floored Modulo."""
    return _floatmath('FLOORED_MODULO',a,b)

@usernamespace
def wrap(v:sfloat, a:sfloat, b:sfloat,) -> sfloat:
    """Wrap value to Range A B."""
    return _floatmath('WRAP',v,a,b)

@usernamespace
def snap(v:sfloat, i:sfloat,) -> sfloat:
    """Snap to Increment."""
    return _floatmath('SNAP',v,i)

@usernamespace
def pingpong(v:sfloat, scale:sfloat,) -> sfloat:
    """PingPong. Wrap a value and every other cycles at cycle Scale."""
    return _floatmath('PINGPONG',v,scale)

@usernamespace
def floordiv(a:sfloat, b:sfloat,) -> sfloat: #Custom
    """Floor Division.\nEquivalent to the '//' symbol."""
    _r = div(a,b)
    r = floor(_r)
    frame_nodes(a.id_data, _r.node, r.node, label='FloorDiv')
    return r

@usernamespace
def sin(a:sfloat,) -> sfloat:
    """The Sine of A."""
    return _floatmath('SINE',a)

@usernamespace
def cos(a:sfloat,) -> sfloat:
    """The Cosine of A."""
    return _floatmath('COSINE',a)

@usernamespace
def tan(a:sfloat,) -> sfloat:
    """The Tangent of A."""
    return _floatmath('TANGENT',a)

@usernamespace
def asin(a:sfloat,) -> sfloat:
    """The Arcsine of A."""
    return _floatmath('ARCSINE',a)

@usernamespace
def acos(a:sfloat,) -> sfloat:
    """The Arccosine of A."""
    return _floatmath('ARCCOSINE',a)

@usernamespace
def atan(a:sfloat,) -> sfloat:
    """The Arctangent of A."""
    return _floatmath('ARCTANGENT',a)

@usernamespace
def hsin(a:sfloat,) -> sfloat:
    """The Hyperbolic Sine of A."""
    return _floatmath('SINH',a)

@usernamespace
def hcos(a:sfloat,) -> sfloat:
    """The Hyperbolic Cosine of A."""
    return _floatmath('COSH',a)

@usernamespace
def htan(a:sfloat,) -> sfloat:
    """The Hyperbolic Tangent of A."""
    return _floatmath('TANH',a)

@usernamespace
def rad(a:sfloat,) -> sfloat:
    """Convert from Degrees to Radians."""
    return _floatmath('RADIANS',a)

@usernamespace
def deg(a:sfloat,) -> sfloat:
    """Convert from Radians to Degrees."""
    return _floatmath('DEGREES',a)

def _mix(data_type:str, sock1:sfloat, sock2:sfloat, sock3:sfloat,) -> sfloat:
    """generic operation for adding a mix node and linking"""

    ng = sock1.id_data
    last = ng.nodes.active

    location = (0,200,)
    if (last):
        location = (last.location.x+last.width+NODE_XOFF, last.location.y-NODE_YOFF,)

    node = ng.nodes.new('ShaderNodeMix')
    node.data_type = data_type
    node.clamp_factor = False

    node.location = location
    ng.nodes.active = node #Always set the last node active for the final link

    link_sockets(sock1, node.inputs[0])

    # Need to choose socket depending on node data_type (hidden sockets)
    match data_type:
        case 'FLOAT':
            link_sockets(sock2, node.inputs[2])
            link_sockets(sock3, node.inputs[3])
        case _:
            raise Exception("Integration Needed")

    return node.outputs[0]

@usernamespace
def lerp(f:sfloat, a:sfloat, b:sfloat,) -> sfloat:
    """Mix.\nLinear Interpolation of value A and B from given factor."""
    return _mix('FLOAT',f,a,b)

@usernamespace
def mix(f:sfloat, a:sfloat, b:sfloat,) -> sfloat: 
    """Alternative notation to lerp() function."""
    return lerp(f,a,b)

def _floatclamp(clamp_type:str, sock1:sfloat, sock2:sfloat, sock3:sfloat,) -> sfloat:
    """generic operation for adding a mix node and linking"""
    
    ng = sock1.id_data
    last = ng.nodes.active
    
    location = (0,200,)
    if (last):
        location = (last.location.x+last.width+NODE_XOFF, last.location.y-NODE_YOFF,)

    node = ng.nodes.new('ShaderNodeClamp')
    node.clamp_type = clamp_type

    node.location = location
    ng.nodes.active = node #Always set the last node active for the final link

    link_sockets(sock1, node.inputs[0])
    link_sockets(sock2, node.inputs[1])
    link_sockets(sock3, node.inputs[2])

    return node.outputs[0]

@usernamespace
def clamp(v:sfloat, a:sfloat, b:sfloat,) -> sfloat:
    """Clamp value between min an max."""
    return _floatclamp('MINMAX',v,a,b)

@usernamespace
def clampr(v:sfloat, a:sfloat, b:sfloat,) -> sfloat:
    """Clamp value between auto-defined min/max."""
    return _floatclamp('RANGE',v,a,b)

def _maprange(data_type:str, interpolation_type:str, sock1:sfloat, sock2:sfloat, sock3:sfloat, sock4:sfloat, sock5:sfloat, sock6:sfloat=None,) -> sfloat:
    """generic operation for adding a remap node and linking"""

    ng = sock1.id_data
    last = ng.nodes.active

    location = (0,200,)
    if (last):
        location = (last.location.x+last.width+NODE_XOFF, last.location.y-NODE_YOFF,)

    node = ng.nodes.new('ShaderNodeMapRange')
    node.data_type = data_type
    node.interpolation_type = interpolation_type
    node.clamp = False

    node.location = location
    ng.nodes.active = node #Always set the last node active for the final link

    link_sockets(sock1, node.inputs[0])
    link_sockets(sock2, node.inputs[1])
    link_sockets(sock3, node.inputs[2])
    link_sockets(sock4, node.inputs[3])
    link_sockets(sock5, node.inputs[4])
    if (sock6):
        link_sockets(sock6, node.inputs[5])
    
    return node.outputs[0]

@usernamespace
def map(val:sfloat, a:sfloat, b:sfloat, x:sfloat, y:sfloat,) -> sfloat:
    """Map Range.\nRemap a value from a fiven A,B range to a X,Y range."""
    return _maprange('FLOAT','LINEAR',val,a,b,x,y)

@usernamespace
def mapst(val:sfloat, a:sfloat, b:sfloat, x:sfloat, y:sfloat, step:sfloat,) -> sfloat:
    """Map Range (Stepped).\nRemap a value from a fiven A,B range to a X,Y range with step."""
    return _maprange('FLOAT','STEPPED',val,a,b,x,y,step)

@usernamespace
def mapsmo(val:sfloat, a:sfloat, b:sfloat, x:sfloat, y:sfloat,) -> sfloat:
    """Map Range (Smooth).\nRemap a value from a fiven A,B range to a X,Y range."""
    return _maprange('FLOAT','SMOOTHSTEP',val,a,b,x,y)

@usernamespace
def mapsmoo(val:sfloat, a:sfloat, b:sfloat, x:sfloat, y:sfloat,) -> sfloat:
    """Map Range (Smoother).\nRemap a value from a fiven A,B range to a X,Y range."""
    return _maprange('FLOAT','SMOOTHERSTEP',val,a,b,x,y)

#TODO support comparison functions
# def equal(a:sfloat, b:sfloat,)
# def notequal(a:sfloat, b:sfloat,)
# def aequal(a:sfloat, b:sfloat, threshold:sfloat,)
# def anotequal(a:sfloat, b:sfloat, threshold:sfloat,)
# def issmaller(a:sfloat, b:sfloat,)
# def isasmaller(a:sfloat, b:sfloat, threshold:sfloat,)
# def isbigger(a:sfloat, b:sfloat,)
# def isabigger(a:sfloat, b:sfloat, threshold:sfloat,)
# def isbetween(a:sfloat, x:sfloat, y:sfloat,)
# def isabetween(a:sfloat, x:sfloat, y:sfloat, threshold:sfloat,)
# def isbetweeneq(a:sfloat, x:sfloat, y:sfloat,)
