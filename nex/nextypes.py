# SPDX-FileCopyrightText: 2025 BD3D DIGITAL DESIGN (Dorian B.)
#
# SPDX-License-Identifier: GPL-2.0-or-later


import bpy

from ..nex.pytonode import convert_pyvar_to_data
from ..utils.node_utils import (
    create_new_nodegroup,
    set_socket_defvalue,
    get_socket_type,
    set_socket_type,
    create_socket,
    get_socket_from_socketui,
    remove_socket,
    set_socket_label,
    link_sockets,
)


class NexError(Exception):
    def __init__(self, message):
        super().__init__(message)

class Nex:
    """parent class of all Nex subclasses"""

    node_inst = None
    node_tree = None
    _typeid = ''
    _userid = ''

    def __init__(*args, **kwargs):
        _skitm = None
        _varname = None

    def initialize_var_name(self):
        print("---")
        print(globals().keys())
        print(locals().keys())
        for k, v in globals().items():
            if v is self:
                self._varname = k
                break

    def __repr__(self):
        return f"<Var '{self._varname}' of type {type(self)} = `{self._skitm}` output={self._skitm.is_output}'\
            from node `{self._skitm.node.name}|{self._skitm.node.label}` of type {self._typeid}"



def NexFactory(customnode_instance, gen_classname:str, gen_socket_type:str='', build_tree:bool=False,):
    """return a nex type, which is simply an overloaded type that automatically arrange links sokets together
    enable `build_tree` if you wish to only update constants of the node_tree and not rebuild it!"""

    #TODO implement build_tree...
    
    class NexFloat(Nex):
        
        node_inst = customnode_instance
        node_tree = node_inst.node_tree
        _typeid = 'NodeSocketFloat'
        _userid = _typeid.replace("NodeSocket","")

        def __init__(self, varname='', value=0.0,):

            self._varname = varname

            match value:

                # copy of one self?
                case NexFloat():
                    #Unsure what that means yet..
                    print("is copy?:", value)
                    #PROBLEM we won't get var name from here. idk we need it tho
                    print(value)
                    nxob = value
                    self._skitm = nxob._skitm

                # initial creation by assignation, we need to create a socket type
                case int() | float() | bool():
                    value = float(value)
                    outsock = create_socket(self.node_tree, in_out='INPUT', socket_type=self._typeid, socket_name=varname,)
                    outsock = get_socket_from_socketui(self.node_tree, outsock, in_out='INPUT')
                    set_socket_defvalue(self.node_tree, socket=outsock, node=self.node_inst, value=value, in_out='INPUT')
                    self._skitm = outsock

                # wrong initialization?
                case _:
                    if issubclass(type(value), Nex):
                        raise NexError(f"'{varname}' invalid type assignation.\nCannot assign '{value._userid}' to '{self._userid}'")
                    raise NexError(f"'{varname}' invalid type assignation.\nCannot assign '{type(value)}' to '{self._userid}'")

        def __add__(self, other):
            
            # if isinstance(other, NexFloat):
            #     #we add a node, link it!
            #     return NexFloat(value + other.value + 1.0)

            # elif isinstance(other, (int, float)):
            #     return NexFloat(value + other)

            return NotImplemented

        def __radd__(self, other):
            """right add is the same as left, no order of operation here"""

            return self.__add__(other)


    class NexOutput(Nex):
        """A nex output is just a simple linking operation. We only assign to an output.
        After assinging the final output not a lot of other operations are possible"""

        node_inst = customnode_instance
        node_tree = node_inst.node_tree
        _typeid = gen_socket_type
        _userid = _typeid.replace("NodeSocket","")

        def __init__(self, varname='', value=0.0):

            self._varname = varname
            
            outsock = create_socket(self.node_tree, in_out='OUTPUT', socket_type=self._typeid, socket_name=varname,)
            outsock = get_socket_from_socketui(self.node_tree, outsock, in_out='OUTPUT')
                
            # we link another nextype
            if issubclass(type(value), Nex):
                nxob = value
                l = link_sockets(nxob._skitm, outsock)
                # we might need to send a refresh signal before checking is_valid property?? if it works, it works
                if (not l.is_valid):
                    raise NexError(f"'{varname}' invalid type assignation.\nCannot assign '{nxob._userid}' to '{self._userid}'")

            # or we simply output a default python constant value
            else:
                value, _, socktype = convert_pyvar_to_data(value)
                try:
                    set_socket_defvalue(self.node_tree, value=value, socket=outsock, in_out='OUTPUT',)
                except Exception as e:
                    print(f"NexOutput set_socket_defvalue() Errror:\n{type(e).__name__}\n{e}")
                    raise NexError(f"'{varname}' invalid type assignation.\nCannot assign '{socktype}' to '{self._userid}'")

    # return the class
    ReturnClass = locals().get(gen_classname)
    if (ReturnClass is None):
        raise Exception(f"Type '{gen_classname}' not supported")

    return ReturnClass