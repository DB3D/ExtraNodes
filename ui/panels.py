# SPDX-FileCopyrightText: 2025 BD3D DIGITAL DESIGN
#
# SPDX-License-Identifier: GPL-2.0-or-later


import bpy 

from bl_ui.properties_paint_common import BrushPanel

from ..utils.str_utils import word_wrap


class NODEBOOSTER_PT_tool_search(bpy.types.Panel):
    """search element within your node_tree"""
    
    bl_idname = "NODEBOOSTER_PT_tool_search"
    bl_label = "Node Search"
    bl_category = "Node Booster"
    bl_space_type = "NODE_EDITOR"
    bl_region_type = "UI"
    
    @classmethod
    def poll(cls, context):
        return (context.space_data.type=='NODE_EDITOR') and (context.space_data.node_tree is not None)

    def draw(self, context):

        layout = self.layout
        # noodle_scn = context.scene.noodler
            
        # row = layout.row(align=True)
        # row.prop(noodle_scn,"search_keywords",text="",icon="VIEWZOOM")
        # row.prop(noodle_scn,"search_center",text="",icon="ZOOM_ALL")

        layout.label(text="Search Filters:")

        layout.use_property_split = True

        # layout.prop(noodle_scn,"search_labels")
        # layout.prop(noodle_scn,"search_types")
        # layout.prop(noodle_scn,"search_socket_names")
        # layout.prop(noodle_scn,"search_socket_types")
        # layout.prop(noodle_scn,"search_names")
        # layout.prop(noodle_scn,"search_input_only")
        # layout.prop(noodle_scn,"search_frame_only")

        # s = layout.column()
        # s.label(text=f"Found {noodle_scn.search_found} Element(s)")
    
        return None


class NODEBOOSTER_PT_tool_color_palette(bpy.types.Panel,BrushPanel):
    #palette api is a bit bad, it is operatiors designed for unified paint tools
    #so we are hijacking the context for us then.

    bl_idname = "NODEBOOSTER_PT_tool_color_palette"
    bl_label = "Assign Palette"
    bl_category = "Node Booster"
    bl_space_type = "NODE_EDITOR"
    bl_region_type = "UI"

    @classmethod
    def poll(cls, context):
        return (context.space_data.type=='NODE_EDITOR') and (context.space_data.node_tree is not None)

    def draw(self, context):

        layout = self.layout
        # noodle_scn = context.scene.noodler
        settings = context.tool_settings.vertex_paint
        unified = context.tool_settings.unified_paint_settings

        if settings is None: 
            col = layout.column()
            col.active = False
            col.scale_y = 0.8                
            word_wrap(layout=col, alert=False, active=True, max_char='auto',
                char_auto_sidepadding=0.95, context=context, alignment='LEFT',
                string="Please go in vertex-paint to initiate the palette API.",
                )
            return None 

        layout.template_ID(settings, "palette", new="palette.new")

        if settings.palette:
            row = layout.row(align=True)
            colo = row.row(align=True)
            colo.prop(unified,"color",text="")
            # colo.prop(noodle_scn,"palette_prop",text="")

            row.operator("noodler.reset_color",text="",icon="LOOP_BACK",)
            layout.template_palette(settings, "palette", color=True,)

        return None 


class NODEBOOSTER_PT_tool_frame(bpy.types.Panel):

    bl_idname = "NODEBOOSTER_PT_tool_frame"
    bl_label = "Draw Frame"
    bl_category = "Node Booster"
    bl_space_type = "NODE_EDITOR"
    bl_region_type = "UI"

    @classmethod
    def poll(cls, context):
        return (context.space_data.type=='NODE_EDITOR') and (context.space_data.node_tree is not None)
    
    def draw(self, context):

        layout = self.layout
        # noodle_scn = context.scene.noodler
        
        # layout.use_property_split = True

        # layout.prop(noodle_scn,"frame_label")
        # layout.prop(noodle_scn,"frame_label_size")

        # layout.prop(noodle_scn,"frame_use_custom_color")
        # col = layout.column()
        # col.prop(noodle_scn,"frame_sync_color")
        # col.active = noodle_scn.frame_use_custom_color
        # col.prop(noodle_scn,"frame_color")
        
        return None


