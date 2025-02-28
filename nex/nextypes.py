# SPDX-FileCopyrightText: 2025 BD3D DIGITAL DESIGN (Dorian B.)
#
# SPDX-License-Identifier: GPL-2.0-or-later

# TODO support more operand 
#  - __floordiv__
#  - __modulo__

# TODO implement NexVec
#  - support between vec and vec
#  - vec to float = error, float to vec == possible
#  - dunder operation between NexFloat et NexVec, see how NotImplemented pass the ball to the other class..
#  - Vec itter and slicing? using separate? x,y,z = NexVex should work, x=Vex[0] should work for e in Vec should work as well.
#  - float in vec should work as well

# TODO implement functions
#  - implement a few functions as test, see how a functions that can both work with Vec and Float will work
#    because there will be name collision. perhaps could toy with namespace similar to cpp? Hmm. this would solve it

# TODO implement NexBool
#  - with Nexbool comes comparison operations. == <= ect..

# TODO later 
#  Better errors for user:
#  - need better traceback error for NexError so user can at least now the line where it got all wrong.
#  - it's a bit useless to see a Cannot add 'AnonymousVariable' of type.. with type.. 
#    perhaps just don't tell the user varname if we can print the line?

# TODO later
#  Optimization:
#  - Is the NexFactory bad for performance? these factory are defining classes perhaps 10-15 times per execution
#    and execution can be at very frequent. Perhaps we can initiate the factory at node.init()? If we do that, 
#    let's first check if it's safe to do so. Maybe, storing objects there is not supported. 
#    AS a Reminder: we are storing nodetree objects in there, we'll probably need to only store the nodetree name. & get rid of node_inst.
#  - If we do a constant + Nex + constant + Nex + constant, we'll create 3 constant nodes. Unsure how to mitigate this.
#    ideally we 

# TODO nodes location
# (?) Doing math operation on a value node for the first time should relocate the value node near it's math ope. Note that
# if we optimize the note above, this thought is to be dismissed


import bpy

import traceback
from collections.abc import Iterable
from mathutils import Vector

from ..__init__ import dprint
from ..nex.pytonode import convert_pyvar_to_data
from ..nex import nodesetter
from ..utils.node_utils import (
    create_new_nodegroup,
    set_socket_defvalue,
    get_socket,
    get_socket_type,
    set_socket_type,
    create_socket,
    get_socket_from_socketui,
    remove_socket,
    set_socket_label,
    link_sockets,
    create_constant_input,
)


NEXEQUIVALENCE = {

    #inputs
    'inbool':  'NodeSocketBool',
    'inint':   'NodeSocketInt',
    'infloat': 'NodeSocketFloat',
    'invec':   'NodeSocketVector',
    'incol':   'NodeSocketColor',
    'inquat':  'NodeSocketRotation',
    'inmat':   'NodeSocketMatrix',

    #outputs
    'outbool': 'NodeSocketBool',
    'outint':  'NodeSocketInt',
    'outfloat':'NodeSocketFloat',
    'outvec':  'NodeSocketVector',
    'outcol':  'NodeSocketColor',
    'outquat': 'NodeSocketRotation',
    'outmat':  'NodeSocketMatrix',

}


class NexError(Exception):
    def __init__(self, message):
        super().__init__(message)


class Nex:
    """parent class of all Nex subclasses"""

    _instance_counter = 0 # - Needed to define nxid, see nxid note.
    node_inst = None      # - the node affiliated with this Nex type
    node_tree = None      # - the node.nodetree affiliated with this Nex type
    nxstype = ''          # - the type of socket the Nex type is using
    nxchar = ''           # - the short name of the nex type (for display reasons)

    def __init__(*args, **kwargs):
        nxsock = None  # - The most important part of a NexType, it's association with an output socket!
        nxvname = None # - The name of the variable, if available. High change the variable will be anonymous. Unsure if it's needed to keep this
        nxid = None    # - In order to not constantly rebuild the nodetree, but still update 
                       # some python evaluated values to the nodetree constants (nodes starting with "C|" in the tree)
                       # we need to have some sort of stable id for our nex Instances.
                       # the problem is that these instances can be anonymous. So here i've decided to identify by instance generation count.

    def __repr__(self):
        return f"<{self.nxstype}{self.nxid}'{self.nxvname}'>"
        #return f"<{type(self)}{self.nxid} nxvname='{self.nxvname}'  nxsock=`{self.nxsock}` isoutput={self.nxsock.is_output}' socketnode='{self.nxsock.node.name}''{self.nxsock.node.label}'>"


