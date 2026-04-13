import shutil
import time

import data_process
import math

from math import sqrt
import os
from statistics import mean
import json
import re
from pathlib import Path
import tkinter as tk
from tkinter import font as tk_font
import xml.etree.ElementTree as et

from data_process import TruckDataProcessor
from src.adjust import gearbox_adjust, engine_adjust
from src.gearbox_math import generate_exp_func
from src.adjust.cargo_adjust import cargo_mass_information, update_cargo_names, dump_cargo_info
from src.models import Cargo
from src.utils import xml_result, write_to_output

# Initialize Tkinter without opening a window (optional but clean)
root = tk.Tk()
root.withdraw()

def get_modified_file_if_possible(file_path) -> str:
    output_file_path = str(file_path).replace("input", "output", 1)
    if os.path.exists(output_file_path) and os.path.isfile(output_file_path):
        with open(Path(output_file_path), "r", encoding="utf-8") as file:
            return file.read()
    else:
        with open(file_path, "r") as file:
            return file.read()


def replace_string_in_file(file_path, old_string, new_string):
    # Read the file content

    file_data = get_modified_file_if_possible(file_path)

    if old_string not in file_data:
        print(f"WARNING: String '{old_string}' not found in file '{file_path}'.")

    # Replace all occurrences of the old string with the new string
    file_data = file_data.replace(old_string, new_string)

    write_to_output(file_path, file_data)


def buff_fuel_in_file(file_path, multiplier):
    # print(f"Buffing fuel for: {file_path}")
    content = get_modified_file_if_possible(file_path)

    # Find and replace FuelCapacity values
    def replace_fuel_capacity(match):
        current_value = int(match.group(1))
        new_value = current_value + sqrt(max(700 - current_value, 1))
        new_value = round(
            int(new_value * multiplier), -1
        )  # Increase by multiplier, round to nearest 10
        print(
            f"Fuel Capacity increase: {file_path.name}: {current_value} -> {new_value}"
        )
        return f'FuelCapacity="{new_value}"'

    # Use regex to find FuelCapacity="number" and replace with buffed value
    modified_content = re.sub(r'FuelCapacity="(\d+)"', replace_fuel_capacity, content)

    write_to_output(file_path, modified_content)


def buff_fuel_for_all_trucks(multiplier):
    trucks_folder = Path("input/initial/[media]/classes/trucks")
    dlc_folder = Path("input/initial/[media]/_dlc")

    for file_path in trucks_folder.glob("*.xml"):
        buff_fuel_in_file(file_path, multiplier)

    for folder_path in dlc_folder.glob("dlc_*", case_sensitive=False):
        dlc_truck_folder = Path(folder_path, "classes/trucks")
        for file_path in dlc_truck_folder.glob("*.xml"):
            buff_fuel_in_file(file_path, multiplier)


def buff_steering_speed_in_file(file_path):
    content = get_modified_file_if_possible(file_path)

    backsteer_speed = xml_result(
        content, True, ["Truck", "TruckData", "BackSteerSpeed"], "str"
    )
    if backsteer_speed is not None:
        backsteer_float = float(backsteer_speed)
        new_value = round(max(0.02, min(
            backsteer_float + (0.10 - backsteer_float) * 0.12, 0.1
        )),3)
        print(
            f"BackSteerSpeed increase: {file_path.name}: {backsteer_float} -> {new_value}"
        )
        content = content.replace(
            f'BackSteerSpeed="{backsteer_speed}"', f'BackSteerSpeed="{new_value}"'
        )

    steer_speed = xml_result(
        content, True, ["Truck", "TruckData", "SteerSpeed"], "str"
    )
    if steer_speed is not None:
        steer_float = float(steer_speed)
        new_value = round(max(0.0225,min(steer_float + (0.06 - steer_float) * 0.12, 0.04)),3)
        print(
            f"SteerSpeed increase: {file_path.name}: {steer_float} -> {new_value}"
        )
        content = content.replace(
            f'\tSteerSpeed="{steer_speed}"', f'\tSteerSpeed="{new_value}"'
        )

    write_to_output(file_path, content)


def buff_steering_speed_for_all_trucks():
    trucks_folder = Path("input/initial/[media]/classes/trucks")
    dlc_folder = Path("input/initial/[media]/_dlc")

    for file_path in trucks_folder.glob("*.xml"):
        buff_steering_speed_in_file(file_path)

    for folder_path in dlc_folder.glob("dlc_*", case_sensitive=False):
        dlc_truck_folder = Path(folder_path, "classes/trucks")
        for file_path in dlc_truck_folder.glob("*.xml"):
            buff_steering_speed_in_file(file_path)


