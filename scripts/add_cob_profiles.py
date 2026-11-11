# SPDX-License-Identifier: GPL-3.0-or-later
"""Install STORM IES files and add COB Light Profile menus.

blender -b library/Sympatico_Lighting_Native.blend --python scripts/add_cob_profiles.py -- --ies-dir "/path/to/STORM 1200x IES Files" --save

Without --save this only changes the open file in memory. IES files are copied to
library/ies/. Bundled manufacturer data is outside the project licenses.
"""
import argparse
import math
from pathlib import Path
import runpy
import shutil
import sys

import bpy

ROOT = Path(__file__).resolve().parents[1]
PROFILES = [
    ("STORM 1200x — Bare Head", "STORM 1200x - Bare Head.ies", "storm_1200x_bare.ies"),
    ("STORM 1200x — CPC 15°", "STORM 1200x - CPC 15°.ies", "storm_1200x_cpc_15.ies"),
    ("STORM 1200x — CPC 30°", "STORM 1200x - CPC 30°.ies", "storm_1200x_cpc_30.ies"),
    ("STORM 1200x — CPC 45°", "STORM 1200x - CPC 45°.ies", "storm_1200x_cpc_45.ies"),
    ("STORM 1200x — F12 Fresnel Spot", "STORM 1200x - F12 Fresnel Spot.ies", "storm_1200x_f12_spot.ies"),
    ("STORM 1200x — F12 Fresnel Wide", "STORM 1200x - F12 Fresnel Wide.ies", "storm_1200x_f12_wide.ies"),
]
drive = runpy.run_path(str(ROOT / "scripts/upgrade_cob_native.py"))["drive"]


def ies_peak(path):
    """Validate supported LM-63 type C files and return Cycles' peak intensity."""
    text = path.read_text(encoding="utf-8-sig")
    if "TILT=NONE" not in text:
        raise ValueError(f"{path.name}: only TILT=NONE is supported")
    values = [float(x) for x in text.split("TILT=NONE", 1)[1].replace(",", " ").split()]
    if len(values) < 13 or int(values[5]) != 1:
        raise ValueError(f"{path.name}: expected a type C IES distribution")
    nv, nh = int(values[3]), int(values[4])
    offset = 13 + nv + nh
    candela = values[offset:offset + nv * nh]
    if len(candela) != nv * nh or not candela:
        raise ValueError(f"{path.name}: incomplete candela table")
    peak = max(candela) * values[2] * values[10] * values[11]
    if not math.isfinite(peak) or peak <= 0:
        raise ValueError(f"{path.name}: invalid intensity")
    # Cycles' LM-63 conversion: intern/cycles/util/ies.cpp, 4*pi / 177.83.
    return peak * 0.0706650768394


def configure_geometry(group, socket):
    """Resolve profile geometry inside the node graph, preserving manual settings."""
    inputs = next(n for n in group.nodes if n.type == "GROUP_INPUT")
    manual = group.nodes["Attachment selection"]
    choice = group.nodes["Light Profile options"]
    choice.label = "Profile index"
    for index, label in enumerate(["Default"] + [p[0] for p in PROFILES]):
        choice.inputs[label].default_value = index

    def index_switch(name, data_type):
        node = group.nodes.get(name)
        if node is None:
            node = group.nodes.new("GeometryNodeIndexSwitch")
            node.name = name
            node.data_type = data_type
            while len(node.index_switch_items) < 7:
                node.index_switch_items.new()
        group.links.new(choice.outputs[0], node.inputs["Index"])
        return node

    effective = index_switch("Profile | Effective attachment", "INT")
    effective.location = (choice.location.x + 250, choice.location.y)
    destinations = [link.to_socket for link in manual.outputs[0].links
                    if link.to_node != effective]
    for destination in destinations:
        group.links.new(effective.outputs[0], destination)
    group.links.new(manual.outputs[0], effective.inputs[1])
    for index, (label, _, _) in enumerate(PROFILES, start=2):
        effective.inputs[index].default_value = (
            0 if "Bare Head" in label else 1 if "CPC" in label else 2)

    # Lazy index switches let Blender infer which manual controls are unused.
    beam = index_switch("Profile | Fresnel geometry", "FLOAT")
    beam.location = (choice.location.x + 250, choice.location.y - 350)
    beam.label = "Lens geometry only; IES defines the actual beam"
    group.links.new(inputs.outputs["Fresnel Beam (deg)"], beam.inputs[1])
    for index, (label, _, _) in enumerate(PROFILES, start=2):
        beam.inputs[index].default_value = 15 if "Fresnel Spot" in label else 45
    group.links.new(beam.outputs[0],
                    group.nodes["Fresnel attachment"].inputs["Fresnel Beam (deg)"])
    for item in group.interface.items_tree:
        if item.name == "Attachment":
            item.description = "Manual attachment for Default. An IES profile automatically selects matching geometry; returning to Default restores this choice."
        elif item.name == "Fresnel Beam (deg)":
            item.description = "Manual beam angle for Default only. IES profiles supply the measured beam and override this control."
    socket.description = "Default uses manual attachment and beam controls. IES profiles select matching geometry and override beam shape; Cycles only."