def generate_tag(NexType, function, *variables, start='F'):
    """generate an unique tag for a function and their args"""

    # ex 'F|f.pow(f4,f5)'
    #    'F|f.mult(f2,PyInt)'
    # TODO would be nice to write output Nex 'F|f.pow(f1,f2)=f3' for easy debug!

    argrepr = []
    for v in variables:
        if isinstance(v,Nex):
              argrepr.append(f"{v.nxchar}{v.nxid}")
        else: argrepr.append(f"Py{type(v).__name__.title()}")

    innertag = ",".join(argrepr)
    tag = f"{start}|{NexType.nxchar}.{function.__name__}({innertag})"

    return tag


def call_Nex_operand(NexType, sockfunc, *variables, uniquetag:str=None, NexTypeReturnSpecial=None):
    """call the sockfunc related to the operand with sockets of our NexTypes, and return a 
    new NexType from the newly formed socket.
    
    Each new node the sockfuncs will create will be tagged, it is essential that we don't create & 
    link the nodes if there's no need to do so, as a Nex script can be executed very frequently. 
    
    We tag them using the Nex id and types to ensure uniqueness of our values. If a tag already exists, 
    the 'update_if_exists' parameter of the nodesetter functions will make sure to only update the values
    of an existing node that already exists"""

    try:
        r = sockfunc(NexType.node_tree, *variables, update_if_exists=uniquetag,)

    except nodesetter.InvalidTypePassedToSocket as e:
        msg = f"SocketTypeError. Function '{sockfunc.__name__}' Expected parameters in " + str(e).split('Expected parameters in ')[1]
        raise NexError(msg) #Note that a previous NexError Should've been raised prior to that.

    except Exception as e:
        print(f"ERROR: call_Nex_operand.sockfunc() caught error {type(e).__name__}")
        raise

    # Then return a Nextype..
    # Support for multi outputs & if output type is not the same as input with NexTypeReturnSpecial
    if type(r) is tuple:
        if (NexTypeReturnSpecial is not None):
            return tuple(NexTypeReturnSpecial(fromsocket=s) for s in r)
        return tuple(NexType(fromsocket=s) for s in r)

    return NexType(fromsocket=r)


# unused for now
# def create_Nex_constant(node_tree, NexType, nodetype:str, value,):
#     """Create a new input node (if not already exist) ensure it's default value, then assign to a NexType & return it."""
#
#     new = NexType(manualdef=True)
#     tag = f"{new.nxchar}{new.nxid}"
#
#     # create_constant_input() is smart it will create the node only if it doesn't exist, & ensure (new?) values
#     newsock = create_constant_input(node_tree, nodetype, value, tag)
#
#     new.nxsock = newsock
#     new.nxvname = 'AnonymousVariable'
#
#     return new


def py_to_Vec3(value):
    match value:
        case Vector():
            if (len(value)!=3): raise NexError(f"ValueError. Vector({value[:]}) should have 3 elements for fitting in a 'SocketVector'.")
            return value
        case list() | set() | tuple():
            if (len(value)!=3): raise NexError(f"ValueError. Itterable '{value}' should have 3 elements for fitting in a 'SocketVector'.")
            return Vector(value)
        case int() | float() | bool():
            return Vector((float(value), float(value), float(value),))
        case _:
            raise Exception(f"Unsuported type for {value}")


