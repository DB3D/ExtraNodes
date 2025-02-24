# SPDX-FileCopyrightText: 2025 BD3D DIGITAL DESIGN
#
# SPDX-License-Identifier: GPL-2.0-or-later


import bpy


#NOTE this functinality is implemented on an property update level

#TODO this functionality could be improved
#   TODO would be nice to add a recursive search feature in there
#   TODO perhaps better to use a search operator instead of using a prop update
#   TODO perhaps it would be nicer to confirm if user want to select (or enter a subgroup)
#      right now we directly select everything after search, perhaps 1) search, then display 
#      the found match on the ui, then 2) propose operators to select, recenter view, and enter nodetrees?
#   TODO instead of simple boolean for types, we should have enum with type match..
#   TODO add a case for matching nodetree names
#   TODO add a recursive toggle option


def search_upd(self, context):
    """search in context nodetree for nodes"""

    ng = context.space_data.edit_tree

    keywords = self.search_keywords.lower().replace(","," ").split(" ")
    keywords = set(keywords)

    def is_matching(keywords,terms):
        matches = []
        for k in keywords:
            for t in terms:
                matches.append(k in t)
        return any(matches) 

    found = []
    for n in ng.nodes:
        terms = []

        if (self.search_labels):
            name = n.label.lower()
            if not name:
                name = n.bl_label.lower()
            terms += name.split(" ")

        if (self.search_types):
            terms += n.type.lower().split(" ")

        if (self.search_names):
            name = n.name + " " + n.bl_idname
            terms += name.replace("_"," ").lower().split(" ")

        if (self.search_socket_names):
            for s in [*list(n.inputs),*list(n.outputs)]:
                name = s.name.lower() 
                if name not in terms:
                    terms += name.split(" ")

        if (self.search_socket_types):
            for s in [*list(n.inputs),*list(n.outputs)]:
                name = s.type.lower() 
                if name not in terms:
                    terms += name.split(" ")

        if (not is_matching(keywords,terms)):
            continue

        found.append(n)

        continue

    #unselect all
    for n in ng.nodes:
        n.select = False

    self.search_found = len(found)
    if (self.search_found==0):
        return None

    if (self.search_input_only):
        for n in found.copy():
            if (len(n.inputs)==0 and (n.type!="FRAME")):
                continue
            found.remove(n)
            continue

    if (self.search_frame_only):
        for n in found.copy():
            if (n.type!="FRAME"):
                found.remove(n)
            continue

    for n in found:
        n.select = True 

    if (self.search_center):
        with bpy.context.temp_override(area=context.area, space=context.area.spaces[0], region=context.area.regions[3]): 
            bpy.ops.node.view_selected()

    return None