def buff_steering_angle_in_file(file_path):
    content = get_modified_file_if_possible(file_path)

    def replace_steering_angle(match):
        current_value = float(match.group(1))
        if current_value >= 20:
            new_value = round(min(current_value + math.pow(sqrt(max((39 - current_value), 1)),1.1),40),1)
            if new_value != current_value:
                print(
                    f"Steering angle increase: {file_path.name}: {current_value} -> {new_value}"
                )
            return f'SteeringAngle="{new_value}"'
        return f'SteeringAngle="{current_value}"'

    modified_content = re.sub(r'SteeringAngle="(\d+)"', replace_steering_angle, content)

    write_to_output(file_path, modified_content)


def buff_steering_angle_for_all_trucks():
    trucks_folder = Path("input/initial/[media]/classes/trucks")
    dlc_folder = Path("input/initial/[media]/_dlc")

    for file_path in trucks_folder.glob("*.xml"):
        buff_steering_angle_in_file(file_path)

    for folder_path in dlc_folder.glob("dlc_*", case_sensitive=False):
        dlc_truck_folder = Path(folder_path, "classes/trucks")
        for file_path in dlc_truck_folder.glob("*.xml"):
            buff_steering_angle_in_file(file_path)


def buff_wheel_friction_value_in_file(
    file_path, friction_type="BodyFrictionAsphalt", weight=2, base: float = 3.0
):
    # print(f"Buffing asphalt for: {file_path}")
    content = get_modified_file_if_possible(file_path)

    # Find and replace Asphalt values
    def replace_asphalt_friction(match):
        current_value = float(match.group(1))
        weights = [base]
        for _ in range(weight + 1):
            weights.append(current_value)
        new_value = round(max(mean(weights), current_value), 1)
        if "train" not in file_path.name.lower():
            print(
                f"Friction increase: {file_path.name} - {friction_type}: {current_value} -> {new_value}"
            )
            new_value = round(new_value * 1.2, 1)
            return f'{friction_type}="{new_value}"'
        return f'{friction_type}="{current_value}"'

    # Use regex to find BodyFrictionAsphalt="number" and replace with buffed value
    modified_content = re.sub(
        rf'{friction_type}="(\d+(?:\.\d+)?)"', replace_asphalt_friction, content
    )

    write_to_output(file_path, modified_content)


def buff_friction_type_for_all_wheels(
    friction_type="BodyFrictionAsphalt", weight=2, base: float = 3.0
):
    wheels_folder = Path("input/initial/[media]/classes/wheels")
    dlc_folder = Path("input/initial/[media]/_dlc")

    buff_wheel_friction_value_in_file(
        Path("input/initial/[media]/_templates/trucks.xml"), friction_type, weight, base
    )

    # Iterate through all XML files in the folder
    for file_path in wheels_folder.glob("*.xml"):
        buff_wheel_friction_value_in_file(file_path, friction_type, weight, base)

    for folder_path in dlc_folder.glob("dlc_*", case_sensitive=False):
        dlc_truck_folder = Path(folder_path, "classes/wheels")

        # Iterate through all XML files in the folder
        for file_path in dlc_truck_folder.glob("*.xml"):
            buff_wheel_friction_value_in_file(file_path, friction_type, weight, base)


def get_text_width(text: str) -> int:
    # Define the font you want to use
    custom_font = tk_font.Font(family="Open Sans", size=10)
    width_pixels = custom_font.measure(text)

    # print(f"Pixel width: {width_pixels}px for {text}")
    return width_pixels


def add_grip_to_rock_file(file_path, friction=1.8):
    file_data = get_modified_file_if_possible(file_path)

    if "Friction" in file_data:
        return

    replace = False
    replacement = f'<Body Collisions="Dynamic" Friction="{friction}"'
    if '<Body Collisions="Dynamic"' in file_data:
        # Replace all occurrences of the old string with the new string
        file_data = file_data.replace('<Body Collisions="Dynamic"', replacement)
        replace = True
    elif '<Body\n\t\t\tCollisions="Dynamic"\n\t\t' in file_data:
        file_data = file_data.replace(
            '<Body\n\t\t\tCollisions="Dynamic"\n\t\t', replacement
        )
        replace = True

    if replace:
        write_to_output(file_path, file_data)

    else:
        print(f"No changes made to {file_path}")


def add_grip_to_rocks():
    rocks_models_folder = Path("input/initial/[media]/classes/models")
    dlc_folder = Path("input/initial/[media]/_dlc")

    # Iterate through all XML files in the folder
    for file_path in rocks_models_folder.glob("rock_*.xml"):
        add_grip_to_rock_file(file_path)

    for file_path in dlc_folder.glob(
        "*/classes/models/rock_*.xml", case_sensitive=False
    ):
        add_grip_to_rock_file(file_path)


