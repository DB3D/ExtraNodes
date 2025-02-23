# SPDX-FileCopyrightText: 2025 BD3D DIGITAL DESIGN
#
# SPDX-License-Identifier: GPL-2.0-or-later


import bpy 

from collections.abc import Iterable

from .__init__ import get_addon_prefs
from .customnodes import NODEBOOSTER_NG_camerainfo, NODEBOOSTER_NG_pythonapi, NODEBOOSTER_NG_sequencervolume
from .utils.node_utils import set_socket_defvalue


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


def all_3d_viewports():
    """return generator of all 3d view space"""

    for window in bpy.context.window_manager.windows:
        for area in window.screen.areas:
            if (area.type == 'VIEW_3D'):
                for space in area.spaces:
                    if (space.type == 'VIEW_3D'):
                        yield space


def all_3d_viewports_shading_type():
    """return generator of all shading type str"""

    for space in all_3d_viewports():
        yield space.shading.type


def is_rendered_view():
    """check if is rendered view in a 3d view somewhere"""

    return 'RENDERED' in all_3d_viewports_shading_type()


VIEWPORTSHADING_OWNER = object()


def msgbus_viewportshading_callback(*args):
    
    sett_plugin = get_addon_prefs()
    
    if (sett_plugin.debug_depsgraph):
        print("msgbus_viewportshading_callback(): msgbus signal")

    ng = bpy.data.node_groups.get(".GeometryNodeExtraNodesIsRenderedView")
    if (ng):
        set_socket_defvalue(ng, 0, value=is_rendered_view(),)

    return None 


def all_handlers(name=False):
    """return a list of handler stored in .blend""" 

    for oh in bpy.app.handlers:
        if isinstance(oh, Iterable):
            for h in oh:
                yield h


def register_handlers_and_msgbus():
    
    all_handler_names = [h.__name__ for h in all_handlers()]

    if ('nodebooster_handler_depspost' not in all_handler_names):
        bpy.app.handlers.depsgraph_update_post.append(nodebooster_handler_depspost)

    if ('nodebooster_handler_framepre' not in all_handler_names):
        bpy.app.handlers.frame_change_pre.append(nodebooster_handler_framepre)

    #add msgbus
    bpy.msgbus.subscribe_rna(
        key=(bpy.types.View3DShading, "type"),
        owner=VIEWPORTSHADING_OWNER,
        notify=msgbus_viewportshading_callback,
        args=(None,),
        options={"PERSISTENT"},
        )
        
    return None 


def unregister_handlers_and_msgbus():

    for h in all_handlers():

        if(h.__name__=='nodebooster_handler_depspost'):
            bpy.app.handlers.depsgraph_update_post.remove(h)

        if(h.__name__=='nodebooster_handler_framepre'):
            bpy.app.handlers.frame_change_pre.remove(h)
    
    #remove msgbus
    bpy.msgbus.clear_by_owner(VIEWPORTSHADING_OWNER)
    
    return None
