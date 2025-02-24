# SPDX-FileCopyrightText: 2025 BD3D DIGITAL DESIGN
#
# SPDX-License-Identifier: GPL-2.0-or-later


import bpy 

from bl_ui.properties_paint_common import BrushPanel

from ..utils.str_utils import word_wrap
from ..operators import ADDON_KEYMAPS


class NODEBOOSTER_PT_tool_search(bpy.types.Panel):
    """search element within your node_tree"""

    bl_idname = "NODEBOOSTER_PT_tool_search"
    bl_label = "Node Search"
    bl_category = "Node Booster"
    bl_space_type = "NODE_EDITOR"
    bl_region_type = "UI"
    bl_order = 0

    @classmethod
    def poll(cls, context):
        return (context.space_data.type=='NODE_EDITOR') and (context.space_data.node_tree is not None)

    def draw(self, context):

        sett_scene = context.scene.nodebooster

        layout = self.layout
        layout.use_property_split = True
        layout.use_property_decorate = False

        row = layout.row(align=True)
        row.prop(sett_scene,"search_keywords",text="",icon="VIEWZOOM")
        row.prop(sett_scene,"search_center",text="",icon="ZOOM_ALL")

        col = layout.column(heading="Filters")
        col.prop(sett_scene,"search_labels")
        # col.prop(sett_scene,"search_types") #TODO For later. Ideally they should be type enum
        col.prop(sett_scene,"search_socket_names") #TODO Ideally we should have an option to either check sockets or ng info.
        # col.prop(sett_scene,"search_socket_types") #TODO For later. Ideally they should be type enum
        col.prop(sett_scene,"search_names")
        col.prop(sett_scene,"search_input_only")
        col.prop(sett_scene,"search_frame_only")

        s = layout.column()
        s.label(text=f"Found {sett_scene.search_found} Element(s)")
    
        return None


class NODEBOOSTER_PT_tool_color_palette(bpy.types.Panel,BrushPanel):
    #palette api is a bit bad, it is operatiors designed for unified paint tools
    #so we are hijacking the context for us then.

    bl_idname = "NODEBOOSTER_PT_tool_color_palette"
    bl_label = "Assign Color"
    bl_category = "Node Booster"
    bl_space_type = "NODE_EDITOR"
    bl_region_type = "UI"
    bl_order = 1

    @classmethod
    def poll(cls, context):
        return (context.space_data.type=='NODE_EDITOR') and (context.space_data.node_tree is not None)

    def draw(self, context):

        layout = self.layout

        sett_scene = context.scene.nodebooster
        ts = context.tool_settings
        tsi = ts.image_paint

        if (not tsi.palette):
            layout.operator("nodebooster.initalize_palette",text="Create Palette",icon="ADD",)
            return None

        row = layout.row(align=True)

        colo = row.row(align=True)
        colo.prop(sett_scene,"palette_older",text="")
        colo.prop(sett_scene,"palette_old",text="")
        colo.prop(sett_scene,"palette_active",text="")

        row.operator("nodebooster.palette_reset_color",text="",icon="LOOP_BACK",)

        layout.template_palette(tsi, "palette", color=True,)

        return None 


class NODEBOOSTER_PT_tool_frame(bpy.types.Panel):

    bl_idname = "NODEBOOSTER_PT_tool_frame"
    bl_label = "Draw Frame"
    bl_category = "Node Booster"
    bl_space_type = "NODE_EDITOR"
    bl_region_type = "UI"
    bl_order = 3

    @classmethod
    def poll(cls, context):
        return (context.space_data.type=='NODE_EDITOR') and (context.space_data.node_tree is not None)

    def draw(self, context):

        sett_scene = context.scene.nodebooster

        layout = self.layout
        layout.use_property_split = True
        layout.use_property_decorate = False

        col = layout.column()
        col.prop(sett_scene,"frame_label")
        col.prop(sett_scene,"frame_label_size")
        col.prop(sett_scene,"frame_use_custom_color")

        col = col.column()
        col.prop(sett_scene,"frame_sync_color")
        col.separator(factor=0.25)
        col.active = sett_scene.frame_use_custom_color
        col.prop(sett_scene,"frame_color")

        return None