def buff_suspension_damping(file_path: Path):
    file_data = get_modified_file_if_possible(file_path)

    if "Damping=" not in file_data:
        print(
            f"No Damping found in {file_path.stem}, adding it with a default value of 0.15."
        )
        replace_string_in_file(
            file_path, "SuspensionMin", 'Damping="0.15" SuspensionMin'
        )
    else:
        damping_values = re.findall(r'Damping="(\d*\.?\d+)"', file_data)
        unique_damping_values = set(damping_values)
        damping_floats = {value: float(value) for value in unique_damping_values}
        damping_replacements = {
            key: round(value + 0.025 + ((1.0 - value) / 10.0), 2)
            for key, value in damping_floats.items()
        }
        sorted_damping_replacements = dict(
            sorted(damping_replacements.items(), key=lambda item: item[1], reverse=True)
        )
        for key, value in sorted_damping_replacements.items():
            print(f"Increased damping value in {file_path.stem}: {key} -> {value}")
            replace_string_in_file(file_path, f'Damping="{key}"', f'Damping="{value}"')


def buff_all_suspension_damping():
    suspension_main_folder = Path("input/initial/[media]/classes/suspensions")
    dlc_folder = Path("input/initial/[media]/_dlc")

    # Iterate through all XML files in the folder
    for file_path in suspension_main_folder.glob("*.xml"):
        buff_suspension_damping(file_path)

    for file_path in dlc_folder.glob(
        "dlc_*/classes/suspensions/*.xml", case_sensitive=False
    ):
        buff_suspension_damping(file_path)


def camera_clipping_fixes():
    with open("reference/clipping.json", "r") as file:
        clipping_adjustments: list[str] = json.load(file)

    for file_path in clipping_adjustments:
        file_data = get_modified_file_if_possible(file_path)

        if "ClipCamera" not in file_data:
            file_data = file_data.replace(
                "<ModelBrand", '<ModelBrand ClipCamera="false"'
            )
            write_to_output(file_path, file_data)


def get_gearboxes_from_xml(file_path) -> None | dict:
    xml_data = get_modified_file_if_possible(file_path)
    if "_parent" in xml_data:
        print(f"Warning, parented gearbox file: {file_path}, skipping.")
    else:
        wrapped_xml_data = f"<fake_root>{xml_data}</fake_root>"
        root = et.fromstring(wrapped_xml_data)
        gearbox_variants = root.find("GearboxVariants")
        if gearbox_variants is not None:
            hauler_candidate = False
            if ("finetune" or "highway" in xml_data) and "offroad" in xml_data:
                hauler_candidate = True
            gear_boxes: dict = {
                "file_path": str(file_path),
                "hauler_candidate": hauler_candidate,
                "gearboxes": [],
            }
            for gearbox in gearbox_variants.findall("Gearbox"):
                reverse_vel = 0
                reverse_fuel_modifier = 0
                high_vel = 0
                high_fuel_modifier = 0
                price = 0
                high_exists = False
                low_exists = False
                low_plus_exists = False
                low_minus_exists = False
                is_manual_low_gear = False

                reverse_gear = gearbox.find("ReverseGear")
                if reverse_gear is not None:
                    reverse_vel = float(reverse_gear.attrib["AngVel"])
                    reverse_fuel_modifier = float(reverse_gear.attrib["FuelModifier"])
                high_gear = gearbox.find("HighGear")
                if high_gear is not None:
                    high_vel = float(high_gear.attrib["AngVel"])
                    high_fuel_modifier = float(high_gear.attrib["FuelModifier"])
                gears = []
                for gear in gearbox.findall("Gear"):
                    gears.append(
                        {
                            "ang_vel": float(gear.attrib["AngVel"]),
                            "fuel_modifier": float(gear.attrib["FuelModifier"]),
                        }
                    )
                game_data = gearbox.find("GameData")
                if game_data is not None:
                    price = int(game_data.attrib["Price"])
                    params = game_data.find("GearboxParams")
                    if params is not None:
                        if "IsManualLowGear" in params.attrib:
                            is_manual_low_gear = (
                                params.attrib["IsManualLowGear"].lower() == "true"
                            )
                        if "IsHighGearExists" in params.attrib:
                            high_exists = (
                                params.attrib["IsHighGearExists"].lower() == "true"
                            )
                        if "IsLowerGearExists" in params.attrib:
                            low_exists = (
                                params.attrib["IsLowerGearExists"].lower() == "true"
                            )
                        if "IsLowerPlusGearExists" in params.attrib:
                            low_plus_exists = (
                                params.attrib["IsLowerPlusGearExists"].lower() == "true"
                            )
                        if "IsLowerMinusGearExists" in params.attrib:
                            low_minus_exists = (
                                params.attrib["IsLowerMinusGearExists"].lower()
                                == "true"
                            )
                gear_boxes["gearboxes"].append(
                    {
                        "name": gearbox.attrib["Name"],
                        "awd_modifier": float(gearbox.attrib["AWDConsumptionModifier"]),
                        "damage_capacity": int(gearbox.attrib["DamageCapacity"]),
                        "damage_threshold": float(
                            gearbox.attrib["CriticalDamageThreshold"]
                        ),
                        "damage_consumption_modifier": float(
                            gearbox.attrib["DamagedConsumptionModifier"]
                        ),
                        "fuel_consumption": float(gearbox.attrib["FuelConsumption"]),
                        "idle_fuel_modifier": float(gearbox.attrib["IdleFuelModifier"]),
                        "min_break_frequency": float(gearbox.attrib["MinBreakFreq"]),
                        "max_break_frequency": float(gearbox.attrib["MaxBreakFreq"]),
                        "reverse_vel": float(reverse_vel),
                        "reverse_fuel_modifier": float(reverse_fuel_modifier),
                        "high_vel": float(high_vel),
                        "high_fuel_modifier": float(high_fuel_modifier),
                        "gears": gears,
                        "price": price,
                        "high_exists": high_exists,
                        "low_exists": low_exists,
                        "low_plus_exists": low_plus_exists,
                        "low_minus_exists": low_minus_exists,
                        "is_manual_low_gear": is_manual_low_gear,
                    }
                )
            return gear_boxes

    return None


