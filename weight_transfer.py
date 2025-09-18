import bpy

def transfer_weights(object_a_name, object_b_name, mapping, clear_target=False, vert_mapping='POLYINTERP_NEAREST'):
    """
    Transfer vertex weights from object_b -> object_a using explicit group mapping.
    mapping: list of (dst_group_name, src_group_name) tuples
    clear_target: if True, clears all vertex groups on object_a before transfer
    vert_mapping: vertex mapping method for data_transfer (default 'POLYINTERP_NEAREST')
    """
    if object_a_name not in bpy.data.objects or object_b_name not in bpy.data.objects:
        raise ValueError("One or both object names not found in bpy.data.objects")

    obj_a = bpy.data.objects[object_a_name]
    obj_b = bpy.data.objects[object_b_name]

    if obj_a.type != 'MESH' or obj_b.type != 'MESH':
        raise TypeError("Both objects must be mesh objects")

    # Optionally clear all groups on target
    if clear_target:
        obj_a.vertex_groups.clear()

    # Function to make selection/active proper for data_transfer
    def prep_selection_for_transfer(active_obj, selected_objs):
        bpy.ops.object.select_all(action='DESELECT')
        for o in selected_objs:
            o.select_set(True)
        active_obj.select_set(True)
        bpy.context.view_layer.objects.active = active_obj

    for dst_name, src_name in mapping:
        if src_name not in obj_b.vertex_groups:
            print(f"[SKIP] source group '{src_name}' not found on {obj_b.name}")
            continue

        # Ensure target group exists on obj_a
        if dst_name not in obj_a.vertex_groups:
            obj_a.vertex_groups.new(name=dst_name)

        # Backup and rename the source group on obj_b -> dst_name (temporary)
        src_group = obj_b.vertex_groups[src_name]
        orig_name = src_group.name
        try:
            # If dst_name already exists on obj_b (unlikely), pick a unique temporary name
            if dst_name in obj_b.vertex_groups and dst_name != orig_name:
                temp_unique = dst_name + "_tmp_for_transfer"
                # ensure uniqueness
                i = 1
                while temp_unique in obj_b.vertex_groups:
                    temp_unique = f"{dst_name}_tmp_for_transfer_{i}"
                    i += 1
                # rename the existing conflict group to the temp_unique to avoid name collision
                conflict = obj_b.vertex_groups[dst_name]
                conflict.name = temp_unique

            # Now rename the source group to the dst_name so data_transfer maps by name/active
            src_group.name = dst_name

            # Prepare selection: active is obj_a, selected includes obj_b (so with use_reverse_transfer=True it will transfer B->A)
            prep_selection_for_transfer(obj_a, [obj_b])

            # Make the relevant groups active on each object
            # On obj_b (source), its group named dst_name is now the source active group
            obj_b.vertex_groups.active = obj_b.vertex_groups[dst_name]
            # On obj_a (target), set the dst group active (exists or was created above)
            obj_a.vertex_groups.active = obj_a.vertex_groups[dst_name]

            # Run data_transfer from selected -> active (use_reverse_transfer=True)
            bpy.ops.object.data_transfer(
                data_type='VGROUP_WEIGHTS',
                vert_mapping=vert_mapping,
                layers_select_src='ACTIVE',
                layers_select_dst='ACTIVE',
                use_create=True,
                use_reverse_transfer=True
            )

            print(f"[OK] transferred '{src_name}' (B) -> '{dst_name}' (A)")

        finally:
            # restore original source group name on obj_b (even if error occurred)
            # find the group object currently named dst_name on obj_b; it might be our renamed src_group
            # but indices might have changed, so search for group whose name is dst_name and has same index as src_group if possible
            # simplest: if orig_name exists already, restore src_group by reference if still present
            # find a vertex group that contains the original name or the dst_name.
            # attempt to restore the renamed group back to orig_name
            # Note: if we had renamed a conflicting group earlier to a temp_unique name, we should restore it too.
            found = None
            for g in obj_b.vertex_groups:
                if g.name == dst_name:
                    found = g
                    break
            if found:
                found.name = orig_name

            # Restore any conflict-temp group names back to the dst_name if created above
            # (search for names with suffix '_tmp_for_transfer' and move them back)
            for g in obj_b.vertex_groups:
                if g.name.startswith(dst_name + "_tmp_for_transfer"):
                    g.name = dst_name

    print("All mapped transfers complete.")

    print("Weight transfer complete.")

transfer_weights("Cube", "YelanBody.001", [("1","53"),("2","85"),("3","65")])