class NODEBOOSTER_PT_shortcuts_memo(bpy.types.Panel):

    bl_idname = "NODEBOOSTER_PT_shortcuts_memo"
    bl_label = "Shortcuts"
    bl_category = "Node Booster"
    bl_space_type = "NODE_EDITOR"
    bl_region_type = "UI"
    bl_order = 2

    @classmethod
    def poll(cls, context):
        return (context.space_data.type=='NODE_EDITOR') and (context.space_data.node_tree is not None)

    def draw(self, context):

        layout = self.layout

        for i, (km, kmi, name, icon) in enumerate(ADDON_KEYMAPS):
            
            if (i!=0):
                layout.separator(type='LINE')

            col = layout.box()

            titlename = name.replace('Select','Sel.')
            mainrow = col.row(align=True)
            row = mainrow.row(align=True)
            row.alignment = 'LEFT'
            row.prop(kmi, "active", text=titlename,emboss=False,)
            row = mainrow.row(align=True)
            row.alignment = 'RIGHT'
            row.label(text='',icon=icon)

            col = col.column()
            col.active = kmi.active

            header, panel = col.panel(f'geobuilder_shortcut_layoutpanel_defaults_{i}', default_closed=False,)
            header.label(text="Default Shortcut",)
            if (panel):
                panel.separator(factor=0.5)
                row = panel.row(align=True)
                row.separator(factor=0.5)

                match name:
                    case "Add Favorite":
                        row.label(text='', icon='EVENT_CTRL',)
                        row.separator(factor=2.35)
                        row.label(text='', icon='EVENT_Y',)

                    case "Loop Favorites":
                        row.label(text='', icon='EVENT_Y',)

                    case "Select Downstream":
                        row.label(text='', icon='EVENT_CTRL',)
                        row.separator(factor=2.35)
                        row.label(text='', icon='MOUSE_LMB',)

                    case "Select Downstream (Add)":
                        row.label(text='', icon='EVENT_SHIFT',)
                        row.separator(factor=0.9)
                        row.label(text='', icon='EVENT_CTRL',)
                        row.separator(factor=2.35)
                        row.label(text='', icon='MOUSE_LMB',)

                    case "Select Upsteam":
                        row.label(text='', icon='EVENT_CTRL',)
                        row.separator(factor=2.35)
                        row.label(text='', icon='EVENT_ALT',)
                        row.separator(factor=2.35)
                        row.label(text='', icon='MOUSE_LMB',)

                    case "Select Upsteam (Add)":
                        row.label(text='', icon='EVENT_SHIFT',)
                        row.separator(factor=0.9)
                        row.label(text='', icon='EVENT_CTRL',)
                        row.separator(factor=2.35)
                        row.label(text='', icon='EVENT_ALT',)
                        row.separator(factor=2.35)
                        row.label(text='', icon='MOUSE_LMB',)

                    case "Draw Frame":
                        row.label(text='', icon='IMPORT',)
                        row.label(text='', icon='EVENT_J',)

                    case "Draw Route":
                        row.label(text='', icon='IMPORT',)
                        row.label(text='', icon='EVENT_E',)

                    case "Reroute Chamfer":
                        row.label(text='', icon='EVENT_CTRL',)
                        row.separator(factor=2.35)
                        row.label(text='', icon='EVENT_B',)

                panel.separator(factor=0.5)

            col.separator(factor=0.5)

            header, panel = col.panel(f'geobuilder_shortcut_layoutpanel_custom_{i}', default_closed=True,)
            header.label(text="Customize",)
            if (panel):
                panel.use_property_split = True

                sub = panel.column()
                subrow = sub.row(align=True)
                subrow.prop(kmi, "type", text='Key', event=True)

                sub = panel.column(heading='Modifiers:')
                sub.use_property_split = True
                sub.prop(kmi, "shift_ui",)
                sub.prop(kmi, "ctrl_ui",)
                sub.prop(kmi, "alt_ui",)

            continue

        return None 