class NODEBOOSTER_PT_shortcuts_memo(bpy.types.Panel):

    bl_idname = "NODEBOOSTER_PT_shortcuts_memo"
    bl_label = "Default Shortcuts"
    bl_category = "Node Booster"
    bl_space_type = "NODE_EDITOR"
    bl_region_type = "UI"

    @classmethod
    def poll(cls, context):
        return (context.space_data.type=='NODE_EDITOR') and (context.space_data.node_tree is not None)

    def draw(self, context):

        layout = self.layout
    
        col = layout.column(align=True)
        col.label(text="Loop Favorites:")
        box = col.box()
        box.scale_y = 0.9
        row = box.row(align=True)
        row.label(text='', icon='EVENT_Y',)

        layout.separator(type='LINE')

        col = layout.column(align=True)
        col.label(text="Add Favorite:")
        box = col.box()
        box.scale_y = 0.9
        row = box.row(align=True)
        row.label(text='', icon='EVENT_CTRL',)
        row.separator(factor=2.35)
        row.label(text='', icon='EVENT_Y',)

        layout.separator(type='LINE')

        col = layout.column(align=True)
        col.label(text="Draw Reroute:")
        box = col.box()
        box.scale_y = 0.9
        row = box.row(align=True)
        row.label(text='', icon='IMPORT',)
        row.label(text='', icon='EVENT_V',)

        layout.separator(type='LINE')

        col = layout.column(align=True)
        col.label(text="Draw Frame:")
        box = col.box()
        box.scale_y = 0.9
        row = box.row(align=True)
        row.label(text='', icon='IMPORT',)
        row.label(text='', icon='EVENT_J',)

        layout.separator(type='LINE')

        col = layout.column(align=True)
        col.label(text="Reroute Chamfer:")
        box = col.box()
        box.scale_y = 0.9
        row = box.row(align=True)
        row.label(text='', icon='EVENT_CTRL',)
        row.separator(factor=2.35)
        row.label(text='', icon='EVENT_B',)

        layout.separator(type='LINE')

        col = layout.column(align=True)
        col.label(text="Select Downstream:")
        box = col.box()
        box.scale_y = 0.9
        row = box.row(align=True)
        row.label(text='', icon='EVENT_CTRL',)
        row.separator(factor=2.35)
        row.label(text='', icon='MOUSE_LMB',)
        #
        box = col.box()
        box.scale_y = 0.9
        row = box.row(align=True)
        row.label(text='', icon='EVENT_SHIFT',)
        row.separator(factor=0.9)
        row.label(text='', icon='EVENT_CTRL',)
        row.separator(factor=2.35)
        row.label(text='', icon='MOUSE_LMB',)

        layout.separator(type='LINE')

        col = layout.column(align=True)
        col.label(text="Select Upstream:")
        box = col.box()
        box.scale_y = 0.9
        row = box.row(align=True)
        row.label(text='', icon='EVENT_CTRL',)
        row.separator(factor=2.35)
        row.label(text='', icon='EVENT_ALT',)
        row.separator(factor=2.35)
        row.label(text='', icon='MOUSE_LMB',)
        #
        box = col.box()
        box.scale_y = 0.9
        row = box.row(align=True)
        row.label(text='', icon='EVENT_SHIFT',)
        row.separator(factor=0.9)
        row.label(text='', icon='EVENT_CTRL',)
        row.separator(factor=2.35)
        row.label(text='', icon='EVENT_ALT',)
        row.separator(factor=2.35)
        row.label(text='', icon='MOUSE_LMB',)

        layout.separator(factor=2)

        return None 