def dump_gearbox_info() -> dict:
    gear_boxes = {}
    models_main_folder = Path("input/initial/[media]/classes/gearboxes")
    dlc_folder = Path("input/initial/[media]/_dlc")

    # Iterate through all XML files in the folder
    for file_path in models_main_folder.glob("*.xml"):
        gearboxes = get_gearboxes_from_xml(file_path)
        if gearboxes:
            gear_boxes[file_path.stem] = gearboxes

    for file_path in dlc_folder.glob("*/classes/gearboxes/*.xml", case_sensitive=False):
        gearboxes = get_gearboxes_from_xml(file_path)
        if gearboxes:
            gear_boxes[file_path.stem] = gearboxes

    with open("reference/info/gear_boxes_info.json", "w") as file:
        json.dump(gear_boxes, file, indent=4)

    return gear_boxes


def add_custom_gearboxes(gearboxes: dict):
    for file_name, gbs in gearboxes.items():
        template = ""
        with open("reference/gearbox_template.xml", "r") as file:
            template = file.read()
        lowest_vel = 10
        highest_vel = 0
        offroad_highest_vel = 0
        offroad_high_vel = 0
        offroad_1_fuel_consumption = 10
        reverse_vel = 0
        reverse_fuel_modifier = 0
        damage_capacity = 0
        awd_modifier = 0
        damaged_consumption_modifier = 0
        fuel_consumption = 0
        idle_fuel_modifier = 0
        min_break_frequency = 0
        max_break_frequency = 0
        price = 0
        gears = []

        if gbs["hauler_candidate"]:
            file_path = gbs["file_path"]
            for gb in gbs["gearboxes"]:
                for gear in gb["gears"]:
                    if float(gear["ang_vel"]) < lowest_vel:
                        lowest_vel = gear["ang_vel"]
                    if float(gear["ang_vel"]) > highest_vel:
                        highest_vel = gear["ang_vel"]
                if "offroad" in gb["name"]:
                    offroad_1_fuel_consumption = float(gb["gears"][0]["fuel_modifier"])
                    for gear in gb["gears"]:
                        if float(gear["ang_vel"]) > offroad_highest_vel:
                            offroad_highest_vel = gear["ang_vel"]
                    reverse_vel = gb["reverse_vel"] * 1.25
                    offroad_high_vel = gb["high_vel"]
                    reverse_fuel_modifier = gb["reverse_fuel_modifier"]
                    damage_capacity = round(int(gb["damage_capacity"] * 0.8), -1)
                    awd_modifier = round(
                        max((gb["awd_modifier"] * 4.0 + 1.3) / 5.0, 1.0), 2
                    )
                    damaged_consumption_modifier = gb["damage_consumption_modifier"]
                    fuel_consumption = gb["fuel_consumption"] * 0.9
                    idle_fuel_modifier = gb["idle_fuel_modifier"] * 0.85
                    min_break_frequency = gb["min_break_frequency"]
                    max_break_frequency = gb["max_break_frequency"]
                    price = int(gb["price"] * 1.5)
            top_vel = min((offroad_highest_vel * 3 + highest_vel) / 4.0, 14.0)
            if offroad_high_vel > 0:
                high_vel = (
                    ((top_vel * 0.6 * 3 + 9) / 4.0) * 2.0 + offroad_high_vel
                ) / 3.0
            else:
                high_vel = (top_vel * 0.6 * 3 + 9) / 4.0
            num_gears = 6
            gear_function = generate_exp_func(
                1.35, 1, lowest_vel * 1.1, num_gears, top_vel
            )
            modifier = float((offroad_1_fuel_consumption-1.0)/5.25)
            for i in range(1, num_gears + 1):
                gears.append(
                    {
                        "ang_vel": round(gear_function(i), 2),
                        "fuel_modifier": round(offroad_1_fuel_consumption+modifier - (modifier * i), 2),
                    }
                )
            gear_box_str = template
            gear_template = '<Gear AngVel="{vel}" FuelModifier="{fuel}" />\n\t'
            gears_str = ""
            for gear in gears:
                gear_str = gear_template.replace(
                    "{vel}", f"{round(gear['ang_vel'], 2)}"
                )
                gear_str = gear_str.replace(
                    "{fuel}", f"{round(gear['fuel_modifier'], 2)}"
                )
                gears_str += gear_str

            gear_box_str = gear_box_str.replace(
                "{awd_modifier}", f"{round(awd_modifier, 2)}"
            )
            gear_box_str = gear_box_str.replace(
                "{damage_threshold}", f"{0.65}"
            )
            gear_box_str = gear_box_str.replace(
                "{damage_capacity}", f"{damage_capacity}"
            )
            gear_box_str = gear_box_str.replace(
                "{damaged_consumption_modifier}",
                f"{round(damaged_consumption_modifier, 2)}",
            )
            gear_box_str = gear_box_str.replace(
                "{fuel_consumption}", f"{round(fuel_consumption, 2)}"
            )
            gear_box_str = gear_box_str.replace(
                "{idle_fuel_modifier}", f"{round(idle_fuel_modifier, 2)}"
            )
            gear_box_str = gear_box_str.replace("{id}", f"{file_name}_modern_hauler")
            gear_box_str = gear_box_str.replace(
                "{min_break_frequency}", f"{round(min_break_frequency, 2)}"
            )
            gear_box_str = gear_box_str.replace(
                "{max_break_frequency}", f"{round(max_break_frequency, 2)}"
            )
            gear_box_str = gear_box_str.replace(
                "{reverse_vel}", f"{round(reverse_vel, 2)}"
            )
            gear_box_str = gear_box_str.replace(
                "{reverse_fuel_modifier}", f"{round(reverse_fuel_modifier, 2)}"
            )
            gear_box_str = gear_box_str.replace("{high_vel}", f"{round(high_vel, 2)}")
            gear_box_str = gear_box_str.replace("{gears}", gears_str)
            gear_box_str = gear_box_str.replace("{high_fuel_modifier}", "1.4")
            gear_box_str = gear_box_str.replace("{price}", f"{price}")
            gear_box_str = gear_box_str.replace(
                "{description}",
                "A modern gearbox optimized for hauling cargo. Has a conservative high gear, moderate speeds, good low gear control, and smart auto gearing.",
            )
            gear_box_str = gear_box_str.replace("{name}", "Modern Hauler")
            print(f"Adding modern hauler gearbox to {file_path}")
            replace_string_in_file(
                file_path, "</GearboxVariants>", f"{gear_box_str}\n</GearboxVariants>"
            )


