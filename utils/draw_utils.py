# SPDX-FileCopyrightText: 2025 BD3D DIGITAL DESIGN
#
# SPDX-License-Identifier: GPL-2.0-or-later


import bpy 


def get_dpifac():
    """get user dpi"""
    prefs = bpy.context.preferences.system
    return prefs.dpi * prefs.pixel_size / 72


def ensure_mouse_cursor(context, event):
    """function needed to get cursor location"""

    space = context.space_data
    tree = space.edit_tree

    # convert mouse position to the View2D
    if (context.region.type == 'WINDOW'):
          space.cursor_location_from_region(event.mouse_region_x, event.mouse_region_y)
    else: space.cursor_location = tree.view_center

    return None


def popup_menu(msgs, title, icon):
    """pop a menu message for the user"""

    def draw(self, context):
        layout = self.layout
        for msg in msgs:
            layout.label(text=msg)
        return  

    bpy.context.window_manager.popup_menu(draw, title=title, icon=icon)
    return None 
