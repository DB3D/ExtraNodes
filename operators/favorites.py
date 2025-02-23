# SPDX-FileCopyrightText: 2025 BD3D DIGITAL DESIGN
#
# SPDX-License-Identifier: GPL-2.0-or-later

# NOTE ideally, active favorite should be set on a prop per nodegroup and not per scene.


import bpy

from ..utils.draw_utils import ensure_mouse_cursor, popup_menu


FAVORITEUNICODE = "★" #\u2605


def get_favorites(nodes, at_index=None,):

    favs = []

    for n in nodes:
        if n.name.startswith(FAVORITEUNICODE):
            favs.append(n)
        continue

    favs.sort(key=lambda e:e.name)

    if (at_index is not None):
        for i,n in enumerate(favs):
            if (i==at_index):
                return n
        return None 

    return favs


class NODEBOOSTER_OT_favorite_add(bpy.types.Operator):

    bl_idname      = "nodebooster.favorite_add"
    bl_label       = "Add New Favorites Reroute"
    bl_description = "Add New Favorites Reroute"

    def invoke(self, context, event):

        ng = context.space_data.edit_tree

        idx = 1
        name = f"{FAVORITEUNICODE}{idx:02}"
        while name in [n.name for n in ng.nodes]:
            idx +=1
            name = f"{FAVORITEUNICODE}{idx:02}"

        if (idx>50):
            popup_menu([f"You reached {idx-1} favorites.","That's too many!.",],"Max Favorites!","ORPHAN_DATA")
            return {"FINISHED"}

        sh = ng.nodes.new("NodeReroute")
        sh.name = sh.label = name
        ensure_mouse_cursor(context, event)
        sh.location = context.space_data.cursor_location

        self.report({'INFO'}, f"Added Favorite '{sh.label}'",)

        return {"FINISHED"}


class NODEBOOSTER_OT_favorite_loop(bpy.types.Operator):

    bl_idname      = "nodebooster.favorite_loop"
    bl_label       = "Loop Over Your Favorites"
    bl_description = "Loop Over Your Favorites"

    def execute(self, context):

        ng = context.space_data.edit_tree
        sett_scene = context.scene.nodebooster

        favs = get_favorites(ng.nodes)
        favs_len = len(favs)

        if (favs_len==0):
            self.report({'INFO'}, "No Favorites Found")
            return {"FINISHED"}

        #rest to 0 if reach the end
        if (sett_scene.favorite_index>=(favs_len-1)):
              sett_scene.favorite_index = 0
        else: sett_scene.favorite_index += 1

        reroute = get_favorites(ng.nodes, at_index=sett_scene.favorite_index)
        
        for n in ng.nodes:
            n.select = False
        reroute.select = True 
        ng.nodes.active = reroute

        bpy.ops.node.view_selected()
    
        self.report({'INFO'}, f"Looping to Favorite '{reroute.label}'")

        return {"FINISHED"}