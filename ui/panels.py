# SPDX-FileCopyrightText: 2025 BD3D DIGITAL DESIGN
#
# SPDX-License-Identifier: GPL-2.0-or-later


import bpy 

from bl_ui.properties_paint_common import BrushPanel

from ..__init__ import get_addon_prefs
from ..utils.str_utils import word_wrap


class NODEBOOSTER_PT_active_node(bpy.types.Panel):

    bl_idname = "NODEBOOSTER_PT_active_node"
    bl_label = "Active Node"
    bl_category = "Node Booster"
    bl_space_type = "NODE_EDITOR"
    bl_region_type = "UI"
    bl_order = 0

    @classmethod
    def poll(cls, context):
        if (context.space_data.type!='NODE_EDITOR'):
            return False
        if (context.space_data.node_tree is None):
            return False
        return True
    
    def draw(self, context):

        layout = self.layout

        ng = context.space_data.edit_tree
        active = ng.nodes.active

        if (not active):
            layout.active = False
            layout.label(text="No Active Nodes")
            return None
        
        if ('NodeBooster' not in active.bl_idname):
            layout.active = False
            layout.label(text="Select a Booster Node")
            return None
    
        sett_plugin = get_addon_prefs()
        ng = context.space_data.edit_tree
        n = ng.nodes.active

        layout.label(text=n.bl_label)
        
        match n.bl_idname:

            case 'GeometryNodeNodeBoosterMathExpression':

                header, panel = layout.panel("params_panelid", default_closed=False,)
                header.label(text="Parameters",)
                if (panel):
                    
                    col = panel.column(align=True)
                    row = col.row(align=True)
                    row.alert = bool(n.error_message)
                    row.prop(n,"user_mathexp", text="",)

                    panel.prop(n, "use_algrebric_multiplication",)
                    panel.prop(n, "use_macros",)
                    
                    if (n.error_message):
                        lbl = col.row()
                        lbl.alert = bool(n.error_message)
                        lbl.label(text=n.error_message)
                
                header, panel = layout.panel("inputs_panelid", default_closed=True,)
                header.label(text="Inputs",)
                if (panel):
                    
                    col = panel.column()
                    col.use_property_split = True
                    col.use_property_decorate = True
                    
                    for s in n.inputs:
                        row = col.row()
                        row.active = not any(s.links)
                        row.prop(s,'default_value', text=s.name,)

                header, panel = layout.panel("doc_panelid", default_closed=True,)
                header.label(text="Documentation",)
                if (panel):
                    word_wrap(layout=panel, alert=False, active=True, max_char='auto',
                        char_auto_sidepadding=0.9, context=context, string=n.bl_description,
                        )
                    panel.operator("wm.url_open", text="Documentation",).url = "https://blenderartists.org/t/nodebooster-extra-nodes-and-functionalities-for-nodeeditors"

                header, panel = layout.panel("doc_glossid", default_closed=True,)
                header.label(text="Glossary",)
                if (panel):
                    
                    from ..customnodes.mathexpression import DOCSYMBOLS, USER_FUNCTIONS
                    col = panel.column()
                    
                    for symbol,v in DOCSYMBOLS.items():
                        
                        desc = v['name']+'\n'+v['desc'] if v['desc'] else v['name']
                        row = col.row()
                        row.scale_y = 0.65
                        row.box().label(text=symbol,)
                        
                        col.separator(factor=0.5)
                        
                        word_wrap(layout=col, alert=False, active=True, max_char='auto',
                            char_auto_sidepadding=0.95, context=context, string=desc, alignment='LEFT',
                            )
                        col.separator()
                    
                    for f in USER_FUNCTIONS:
                        
                        #collect functiona arguments for user
                        fargs = list(f.__code__.co_varnames[:f.__code__.co_argcount])
                        if 'cls' in fargs:
                            fargs.remove('cls')
                        fstr = f'{f.__name__}({", ".join(fargs)})'
                        
                        row = col.row()
                        row.scale_y = 0.65
                        row.box().label(text=fstr,)
                        
                        col.separator(factor=0.5)
                        
                        word_wrap(layout=col, alert=False, active=True, max_char='auto',
                            char_auto_sidepadding=0.95, context=context, string=f.__doc__, alignment='LEFT',
                            )
                        col.separator()
                        
                header, panel = layout.panel("dev_panelid", default_closed=True,)
                header.label(text="Development",)
                if (panel):
                    panel.active = False

                    col = panel.column(align=True)
                    col.label(text="SanatizedExp:")
                    row = col.row()
                    row.enabled = False
                    row.prop(n, "debug_sanatized", text="",)

                    col = panel.column(align=True)
                    col.label(text="FunctionExp:")
                    row = col.row()
                    row.enabled = False
                    row.prop(n, "debug_fctexp", text="",)

                    col = panel.column(align=True)
                    col.label(text="NodeTree:")
                    col.template_ID(n, "node_tree")

                col = layout.column(align=True)
                op = col.operator("extranode.bake_mathexpression", text="Convert to Group",)
                op.nodegroup_name = n.node_tree.name
                op.node_name = n.name

            case 'GeometryNodeNodeBoosterPythonApi':

                header, panel = layout.panel("params_panelid", default_closed=False,)
                header.label(text="Parameters",)
                if (panel):

                    col = panel.column(align=True)
                    row = col.row(align=True)
                    row.alert = n.evaluation_error
                    icon = 'ERROR' if n.evaluation_error else 'SCRIPT'
                    row.prop(n,"user_expression", text="", icon=icon,)

                header, panel = layout.panel("prefs_panelid", default_closed=True,)
                header.label(text="Preferences",)
                if (panel):
                    col = panel.column(align=True)
                    col.label(text="Namespace Convenience:")
                    
                    row = col.row(align=True)
                    row.enabled = False
                    row.prop(sett_plugin,"pynode_convenience_exec1",text="",)
                    
                    row = col.row(align=True)
                    row.enabled = False
                    row.prop(sett_plugin,"pynode_convenience_exec2",text="",)
                    
                    row = col.row(align=True)
                    row.prop(sett_plugin,"pynode_convenience_exec3",text="",)
                
                    panel.prop(sett_plugin,"pynode_depseval",)

                header, panel = layout.panel("doc_panelid", default_closed=True,)
                header.label(text="Documentation",)
                if (panel):
                    word_wrap(layout=panel, alert=False, active=True, max_char='auto',
                        char_auto_sidepadding=0.9, context=context, string=n.bl_description,
                        )
                    panel.operator("wm.url_open", text="Documentation",).url = "https://blenderartists.org/t/nodebooster-extra-nodes-and-functionalities-for-nodeeditors"

                header, panel = layout.panel("dev_panelid", default_closed=True,)
                header.label(text="Development",)
                if (panel):
                    panel.active = False
                                    
                    col = panel.column(align=True)
                    col.label(text="NodeTree:")
                    col.template_ID(n, "node_tree")
                    
                    col = panel.column(align=True)
                    col.label(text="Debugging:")
                    row = col.row()
                    row.enabled = False
                    row.prop(n, "debug_update_counter",)

            case 'GeometryNodeNodeBoosterSequencerVolume':

                header, panel = layout.panel("doc_panelid", default_closed=True,)
                header.label(text="Documentation",)
                if (panel):
                    word_wrap(layout=panel, alert=False, active=True, max_char='auto',
                        char_auto_sidepadding=0.9, context=context, string=n.bl_description,
                        )
                    panel.operator("wm.url_open", text="Documentation",).url = "https://blenderartists.org/t/nodebooster-extra-nodes-and-functionalities-for-nodeeditors"
                    
                header, panel = layout.panel("dev_panelid", default_closed=True,)
                header.label(text="Development",)
                if (panel):
                    panel.active = False
                                    
                    col = panel.column(align=True)
                    col.label(text="NodeTree:")
                    col.template_ID(n, "node_tree")

            case 'GeometryNodeNodeBoosterIsRenderedView':
                
                header, panel = layout.panel("doc_panelid", default_closed=True,)
                header.label(text="Documentation",)
                if (panel):
                    word_wrap(layout=panel, alert=False, active=True, max_char='auto',
                        char_auto_sidepadding=0.9, context=context, string=n.bl_description,
                        )
                    panel.operator("wm.url_open", text="Documentation",).url = "https://blenderartists.org/t/nodebooster-extra-nodes-and-functionalities-for-nodeeditors"
                    
                header, panel = layout.panel("dev_panelid", default_closed=True,)
                header.label(text="Development",)
                if (panel):
                    panel.active = False
                                    
                    col = panel.column(align=True)
                    col.label(text="NodeTree:")
                    col.template_ID(n, "node_tree")
            
            case 'GeometryNodeNodeBoosterCameraInfo':

                header, panel = layout.panel("params_panelid", default_closed=False,)
                header.label(text="Parameters",)
                if (panel):
                        
                    row = panel.row(align=True)
                    sub = row.row(align=True)
                    sub.active = not n.use_scene_cam

                    if (n.use_scene_cam):
                        sub.prop(bpy.context.scene, "camera", text="", icon="CAMERA_DATA")
                    else: sub.prop(n, "camera_obj", text="", icon="CAMERA_DATA")

                    panel.prop(n, "use_scene_cam",)

                header, panel = layout.panel("doc_panelid", default_closed=True,)
                header.label(text="Documentation",)
                if (panel):
                    word_wrap(layout=panel, alert=False, active=True, max_char='auto',
                        char_auto_sidepadding=0.9, context=context, string=n.bl_description,
                        )
                    panel.operator("wm.url_open", text="Documentation",).url = "https://blenderartists.org/t/nodebooster-extra-nodes-and-functionalities-for-nodeeditors"

                header, panel = layout.panel("dev_panelid", default_closed=True,)
                header.label(text="Development",)
                if (panel):
                    panel.active = False

                    col = panel.column(align=True)
                    col.label(text="NodeTree:")
                    col.template_ID(n, "node_tree")    

        return None


class NODEBOOSTER_PT_tool_search(bpy.types.Panel):
    """search element within your node_tree"""

    bl_idname = "NODEBOOSTER_PT_tool_search"
    bl_label = "Search"
    bl_category = "Node Booster"
    bl_space_type = "NODE_EDITOR"
    bl_region_type = "UI"
    bl_order = 1

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
    bl_order = 2

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


class NODEBOOSTER_PT_shortcuts_memo(bpy.types.Panel):

    bl_idname = "NODEBOOSTER_PT_shortcuts_memo"
    bl_label = "Shortcuts"
    bl_category = "Node Booster"
    bl_space_type = "NODE_EDITOR"
    bl_region_type = "UI"
    bl_order = 3

    @classmethod
    def poll(cls, context):
        return (context.space_data.type=='NODE_EDITOR') and (context.space_data.node_tree is not None)

    def draw(self, context):

        from ..operators import ADDON_KEYMAPS
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


class NODEBOOSTER_PT_tool_frame(bpy.types.Panel):

    bl_idname = "NODEBOOSTER_PT_tool_frame"
    bl_label = "Draw Frame"
    bl_category = "Node Booster"
    bl_space_type = "NODE_EDITOR"
    bl_region_type = "UI"
    bl_order = 4

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
