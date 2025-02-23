# SPDX-FileCopyrightText: 2025 BD3D DIGITAL DESIGN
#
# SPDX-License-Identifier: GPL-2.0-or-later


import bpy 

from collections.abc import Iterable

from .__init__ import get_addon_prefs
from .customnodes import NODEBOOSTER_NG_camerainfo, NODEBOOSTER_NG_pythonapi, NODEBOOSTER_NG_sequencervolume, NODEBOOSTER_NG_isrenderedview


# We start with msgbusses


MSGBUSOWNER_VIEWPORT_SHADING = object()


def msgbus_viewportshading_callback(*args):
    
    sett_plugin = get_addon_prefs()
    
    if (sett_plugin.debug_depsgraph):
        print("msgbus_viewportshading_callback(): msgbus signal")

    NODEBOOSTER_NG_isrenderedview.update_all()

    return None 


def register_msgbusses():
    
    bpy.msgbus.subscribe_rna(
        key=(bpy.types.View3DShading, "type"),
        owner=MSGBUSOWNER_VIEWPORT_SHADING,
        notify=msgbus_viewportshading_callback,
        args=(None,),
        options={"PERSISTENT"},
        )

    return None


def unregister_msgbusses():
    
    bpy.msgbus.clear_by_owner(MSGBUSOWNER_VIEWPORT_SHADING)
    
    return None


# Then we register the handlers


@bpy.app.handlers.persistent
def nodebooster_handler_depspost(scene,desp):
    """update on depsgraph change"""
    
    sett_plugin = get_addon_prefs()
    
    if (sett_plugin.debug_depsgraph):
        print("nodebooster_handler_depspost(): depsgraph signal")

    #automatic update for Python Api Node?
    if (sett_plugin.pynode_depseval):
        NODEBOOSTER_NG_pythonapi.update_all()
            
    #need to update camera nodes outputs
    NODEBOOSTER_NG_camerainfo.update_all()

    return None


@bpy.app.handlers.persistent
def nodebooster_handler_framepre(scene,desp):
    """update on frame change"""
    
    sett_plugin = get_addon_prefs()

    if (sett_plugin.debug_depsgraph):
        print("nodebooster_handler_framepre(): frame_pre signal")

    #automatic update for Python Api Node?
    if (sett_plugin.pynode_depseval):
        NODEBOOSTER_NG_pythonapi.update_all()

    #need to update camera nodes outputs
    NODEBOOSTER_NG_camerainfo.update_all()
    
    #need to update all volume sequencer nodes output value
    NODEBOOSTER_NG_sequencervolume.update_all()

    return None


@bpy.app.handlers.persistent
def nodebooster_handler_loadpost(scene,desp):
    """Handler function when user is loading a file"""
    
    sett_plugin = get_addon_prefs()
    
    if (sett_plugin.debug_depsgraph):
        print("nodebooster_handler_framepre(): frame_pre signal")

    #need to add message bus on each blender load
    register_msgbusses()

    return None


# Registering the handlers


def all_handlers(name=False):
    """return a list of handler stored in .blend""" 

    for oh in bpy.app.handlers:
        if isinstance(oh, Iterable):
            for h in oh:
                yield h


def load_handlers():
    
    handler_names = [h.__name__ for h in all_handlers()]

    if ('nodebooster_handler_depspost' not in handler_names):
        bpy.app.handlers.depsgraph_update_post.append(nodebooster_handler_depspost)

    if ('nodebooster_handler_framepre' not in handler_names):
        bpy.app.handlers.frame_change_pre.append(nodebooster_handler_framepre)

    if ('nodebooster_handler_loadpost' not in handler_names):
        bpy.app.handlers.load_post.append(nodebooster_handler_loadpost)
        
    return None 


def unload_handlers():

    for h in all_handlers():

        if(h.__name__=='nodebooster_handler_depspost'):
            bpy.app.handlers.depsgraph_update_post.remove(h)

        if(h.__name__=='nodebooster_handler_framepre'):
            bpy.app.handlers.frame_change_pre.remove(h)

        if(h.__name__=='nodebooster_handler_loadpost'):
            bpy.app.handlers.load_post.remove(h)

    return None