def get_split_color(c_str_1: str) -> dict[str, float]:
    c_str = (
        c_str_1.replace("g", "")
        .replace(" ", "")
        .replace("(", "")
        .replace(")", "")
        .strip()
    )
    splits = c_str.split(";")
    return {
        "r": float(splits[0]),
        "g": float(splits[1]),
        "b": float(splits[2]),
    }


def add_custom_colours():
    colours = []
    with open(Path("reference/colours_to_add.json"), "r") as f:
        colours = json.load(f)

    tree = et.parse(
        "input/initial/[media]/classes/customization_presets/customization_preset.xml"
    )
    root = tree.getroot()
    for truck in root.findall("Truck"):
        name = truck.attrib["Name"]
        ids: list[int] = []
        existing_colours: list[dict] = []
        has_split_colours = False
        for preset in truck.findall("CustomizationPreset"):
            colour_id = int(preset.attrib["Id"])
            ids.append(colour_id)
            c_str_1 = preset.attrib["TintColor1"]
            c_str_2 = preset.attrib["TintColor2"]
            c_str_3 = preset.attrib["TintColor3"]
            if c_str_1 != c_str_2 and c_str_2 != c_str_3 and c_str_1 != c_str_3:
                has_split_colours = True
                color_1: dict[str, float] = get_split_color(c_str_1)
                color_2: dict[str, float] = get_split_color(c_str_2)
                color_3: dict[str, float] = get_split_color(c_str_3)
                existing_colours.append({"1": color_1, "2": color_2, "3": color_3})

        if has_split_colours:
            max_id = max(ids) + 1
            print(f"Adding additional colours to {name}")
            for colour in colours:
                if (
                    colour["vehicle"] != name
                    and {"1": colour["1"], "2": colour["2"], "3": colour["3"]}
                    not in existing_colours
                ):
                    et.SubElement(
                        truck,
                        "CustomizationPreset",
                        Id=str(max_id),
                        TintColor1=f"g({int(colour['1']['r'])}; {int(colour['1']['g'])}; {int(colour['1']['b'])})",
                        TintColor2=f"g({int(colour['2']['r'])}; {int(colour['2']['g'])}; {int(colour['2']['b'])})",
                        TintColor3=f"g({int(colour['3']['r'])}; {int(colour['3']['g'])}; {int(colour['3']['b'])})",
                        MaterialOverrideName="skin_00",
                    )
                    max_id += 1

    et.indent(tree)
    output_file_path = Path(
        "output/initial/[media]/classes/customization_presets/customization_preset.xml"
    )
    directory = os.path.dirname(output_file_path)
    os.makedirs(directory, exist_ok=True)
    tree.write(output_file_path, encoding="utf-8")