def NexFactory(factor_customnode_instance, factory_classname:str, factory_outsocktype:str='',):
    """return a nex type, which is simply an overloaded custom type that automatically arrange links and nodes and
    set default values. The nextypes will/should only build the nodetree and links when neccessary"""


    # ooooo      ooo                       oooooooooooo oooo                          .   
    # `888b.     `8'                       `888'     `8 `888                        .o8   
    #  8 `88b.    8   .ooooo.  oooo    ooo  888          888   .ooooo.   .oooo.   .o888oo 
    #  8   `88b.  8  d88' `88b  `88b..8P'   888oooo8     888  d88' `88b `P  )88b    888   
    #  8     `88b.8  888ooo888    Y888'     888    "     888  888   888  .oP"888    888   
    #  8       `888  888    .o  .o8"'88b    888          888  888   888 d8(  888    888 . 
    # o8o        `8  `Y8bod8P' o88'   888o o888o        o888o `Y8bod8P' `Y888""8o   "888" 
                                                                                        
    class NexFloat(Nex):
        
        _instance_counter = 0
        node_inst = factor_customnode_instance
        node_tree = node_inst.node_tree
        nxstype = 'NodeSocketFloat'
        nxchar = 'f'

        def __init__(self, varname='', value=None, fromsocket=None, manualdef=False):

            #create a stable identifier for our NexObject
            self.nxid = NexFloat._instance_counter
            NexFloat._instance_counter += 1

            #on some occation we might want to first initialize this new python object, and define it later (ot get the id)
            if (manualdef):
                return None

            #initialize from a socket?
            if (fromsocket is not None):
                self.nxsock, self.nxvname = fromsocket, 'AnonymousVariable'
                return None
            
            # Now, define different initialization depending on given value type
            # NOTE to avoid the pitfalls of name resolution within class definitions..

            type_name = type(value).__name__
            match type_name: 

                # a:infloat = anotherinfloat
                case _ if ('Nex' in type_name):
                    raise NexError(f"Invalid use of Inputs. Cannot assign 'SocketInput' to 'SocketInput'.")

                # is user toying with  output? output cannot be reused in any way..
                case 'NexOutput':
                    raise NexError(f"Invalid use of Outputs. Cannot assign 'SocketOutput' to 'SocketInput'.")

                # initial creation by assignation, we need to create a socket type
                case 'int' | 'float' | 'bool':
                    assert varname!='', "Nex Initialization should always define a varname."
                    outsock = get_socket(self.node_tree, in_out='INPUT', socket_name=varname,)
                    assert outsock is not None, f"The socket '{varname}' do not exist in your node inputs."
                    fval = float(value)
                    set_socket_defvalue(self.node_tree, socket=outsock, node=self.node_inst, value=fval, in_out='INPUT')
                    self.nxsock, self.nxvname = outsock, varname

                # wrong initialization?
                case _:
                    raise NexError(f"SocketTypeError. Cannot assign var '{varname}' of type '{type(value).__name__}' to 'SocketFloat'.")

            print(f'DEBUG: {type(self).__name__}.__init__({value}). Instance:',self)
            return None

        # ---------------------
        # NexFloat Additions

        def __add__(self, other): # self + other
            type_name = type(other).__name__
            match type_name:
                case 'NexFloat':
                    a = self.nxsock ; b = other.nxsock
                    sockfunc = nodesetter.add
                case 'NexVec':
                    return NotImplemented
                case 'int' | 'float' | 'bool': 
                    a = self.nxsock ; b = float(other)
                    sockfunc = nodesetter.add
                case _:
                    raise NexError(f"SocketTypeError. Cannot add '{self.nxvname}' of type 'SocketFloat' to '{type(other).__name__}'.")
            tag = generate_tag(NexFloat, sockfunc, self, other,)
            return call_Nex_operand(NexFloat, sockfunc, a, b, uniquetag=tag)

        def __radd__(self, other): # other + self
            # Multiplication is commutative.
            return self.__add__(other)

        # ---------------------
        # NexFloat Subtraction

        def __sub__(self, other): # self - other
            type_name = type(other).__name__
            match type_name:
                case 'NexFloat':
                    a = self.nxsock ; b = other.nxsock
                    sockfunc = nodesetter.sub
                case 'NexVec':
                    return NotImplemented
                case 'int' | 'float' | 'bool':
                    a = self.nxsock ; b = float(other)
                    sockfunc = nodesetter.sub
                case _:
                    raise NexError(f"SocketTypeError. Cannot subtract '{self.nxvname}' of type 'SocketFloat' with '{type(other).__name__}'.")
            tag = generate_tag(NexFloat, sockfunc, self, other,)
            return call_Nex_operand(NexFloat, sockfunc, a, b, uniquetag=tag)

        def __rsub__(self, other): # other - self
            type_name = type(other).__name__
            match type_name:
                case 'NexVec':
                    return NotImplemented
                case 'int' | 'float' | 'bool':
                    a = float(other) ; b = self.nxsock
                    sockfunc = nodesetter.sub
                case _:
                    raise NexError(f"SocketTypeError. Cannot subtract '{type(other).__name__}' with 'SocketFloat'.")
            tag = generate_tag(NexFloat, sockfunc, self, other,)
            return call_Nex_operand(NexFloat, sockfunc, a, b, uniquetag=tag)

        # ---------------------
        # NexFloat Multiplication

        def __mul__(self, other): # self * other
            type_name = type(other).__name__
            match type_name:
                case 'NexFloat':
                    a = self.nxsock ; b = other.nxsock
                    sockfunc = nodesetter.mult
                case 'NexVec':
                    return NotImplemented
                case 'int' | 'float' | 'bool':
                    a = self.nxsock ; b = float(other)
                    sockfunc = nodesetter.mult
                case _:
                    raise NexError(f"SocketTypeError. Cannot multiply '{self.nxvname}' of type 'SocketFloat' with '{type(other).__name__}'.")
            tag = generate_tag(NexFloat, sockfunc, self, other,)
            return call_Nex_operand(NexFloat, sockfunc, a, b, uniquetag=tag)

        def __rmul__(self, other): # other * self
            # Multiplication is commutative.
            return self.__mul__(other)

        # ---------------------
        # NexFloat True Division

        def __truediv__(self, other): # self / other
            type_name = type(other).__name__
            match type_name:
                case 'NexFloat':
                    a = self.nxsock ; b = other.nxsock
                    sockfunc = nodesetter.div
                case 'NexVec':
                    return NotImplemented
                case 'int' | 'float' | 'bool':
                    a = self.nxsock ; b = float(other)
                    sockfunc = nodesetter.div
                case _:
                    raise NexError(f"SocketTypeError. Cannot divide '{self.nxvname}' of type 'SocketFloat' by '{type(other).__name__}'.")
            tag = generate_tag(NexFloat, sockfunc, self, other,)
            return call_Nex_operand(NexFloat, sockfunc, a, b, uniquetag=tag)

        def __rtruediv__(self, other): # other / self
            type_name = type(other).__name__
            match type_name:
                case 'NexVec':
                    return NotImplemented
                case 'int' | 'float' | 'bool':
                    a = float(other) ; b = self.nxsock
                    sockfunc = nodesetter.div
                case _:
                    raise NexError(f"SocketTypeError. Cannot divide '{type(other).__name__}' by 'SocketFloat'.")
            tag = generate_tag(NexFloat, sockfunc, self, other,)
            return call_Nex_operand(NexFloat, sockfunc, a, b, uniquetag=tag)

        # ---------------------
        # NexFloat Power

        def __pow__(self, other): #self ** other
            type_name = type(other).__name__
            match type_name:
                case 'NexFloat':
                    a = self.nxsock ; b = other.nxsock
                    sockfunc = nodesetter.pow
                case 'NexVec':
                    return NotImplemented
                case 'int' | 'float' | 'bool':
                    a = self.nxsock ; b = float(other)
                    sockfunc = nodesetter.pow
                case _:
                    raise NexError(f"SocketTypeError. Cannot raise '{self.nxvname}' of type 'SocketFloat' to the power of '{type(other).__name__}'.")
            tag = generate_tag(NexFloat, sockfunc, self, other,)
            return call_Nex_operand(NexFloat, sockfunc, a, b, uniquetag=tag)

        def __rpow__(self, other): #other ** self
            type_name = type(other).__name__
            match type_name:
                case 'NexVec':
                    return NotImplemented
                case 'int' | 'float' | 'bool':
                    a = float(other) ; b = self.nxsock
                    sockfunc = nodesetter.pow
                case _:
                    raise NexError(f"SocketTypeError. Cannot raise '{type(other).__name__}' to the power of 'SocketFloat'.")
            tag = generate_tag(NexFloat, sockfunc, self, other,)
            return call_Nex_operand(NexFloat, sockfunc, a, b, uniquetag=tag)

        # ---------------------
        # NexFloat Modulo

        def __mod__(self, other): # self % other
            type_name = type(other).__name__
            match type_name:
                case 'NexFloat':
                    a = self.nxsock ; b = other.nxsock
                    sockfunc = nodesetter.mod
                case 'NexVec':
                    return NotImplemented
                case 'int' | 'float' | 'bool':
                    a = self.nxsock ; b = float(other)
                    sockfunc = nodesetter.mod
                case _:
                    raise NexError(f"SocketTypeError. Cannot compute '{self.nxvname}' of type 'SocketFloat' modulo '{type(other).__name__}'.")
            tag = generate_tag(NexFloat, sockfunc, self, other,)
            return call_Nex_operand(NexFloat, sockfunc, a, b, uniquetag=tag)

        def __rmod__(self, other): # other % self
            type_name = type(other).__name__
            match type_name:
                case 'NexVec':
                    return NotImplemented
                case 'int' | 'float' | 'bool':
                    a = float(other) ; b = self.nxsock
                    sockfunc = nodesetter.mod
                case _:
                    raise NexError(f"SocketTypeError. Cannot compute modulo of '{type(other).__name__}' by 'SocketFloat'.")
            tag = generate_tag(NexFloat, sockfunc, self, other,)
            return call_Nex_operand(NexFloat, sockfunc, a, b, uniquetag=tag)

        # ---------------------
        # NexFloat Floor Division

        def __floordiv__(self, other): # self // other
            type_name = type(other).__name__
            match type_name:
                case 'NexFloat':
                    a = self.nxsock ; b = other.nxsock
                    sockfunc = nodesetter.floordiv
                case 'NexVec':
                    return NotImplemented
                case 'int' | 'float' | 'bool':
                    a = self.nxsock ; b = float(other)
                    sockfunc = nodesetter.floordiv
                case _:
                    raise NexError(f"SocketTypeError. Cannot perform floor division on '{self.nxvname}' of type 'SocketFloat' with '{type(other).__name__}'.")
            tag = generate_tag(NexFloat, sockfunc, self, other,)
            return call_Nex_operand(NexFloat, sockfunc, a, b, uniquetag=tag)

        def __rfloordiv__(self, other): # other // self
            type_name = type(other).__name__
            match type_name:
                case 'NexVec':
                    return NotImplemented
                case 'int' | 'float' | 'bool':
                    a = float(other) ; b = self.nxsock
                    sockfunc = nodesetter.floordiv
                case _:
                    raise NexError(f"SocketTypeError. Cannot perform floor division of '{type(other).__name__}' by 'SocketFloat'.")
            tag = generate_tag(NexFloat, sockfunc, self, other,)
            return call_Nex_operand(NexFloat, sockfunc, a, b, uniquetag=tag)

        # ---------------------
        # NexFloat Negate

        def __neg__(self): # -self
            sockfunc = nodesetter.neg
            tag = generate_tag(NexFloat, sockfunc, self,)
            return call_Nex_operand(NexFloat, sockfunc, self.nxsock, uniquetag=tag)

        # ---------------------
        # NexFloat Absolute

        def __abs__(self): # abs(self)
            sockfunc = nodesetter.abs
            tag = generate_tag(NexFloat, sockfunc, self,)
            return call_Nex_operand(NexFloat, sockfunc, self.nxsock, uniquetag=tag)

    # ooooo      ooo                       oooooo     oooo                     
    # `888b.     `8'                        `888.     .8'                      
    #  8 `88b.    8   .ooooo.  oooo    ooo   `888.   .8'    .ooooo.   .ooooo.  
    #  8   `88b.  8  d88' `88b  `88b..8P'     `888. .8'    d88' `88b d88' `"Y8 
    #  8     `88b.8  888ooo888    Y888'        `888.8'     888ooo888 888       
    #  8       `888  888    .o  .o8"'88b        `888'      888    .o 888   .o8 
    # o8o        `8  `Y8bod8P' o88'   888o       `8'       `Y8bod8P' `Y8bod8P' 
                                                                            
    class NexVec(Nex):
        
        _instance_counter = 0
        node_inst = factor_customnode_instance
        node_tree = node_inst.node_tree
        nxstype = 'NodeSocketVector'
        nxchar = 'v'

        def __init__(self, varname='', value=None, fromsocket=None, manualdef=False):

            self.nxid = NexVec._instance_counter
            NexVec._instance_counter += 1

            if (manualdef):
                return None

            if (fromsocket is not None):
                self.nxsock, self.nxvname = fromsocket, 'AnonymousVariable'
                return None

            type_name = type(value).__name__
            match type_name: 

                case _ if ('Nex' in type_name):
                    raise NexError(f"Invalid use of Inputs. Cannot assign 'SocketInput' to 'SocketInput'.")
                case 'NexOutput':
                    raise NexError(f"Invalid use of Outputs. Cannot assign 'SocketOutput' to 'SocketInput'.")

                case 'Vector' | 'list' | 'set' | 'tuple' | 'int' | 'float' | 'bool':
                    assert varname!='', "Nex Initialization should always define a varname."
                    outsock = get_socket(self.node_tree, in_out='INPUT', socket_name=varname,)
                    assert outsock is not None, f"The socket '{varname}' do not exist in your node inputs."
                    fval = py_to_Vec3(value)
                    set_socket_defvalue(self.node_tree, socket=outsock, node=self.node_inst, value=fval, in_out='INPUT')
                    self.nxsock, self.nxvname = outsock, varname

                case _:
                    raise NexError(f"SocketTypeError. Cannot assign var '{varname}' of type '{type(value).__name__}' to 'SocketVector'.")

            print(f'DEBUG: {type(self).__name__}.__init__({value}). Instance:',self)
            return None

        # ---------------------
        # NexVec Additions

        def __add__(self, other): # self + other
            type_name = type(other).__name__
            match type_name:
                case 'NexVec' | 'NexFloat':
                    a = self.nxsock ; b = other.nxsock
                    sockfunc = nodesetter.add
                case 'Vector' | 'list' | 'set' | 'tuple' | 'int' | 'float' | 'bool':
                    a = self.nxsock ; b = py_to_Vec3(other)
                    sockfunc = nodesetter.add
                case _:
                    raise NexError(f"SocketTypeError. Cannot add '{self.nxvname}' of type 'SocketVector' to '{type(other).__name__}'.")
            tag = generate_tag(NexVec, sockfunc, self, other,)
            return call_Nex_operand(NexVec, sockfunc, a, b, uniquetag=tag)

        def __radd__(self, other): # other + self
            # Multiplication is commutative.
            return self.__add__(other)

        # ---------------------
        # NexVec Subtraction

        def __sub__(self, other): # self - other
            type_name = type(other).__name__
            match type_name:
                case 'NexVec' | 'NexFloat':
                    a = self.nxsock ; b = other.nxsock
                    sockfunc = nodesetter.sub
                case 'Vector' | 'list' | 'set' | 'tuple' | 'int' | 'float' | 'bool':
                    a = self.nxsock ; b = py_to_Vec3(other)
                    sockfunc = nodesetter.sub
                case _:
                    raise NexError(f"SocketTypeError. Cannot subtract '{self.nxvname}' of type 'SocketVector' with '{type(other).__name__}'.")
            tag = generate_tag(NexVec, sockfunc, self, other,)
            return call_Nex_operand(NexVec, sockfunc, a, b, uniquetag=tag)

        def __rsub__(self, other): # other - self
            type_name = type(other).__name__
            match type_name:
                case 'NexFloat':
                    a = other.nxsock ; b = self.nxsock
                    sockfunc = nodesetter.sub
                case 'Vector' | 'list' | 'set' | 'tuple' | 'int' | 'float' | 'bool':
                    a = py_to_Vec3(other) ; b = self.nxsock
                    sockfunc = nodesetter.sub
                case _:
                    raise NexError(f"SocketTypeError. Cannot subtract '{type(other).__name__}' with 'SocketVector'.")
            tag = generate_tag(NexVec, sockfunc, self, other,)
            return call_Nex_operand(NexVec, sockfunc, a, b, uniquetag=tag)

        # ---------------------
        # NexVec Multiplication

        def __mul__(self, other): # self * other
            type_name = type(other).__name__
            match type_name:
                case 'NexVec' | 'NexFloat':
                    a = self.nxsock ; b = other.nxsock
                    sockfunc = nodesetter.mult
                case 'Vector' | 'list' | 'set' | 'tuple' | 'int' | 'float' | 'bool':
                    a = self.nxsock ; b = py_to_Vec3(other)
                    sockfunc = nodesetter.mult
                case _:
                    raise NexError(f"SocketTypeError. Cannot multiply '{self.nxvname}' of type 'SocketVector' with '{type(other).__name__}'.")
            tag = generate_tag(NexVec, sockfunc, self, other,)
            return call_Nex_operand(NexVec, sockfunc, a, b, uniquetag=tag)

        def __rmul__(self, other): # other * self
            # Multiplication is commutative.
            return self.__mul__(other)

        # ---------------------
        # NexVec True Division

        def __truediv__(self, other): # self / other
            type_name = type(other).__name__
            match type_name:
                case 'NexVec' | 'NexFloat':
                    a = self.nxsock ; b = other.nxsock
                    sockfunc = nodesetter.div
                case 'Vector' | 'list' | 'set' | 'tuple' | 'int' | 'float' | 'bool':
                    a = self.nxsock ; b = py_to_Vec3(other)
                    sockfunc = nodesetter.div
                case _:
                    raise NexError(f"SocketTypeError. Cannot divide '{self.nxvname}' of type 'SocketVector' by '{type(other).__name__}'.")
            tag = generate_tag(NexVec, sockfunc, self, other,)
            return call_Nex_operand(NexVec, sockfunc, a, b, uniquetag=tag)

        def __rtruediv__(self, other): # other / self
            type_name = type(other).__name__
            match type_name:
                case 'NexFloat':
                    a = other.nxsock ; b = self.nxsock
                    sockfunc = nodesetter.div
                case 'Vector' | 'list' | 'set' | 'tuple' | 'int' | 'float' | 'bool':
                    a = py_to_Vec3(other) ; b = self.nxsock
                    sockfunc = nodesetter.div
                case _:
                    raise NexError(f"SocketTypeError. Cannot divide '{type(other).__name__}' by 'SocketVector'.")
            tag = generate_tag(NexVec, sockfunc, self, other,)
            return call_Nex_operand(NexVec, sockfunc, a, b, uniquetag=tag)

        # ---------------------
        # NexVec Power

        def __pow__(self, other): #self ** other
            raise NexError(f"SocketTypeError. Cannot raise a 'SocketVector'.") #TODO add a function for that in nodesetter. not comprised in vector math node of blender..

        def __rpow__(self, other): #other ** self
            raise NexError(f"SocketTypeError. Cannot raise a 'SocketVector'.") #TODO add a function for that in nodesetter. not comprised in vector math node of blender..

        # ---------------------
        # NexVec Modulo

        def __mod__(self, other): # self % other
            type_name = type(other).__name__
            match type_name:
                case 'NexVec' | 'NexFloat':
                    a = self.nxsock ; b = other.nxsock
                    sockfunc = nodesetter.mod
                case 'Vector' | 'list' | 'set' | 'tuple' | 'int' | 'float' | 'bool':
                    a = self.nxsock ; b = py_to_Vec3(other)
                    sockfunc = nodesetter.mod
                case _:
                    raise NexError(f"SocketTypeError. Cannot compute '{self.nxvname}' of type 'SocketVector' modulo '{type(other).__name__}'.")
            tag = generate_tag(NexVec, sockfunc, self, other,)
            return call_Nex_operand(NexVec, sockfunc, a, b, uniquetag=tag)

        def __rmod__(self, other): # other % self
            type_name = type(other).__name__
            match type_name:
                case 'NexFloat':
                    a = other.nxsock ; b = self.nxsock
                    sockfunc = nodesetter.mod
                case 'Vector' | 'list' | 'set' | 'tuple' | 'int' | 'float' | 'bool':
                    a = py_to_Vec3(other) ; b = self.nxsock
                    sockfunc = nodesetter.mod
                case _:
                    raise NexError(f"SocketTypeError. Cannot compute modulo of '{type(other).__name__}' by 'SocketVector'.")
            tag = generate_tag(NexVec, sockfunc, self, other,)
            return call_Nex_operand(NexVec, sockfunc, a, b, uniquetag=tag)

        # ---------------------
        # NexVec Floor Division

        def __floordiv__(self, other): # self // other
            type_name = type(other).__name__
            match type_name:
                case 'NexVec' | 'NexFloat':
                    a = self.nxsock ; b = other.nxsock
                    sockfunc = nodesetter.floordiv
                case 'Vector' | 'list' | 'set' | 'tuple' | 'int' | 'float' | 'bool':
                    a = self.nxsock ; b = py_to_Vec3(other)
                    sockfunc = nodesetter.floordiv
                case _:
                    raise NexError(f"SocketTypeError. Cannot perform floor division on '{self.nxvname}' of type 'SocketVector' with '{type(other).__name__}'.")
            tag = generate_tag(NexVec, sockfunc, self, other,)
            return call_Nex_operand(NexVec, sockfunc, a, b, uniquetag=tag)

        def __rfloordiv__(self, other): # other // self
            type_name = type(other).__name__
            match type_name:
                case 'NexFloat':
                    a = other.nxsock ; b = self.nxsock
                    sockfunc = nodesetter.floordiv
                case 'Vector' | 'list' | 'set' | 'tuple' | 'int' | 'float' | 'bool':
                    a = py_to_Vec3(other) ; b = self.nxsock
                    sockfunc = nodesetter.floordiv
                case _:
                    raise NexError(f"SocketTypeError. Cannot perform floor division of '{type(other).__name__}' by 'SocketVector'.")
            tag = generate_tag(NexVec, sockfunc, self, other,)
            return call_Nex_operand(NexVec, sockfunc, a, b, uniquetag=tag)

        # ---------------------
        # NexVec Negate

        def __neg__(self): # -self
            sockfunc = nodesetter.neg
            tag = generate_tag(NexVec, sockfunc, self,)
            return call_Nex_operand(NexVec, sockfunc, self.nxsock, uniquetag=tag)

        # ---------------------
        # NexVec Absolute

        def __abs__(self): # abs(self)
            sockfunc = nodesetter.abs
            tag = generate_tag(NexVec, sockfunc, self,)
            return call_Nex_operand(NexVec, sockfunc, self.nxsock, uniquetag=tag)

        # ---------------------
        # NexVec Itter

        #NOTE would be also nice to have NexVec.x .y .z maybe? hmm..

        def __len__(self):
            return 3

        def __iter__(self):
            for i in range(3):
                yield self[i]

        def __getitem__(self, key):
            sockfunc = nodesetter.separate_xyz
            tag = generate_tag(NexVec, sockfunc, self,)
            outs = call_Nex_operand(NexVec, sockfunc, self.nxsock, uniquetag=tag, NexTypeReturnSpecial=NexFloat,)

            #vec[i]
            if isinstance(key, int):
                if key not in (0,1,2):
                    raise NexError("IndexError. indice in VectorSocket[i] exceeded maximal range of 2.")
                return outs[key]

            #vec[:i]
            elif isinstance(key, slice):
                indices = range(*key.indices(3))
                return tuple(outs[i] for i in indices)
            else:
                raise NexError("TypeError. indices in VectorSocket[i] must be integers or slices.")
    
    # ooooo      ooo                         .oooooo.                   .   
    # `888b.     `8'                        d8P'  `Y8b                .o8   
    #  8 `88b.    8   .ooooo.  oooo    ooo 888      888 oooo  oooo  .o888oo 
    #  8   `88b.  8  d88' `88b  `88b..8P'  888      888 `888  `888    888   
    #  8     `88b.8  888ooo888    Y888'    888      888  888   888    888   
    #  8       `888  888    .o  .o8"'88b   `88b    d88'  888   888    888 . 
    # o8o        `8  `Y8bod8P' o88'   888o  `Y8bood8P'   `V88V"V8P'   "888" 
                                                                        
    class NexOutput(Nex):
        """A nex output is just a simple linking operation. We only assign to an output.
        After assinging the final output not a lot of other operations are possible"""

        _instance_counter = 0
        node_inst = factor_customnode_instance
        node_tree = node_inst.node_tree
        nxstype = factory_outsocktype
        nxchar = 'o'

        outsubtype = nxstype.replace("Node","")

        def __init__(self, varname='', value=0.0):

            assert varname!='', "NexOutput Initialization should always define a varname"
            self.nxvname = varname

            # create a stable identifier for our NexObject
            self.nxid = NexOutput._instance_counter
            NexOutput._instance_counter += 1

            # add a socket to this object
            outsock = get_socket(self.node_tree, in_out='OUTPUT', socket_name=varname,)
            self.nxsock = outsock

            type_name = type(value).__name__
            match type_name:

                # is user toying with  output? output cannot be reused in any way..
                case 'NexOutput':
                    raise NexError(f"Invalid use of Outputs. Cannot assign 'SocketOutput' to 'SocketOutput'.")

                # we link another nextype
                case _ if ('Nex' in type_name):
                    l = link_sockets(value.nxsock, outsock)
                    # we might need to send a refresh signal before checking is_valid property?? if it works, it works
                    if (not l.is_valid):
                        raise NexError(f"SocketTypeError. Cannot assign var '{varname}' of type '{type(value).__name__}' to output socket of type '{self.outsubtype}'.")

                # or we simply output a default python constant value
                case _:
                    newval, _, socktype = convert_pyvar_to_data(value)
                    # just do a try except to see if the var assignment to python is working.. easier.
                    try:
                        set_socket_defvalue(self.node_tree, value=newval, socket=outsock, in_out='OUTPUT',)
                    except Exception as e:
                        raise NexError(f"SocketTypeError. Cannot assign var '{varname}' of type '{type(value).__name__}' to output socket of type '{self.outsubtype}'.")


    # return the class
    ReturnClass = locals().get(factory_classname)
    if (ReturnClass is None):
        raise Exception(f"Type '{factory_classname}' not supported")

    return ReturnClass