def install(ies_dir=None):
    folder = ROOT / "library/ies"
    def source_path(source, filename):
        if not ies_dir:
            return folder / filename
        exact = Path(ies_dir) / source
        if exact.exists():
            return exact
        # ZIP extractors may decode the degree symbol differently.
        def key(name):
            return ''.join(c.lower() for c in name if c.isascii() and c.isalnum())
        matches = [p for p in Path(ies_dir).glob("*.ies") if key(p.name) == key(source)]
        if len(matches) != 1:
            raise FileNotFoundError(f"Expected one matching IES file for {source}")
        return matches[0]
    sources = [source_path(source, filename) for _, source, filename in PROFILES]
    # Validate every source before changing the scene.
    peaks = [ies_peak(path) for path in sources]
    folder.mkdir(exist_ok=True)
    if ies_dir:
        for source, (_, _, filename) in zip(sources, PROFILES):
            destination = folder / filename
            if source.resolve() != destination.resolve():
                shutil.copyfile(source, destination)

    for body in list(bpy.data.objects):
        mod = next((m for m in body.modifiers if m.type == "NODES"
                    and m.name == "COB — Controls"), None)
        if not mod:
            continue
        group = mod.node_group
        socket = next((s for s in group.interface.items_tree
                       if s.item_type == "SOCKET" and s.in_out == "INPUT"
                       and s.name == "Light Profile"), None)
        if socket is None:
            socket = group.interface.new_socket(name="Light Profile", in_out="INPUT",
                                                socket_type="NodeSocketMenu")
            socket.description = "Default uses attachment lighting. IES profiles override beam shape; Cycles only. Requires local IES files."
            menu = group.nodes.new("GeometryNodeMenuSwitch")
            menu.name = "Light Profile options"
            menu.label = "Native-light driver selector"
            menu.data_type = "INT"
            menu.enum_items.clear()
            for label in ["Default"] + [p[0] for p in PROFILES]:
                menu.enum_items.new(label)
            group_in = next(n for n in group.nodes if n.type == "GROUP_INPUT")
            group.links.new(group_in.outputs[socket.identifier], menu.inputs["Menu"])
            menu.location = (group_in.location.x + 250, group_in.location.y - 700)
            group.interface.move(socket, 2)
        configure_geometry(group, socket)
        body.update_tag()
        bpy.context.view_layer.update()
        selected = getattr(mod.properties.inputs, socket.identifier)
        items = {i.identifier: i.value for i in selected.bl_rna.properties["value"].enum_items}
        default = items["Default"]
        if selected.value not in items:
            selected.value = "Default"
        path = mod.path_from_id() + ".properties.inputs." + socket.identifier + ".value"
        sockets = {s.name: s.identifier for s in group.interface.items_tree
                   if s.item_type == "SOCKET" and s.in_out == "INPUT"}
        def prop(name):
            return mod.path_from_id() + ".properties.inputs." + sockets[name] + ".value"

        spot = next(o for o in body.children_recursive if o.type == "LIGHT" and o.data.type == "SPOT")
        area = next(o for o in body.children_recursive if o.type == "LIGHT" and o.get("sympatico_cob_area"))
        ies = next((o for o in body.children_recursive if o.get("sympatico_cob_ies")), None)
        if ies is None:
            data = spot.data.copy()
            data.name = body.name + " | IES photometric source"
            data.type = "POINT"
            data.animation_data_clear()
            ies = bpy.data.objects.new(body.name + " | IES source", data)
            ies.parent = body
            ies.rotation_euler = (math.pi, 0, 0)
            ies["sympatico_cob_ies"] = True
            for collection in body.users_collection:
                collection.objects.link(ies)
        data = ies.data
        data.normalize = True
        data.cycles.max_bounces = 1024
        for axis in range(3):
            drive(ies, "scale", "1/max(abs(s),0.000001)", body, {"s": f"scale[{axis}]"}, axis)

        # Preserve default energy expressions and gate them off for IES selection.
        for native in (spot, area):
            curve = next(d for d in native.data.animation_data.drivers if d.data_path == "energy")
            if not any(v.name == "lp" for v in curve.driver.variables):
                original = curve.driver.expression
                var = curve.driver.variables.new()
                var.name = "lp"
                var.type = "SINGLE_PROP"
                var.targets[0].id = body
                var.targets[0].data_path = path
                curve.driver.expression = f"({original}) if lp=={default} else 0"

        drive(data, "energy", f"0 if lp=={default} else w*4*pi", body,
              {"lp": path, "w": prop("Wattage")})
        # IES selection determines the attachment independently of saved manual mode.
        bare = items[PROFILES[0][0]]
        fspot = items[PROFILES[4][0]]
        fwide = items[PROFILES[5][0]]
        drive(ies, "location",
              f"(0.001 if lp=={bare} else (.292-.0026*(15 if lp=={fspot} else 45)+r*.0254 "
              f"if lp=={fspot} or lp=={fwide} else rd*.0254+c*.0127+.003))/max(abs(s),0.000001)",
              body, {"lp": path, "r": prop("Fresnel Source Radius (in)"),
                     "rd": prop("Reflector Depth (in)"), "c": prop("COB Diameter (in)"), "s": "scale[2]"}, 2)
        drive(data, "shadow_soft_size",
              f"r*.0254 if lp=={fspot} or lp=={fwide} else c*.0127", body,
              {"lp": path, "r": prop("Fresnel Source Radius (in)"), "c": prop("COB Diameter (in)")})

        nt = data.node_tree
        for node in list(nt.nodes):
            if node.name.startswith("IES |"):
                nt.nodes.remove(node)
        emission = next(n for n in nt.nodes if n.type == "EMISSION")
        total = None
        for index, ((label, _, filename), peak) in enumerate(zip(PROFILES, peaks)):
            tex = nt.nodes.new("ShaderNodeTexIES")
            tex.name = "IES | " + label
            tex.label = label
            tex.mode = "EXTERNAL"
            tex.filepath = bpy.path.relpath(str(folder / filename)) if bpy.data.filepath else str(folder / filename)
            tex.inputs["Strength"].default_value = 1.0 / peak
            tex.location = (-900, -index * 220)
            weight = nt.nodes.new("ShaderNodeMath")
            weight.name = "IES | select " + str(index)
            weight.operation = "MULTIPLY"
            weight.location = (-600, -index * 220)
            nt.links.new(tex.outputs["Factor"], weight.inputs[0])
            drive(nt, weight.inputs[1].path_from_id("default_value"),
                  f"1 if lp=={items[label]} else 0", body, {"lp": path})
            if total is None:
                total = weight.outputs[0]
            else:
                add = nt.nodes.new("ShaderNodeMath")
                add.name = "IES | sum " + str(index)
                add.operation = "ADD"
                add.location = (-300 + index * 150, -index * 150)
                nt.links.new(total, add.inputs[0])
                nt.links.new(weight.outputs[0], add.inputs[1])
                total = add.outputs[0]
        nt.links.new(total, emission.inputs["Strength"])
        body.update_tag()
        print("IES_PROFILE_MENU", body.name, items)
    bpy.context.view_layer.update()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--ies-dir", type=Path)
    parser.add_argument("--save", action="store_true")
    args = parser.parse_args(sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else [])
    install(args.ies_dir)
    if args.save:
        if not bpy.data.filepath:
            raise RuntimeError("Save the blend file to a location before using --save")
        bpy.ops.wm.save_as_mainfile(filepath=bpy.data.filepath, compress=True)