def add_winch_slots_to_log(cargo_model_path):
    contents = get_modified_file_if_possible(cargo_model_path)
    if "LoadPoint Pos" not in contents:
        return
    load_points = re.findall(r'Pos="\(([^)]*)\)"', contents)
    if len(load_points) == 0:
        print(f"No load points found in {cargo_model_path}")
    for lp in load_points:
        coord = lp.replace(" ", "").replace("(", "").replace(")", "").strip().split(";")
        coords = [float(c) for c in coord]
        contents = contents.replace(
            f'<LoadPoint Pos="({lp})" />',
            f'<LoadPoint Pos="({lp})" />\n\t\t<WinchSocket Pos="({coords[0] * 1.3};{coords[1] + 0.1};0.0)" />',
        )
    write_to_output(cargo_model_path, contents)


def add_cargo_model_attach_points(cargo_model_path: Path):
    # print(f"Adding attach points to {cargo_model_path}")
    if "_log_" in cargo_model_path.stem:
        add_winch_slots_to_log(cargo_model_path)
        return
    contents = get_modified_file_if_possible(cargo_model_path)
    if "<_templates" in contents:
        print(f"Skipping {cargo_model_path} as it is incorrect data")
        return
    root = et.fromstring(contents)

    if root is None:
        return
    game_data = root.find("GameData")
    if game_data is None:
        return
    slots = game_data.get("PackSlotsNumber")
    if slots is None:
        return
    slots_count = int(slots)
    crane_socket = game_data.find("CraneSocket")
    if crane_socket is None:
        return
    crane_socket_pos = crane_socket.get("Pos")
    if crane_socket_pos is None:
        return
    crane_socket_pos = (
        crane_socket_pos.replace(" ", "").replace("(", "").replace(")", "")
    )
    positions = crane_socket_pos.split(";")
    if len(positions) != 3:
        return
    x, height, z = map(float, positions)
    half_height = round(height / 2, 2)
    slot_width = 1.15
    side_pos = 0.9
    offset = -0.1
    if slots_count >= 3:
        et.SubElement(
            game_data,
            "CraneSocket",
            {
                "Pos": f"({round(offset - 0.45 + (slot_width * slots_count), 2)}; {height}; {z})"
            },
        )
        et.SubElement(
            game_data,
            "CraneSocket",
            {
                "Pos": f"({round(-(offset - 0.45 + slot_width * slots_count), 2)}; {height}; {z})"
            },
        )

    et.SubElement(
        game_data,
        "CraneSocket",
        {
            "Pos": f"({round(offset + (slot_width * slots_count), 2)}; {half_height}; {z})"
        },
    )
    et.SubElement(
        game_data,
        "CraneSocket",
        {
            "Pos": f"({round(-(offset + slot_width * slots_count), 2)}; {half_height}; {z})"
        },
    )
    et.SubElement(
        game_data,
        "CraneSocket",
        {"Pos": f"({x}; {half_height}; {side_pos})"},
    )
    et.SubElement(
        game_data,
        "CraneSocket",
        {"Pos": f"({x}; {half_height}; {-side_pos})"},
    )
    et.SubElement(
        game_data,
        "WinchSocket",
        {"Pos": f"({x}; {height}; {z})"},
    )
    et.SubElement(
        game_data,
        "WinchSocket",
        {
            "Pos": f"({round(offset + (slot_width * slots_count), 2)}; {half_height}; {z})"
        },
    )
    et.SubElement(
        game_data,
        "WinchSocket",
        {
            "Pos": f"({round(-(offset + slot_width * slots_count), 2)}; {half_height}; {z})"
        },
    )
    et.SubElement(
        game_data,
        "WinchSocket",
        {"Pos": f"({x}; {half_height}; {side_pos})"},
    )
    et.SubElement(
        game_data,
        "WinchSocket",
        {"Pos": f"({x}; {half_height}; {-side_pos})"},
    )

    et.indent(root)
    output_path = Path(str(cargo_model_path).replace("input", "output", 1))
    print(f"Adding winch and crane sockets to: {cargo_model_path.stem}")
    et.ElementTree(root).write(output_path, encoding="utf-8")


