# SPDX-FileCopyrightText: 2025 BD3D DIGITAL DESIGN, SLU
#
# SPDX-License-Identifier: GPL-2.0-or-later


import bpy, sys
from . import addonprefs, handlers, geometrycustomnodes, menus


def get_addon_prefs():
    """get preferences path from base_package, __package__ path change from submodules"""
    return bpy.context.preferences.addons[__package__].preferences


def cleanse_modules():
    """remove all plugin modules from sys.modules for a clean uninstall"""
    #https://devtalk.blender.org/t/plugin-hot-reload-by-cleaning-sys-modules/20040
    
    all_modules = sys.modules
    all_modules = dict(sorted(all_modules.items(),key= lambda x:x[0])) #sort them
    
    for k,v in all_modules.items():
        if k.startswith(__package__):
            del sys.modules[k]

    return None


classes = []
classes += addonprefs.classes
classes += geometrycustomnodes.classes
classes += menus.classes


def register():
    """main addon register"""

    for cls in classes:
        bpy.utils.register_class(cls)
    
    handlers.register_handlers_and_msgbus()
    menus.append_menus()
    
    return None


def unregister():
    """main addon un-register"""

    menus.remove_menus()
    handlers.unregister_handlers_and_msgbus()
    
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
    
    cleanse_modules()
    
    return None
