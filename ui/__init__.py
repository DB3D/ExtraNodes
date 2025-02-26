# SPDX-FileCopyrightText: 2025 BD3D DIGITAL DESIGN (Dorian B.)
#
# SPDX-License-Identifier: GPL-2.0-or-later


from .menus import (

    NODEBOOSTER_MT_addmenu_general,
    append_menus, 
    remove_menus,

    )

from .panels import (

    NODEBOOSTER_PT_tool_search,
    NODEBOOSTER_PT_tool_color_palette,
    NODEBOOSTER_PT_tool_frame,
    NODEBOOSTER_PT_shortcuts_memo,
    NODEBOOSTER_PT_active_node,

    )


classes = (

    NODEBOOSTER_MT_addmenu_general,
    NODEBOOSTER_PT_tool_search,
    NODEBOOSTER_PT_tool_color_palette,
    NODEBOOSTER_PT_shortcuts_memo,
    NODEBOOSTER_PT_tool_frame,
    NODEBOOSTER_PT_active_node,

    )


def load_ui():

    append_menus()

    return None


def unload_ui():

    remove_menus()

    return None