def add_all_cargo_attach_points():
    cargo_models_path = Path("input/initial/[media]/classes/models")
    dlc_folder = Path("input/initial/[media]/_dlc")
    for cargo_model_path in cargo_models_path.glob(
        "*cargo_*.xml", case_sensitive=False
    ):
        add_cargo_model_attach_points(cargo_model_path)
    for cargo_model_path in dlc_folder.glob(
        "*/classes/models/cargo_*.xml", case_sensitive=False
    ):
        add_cargo_model_attach_points(cargo_model_path)


def make_ui_appends(adj_dict: dict[str, str], entire_file=True):
    for file_name in Path("input/initial/[strings]").glob("*.str"):
        new_file_content = ""
        file_entries: dict[str, str] = {}
        new_entries: dict[str, str] = {}
        with open(file_name, "r", encoding="utf-16LE") as f:
            lines = f.readlines()
        for line in lines:
            elements: list[str] = line.split("\t")
            file_ui_id = elements[0]
            file_ui_entry = elements[-1].strip().replace("\n", "")
            file_entries[file_ui_id] = file_ui_entry
        for ui_id, to_append in adj_dict.items():
            if ui_id in file_entries:
                new_entry = f'"{file_entries[ui_id].replace('"', "")}{to_append}"'
                if entire_file:
                    file_entries[ui_id] = new_entry
                else:
                    new_entries[ui_id] = new_entry
        if entire_file:
            for ui_id, entry in file_entries.items():
                new_file_content += f"{ui_id}\t\t\t\t{entry}\n"
        else:
            for ui_id, entry in new_entries.items():
                new_file_content += f"{ui_id}\t\t\t\t{entry}\n"

        write_to_output(file_name, new_file_content, encoding="utf-16LE")


def get_hex_color_scale(
    value: float, min_val=0.0, max_val=3.2, start_hex="#FA8072", end_hex="#3BB143"
):
    if value < min_val:
        value = min_val
    if value > max_val:
        value = max_val
    normalized = float(value / max_val)

    # Convert hex to RGB
    start_rgb = tuple(int(start_hex.lstrip("#")[i : i + 2], 16) for i in (0, 2, 4))
    end_rgb = tuple(int(end_hex.lstrip("#")[i : i + 2], 16) for i in (0, 2, 4))

    # Interpolate RGB values
    r = int(start_rgb[0] + (end_rgb[0] - start_rgb[0]) * normalized)
    g = int(start_rgb[1] + (end_rgb[1] - start_rgb[1]) * normalized)
    b = int(start_rgb[2] + (end_rgb[2] - start_rgb[2]) * normalized)
    hex_str = f"#{r:02x}{g:02x}{b:02x}"
    hex_str = hex_str.upper()

    return f'<font color=\\"{hex_str}\\">{value}</font>'


def get_updated_tire_names(game_data: TruckDataProcessor) -> dict[str, str]:
    ui_appends: dict[str, str] = {}
    wheel_dict: dict = game_data.wheel_dict
    for _, wheel_data in wheel_dict.items():
        ui_name = str(wheel_data["name_id"])
        if ui_name not in ui_appends:
            body_asphalt = get_hex_color_scale(wheel_data["BodyFrictionAsphalt"])
            body = get_hex_color_scale(wheel_data["BodyFriction"])
            substance = get_hex_color_scale(wheel_data["SubstanceFriction"])
            ui_appends[ui_name] = f" - {body_asphalt}|{body}|{substance}"

    return ui_appends


def get_updated_tire_desc(game_data: TruckDataProcessor) -> dict[str, str]:
    ui_appends = {}
    wheel_data: dict = game_data.wheel_dict
    for _, wheel in wheel_data.items():
        ui_descr = wheel["desc_id"]
        if ui_descr not in ui_appends:
            # mass = wheel["Mass"]
            softness = wheel["SoftForceScale"]
            # damage = wheel["DamageCapacity"]
            width = wheel["Width"]

            ui_appends[ui_descr] = f"\\nSoftness: {softness} | Width: {width}"

    return ui_appends


def get_updated_truck_descs(game_data: TruckDataProcessor) -> dict[str, str]:
    ui_appends = {}
    truck_data: dict = game_data.truck_data
    for _, truck in truck_data.items():
        ui_descr = truck["desc_ui_id"]
        if ui_descr not in ui_appends:
            min_t = int(truck["min_engine_torque"] / 100)
            max_t = int(truck["max_engine_torque"] / 100)
            ui_appends[ui_descr] = (
                f"\\nTorque Range: {min_t:,}-{max_t:,}\\nNm. Mass: {truck['mass']:,} kg."
            )

    return ui_appends


def get_updated_engine_descs(game_data: TruckDataProcessor) -> dict[str, str]:
    ui_appends = {}
    engine_data: dict = game_data.engine_dict
    for _, engine in engine_data.items():
        ui_descr = engine["ui_desc_id"]
        if ui_descr not in ui_appends:
            torque = int(engine["torque"] / 100)
            torque_efficiency = engine["torque_efficiency"]
            ui_appends[ui_descr] = (
                f"\\nTorque: {torque:,} Nm. Fuel Use: {round(engine['fuel_consumption'], 1)}\\nEfficiency: {torque_efficiency} Nm/L-consumed"
            )

    return ui_appends


def main():
    output_folder = Path("output/initial")
    shutil.rmtree(output_folder)
    os.makedirs(output_folder)
    time.sleep(0.5)

    adjustments = {}
    performed_adjustments = []
    with open("reference/adjustments.json", "r") as f:
        adjustments = json.load(f)

    for name, adj in adjustments.items():
        if name not in performed_adjustments and adj["enabled"]:
            replace_string_in_file(adj["path"], adj["from"], adj["to"])
            performed_adjustments.append(name)

    if "buffed_all_trucks_fuel_capacity" not in performed_adjustments:
        buff_fuel_for_all_trucks(1.25)
        performed_adjustments.append("buffed_all_trucks_fuel_capacity")

    if "buffed_all_trucks_steer_speed" not in performed_adjustments:
        buff_steering_speed_for_all_trucks()
        performed_adjustments.append("buffed_all_trucks_steer_speed")

    if "buffed_all_trucks_steering_angle" not in performed_adjustments:
        buff_steering_angle_for_all_trucks()
        performed_adjustments.append("buffed_all_trucks_steering_angle")

    if "buffed_all_wheel_asphalt" not in performed_adjustments:
        buff_friction_type_for_all_wheels("BodyFrictionAsphalt", 3, base=3.0)
        performed_adjustments.append("buffed_all_wheel_asphalt")

    if "buffed_all_wheel_body_friction" not in performed_adjustments:
        buff_friction_type_for_all_wheels("BodyFriction", 4, base=2.5)
        performed_adjustments.append("buffed_all_wheel_body_friction")

    if "buffed_all_wheel_substance_friction" not in performed_adjustments:
        buff_friction_type_for_all_wheels("SubstanceFriction", 5, base=2.3)
        performed_adjustments.append("buffed_all_wheel_substance_friction")

    cargo_list: list[Cargo] = []
    if "cargo_mass_adjustments" not in performed_adjustments:
        cargo_list = cargo_mass_information()
        performed_adjustments.append("cargo_mass_adjustments")

    if "add_grip_to_rocks" not in performed_adjustments:
        add_grip_to_rocks()
        performed_adjustments.append("add_grip_to_rocks")

    if "buff_all_suspension_damping" not in performed_adjustments:
        buff_all_suspension_damping()
        performed_adjustments.append("buff_all_suspension_damping")

    if "clipping_fixes" not in performed_adjustments:
        camera_clipping_fixes()
        performed_adjustments.append("clipping_fixes")

    if "modify_all_gearboxes" not in performed_adjustments:
        gearbox_adjust.modify_all_gearbox()
        performed_adjustments.append("modify_all_gearboxes")

    if "modify_all_engines" not in performed_adjustments:
        engine_adjust.modify_all_engines()
        performed_adjustments.append("modify_all_engines")

    if "add_hauling_gearbox" not in performed_adjustments:
        gearboxes_dict: dict = dump_gearbox_info()
        add_custom_gearboxes(gearboxes_dict)
        performed_adjustments.append("add_hauling_gearbox")

    if "add_custom_colours" not in performed_adjustments:
        add_custom_colours()
        performed_adjustments.append("add_custom_colours")

    if "add_cargo_attach_points" not in performed_adjustments:
        add_all_cargo_attach_points()
        performed_adjustments.append("add_cargo_attach_points")

    game_data: TruckDataProcessor = TruckDataProcessor(False)
    ui_appends: dict[str, str] = {}

    if "update_tire_names" not in performed_adjustments:
        ui_appends.update(get_updated_tire_names(game_data))
        performed_adjustments.append("update_tire_names")

    if "update_tire_desc" not in performed_adjustments:
        ui_appends.update(get_updated_tire_desc(game_data))
        performed_adjustments.append("update_tire_desc")

    if "cargo_name_updates" not in performed_adjustments:
        cargo_list, to_append_ui = update_cargo_names(cargo_list, game_data)
        ui_appends.update(to_append_ui)
        # dump_cargo_info(cargo_list)
        performed_adjustments.append("cargo_name_updates")

    if "truck_description_updates" not in performed_adjustments:
        ui_appends.update(get_updated_truck_descs(game_data))
        performed_adjustments.append("truck_description_updates")

    if "engine_description_updates" not in performed_adjustments:
        ui_appends.update(get_updated_engine_descs(game_data))
        performed_adjustments.append("engine_description_updates")

    if ui_appends != {}:
        make_ui_appends(ui_appends)

    with open("reference/performed_adjustments.json", "w") as f:
        json.dump(performed_adjustments, f, indent=4)


if __name__ == "__main__":
    main()
    data_process.main()
