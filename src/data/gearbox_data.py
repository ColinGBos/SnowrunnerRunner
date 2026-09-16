import json
import random

from lxml import etree  # ty:ignore[unresolved-import]
from pathlib import Path

import utils
from src.utils import (
    get_modified_file_if_possible,
)


def get_gearbox_data(file_path: Path, use_initial_files: bool, ui_dict: dict[str, str], existing_gearboxes=None) -> dict[str, dict]:
    rets: dict[str, dict] = {}
    gearbox_file = file_path.stem
    full_file: str = str(file_path.relative_to(utils.root_path))
    contents = get_modified_file_if_possible(file_path, use_initial_files)
    #
    # if "_parent" in contents:
    #     print(f"Warning, parented gearbox file: {file_path}, skipping.")
    #     return rets

    parser = etree.XMLParser(recover=True)
    wrapped_xml_data = f"<fake_root>{contents}</fake_root>"
    root = etree.fromstring(wrapped_xml_data, parser=parser)
    templates: list[dict] = []
    parent_template = root.find("_parent")
    if parent_template is not None:
        template_name = parent_template.get("File")
        if existing_gearboxes is not None:
            for existing_gearbox_id, existing_gearbox_data in existing_gearboxes.items():
                if existing_gearbox_data["gearbox_file"] == template_name:
                    templates.append(existing_gearbox_data)

    gearbox_variants = root.find("GearboxVariants")

    index = 0
    for gearbox in gearbox_variants.findall("Gearbox"):
        gearbox_data: dict = {}
        if len(templates) > 0:
            gearbox_data: dict = templates[index].copy()
            index += 1

        gearbox_data["id"] = f"{gearbox_file}_{gearbox.get('Name')}"
        gearbox_data["gearbox_file"] = gearbox_file
        gearbox_data["full_file"] = full_file
        awd_modifier = gearbox.get("AWDConsumptionModifier")
        if awd_modifier is not None:
            gearbox_data["awd_modifier"] = float(awd_modifier)

        critical_damage_threshold = gearbox.get("CriticalDamageThreshold")
        if critical_damage_threshold is not None:
            gearbox_data["critical_damage_threshold"] = float(critical_damage_threshold)

        damage_capacity = gearbox.get("DamageCapacity")
        if damage_capacity is not None:
            gearbox_data["damage_capacity"] = int(damage_capacity)

        fuel_consumption = gearbox.get("FuelConsumption")
        if fuel_consumption is not None:
            gearbox_data["fuel_consumption"] = float(fuel_consumption)

        idle_f = gearbox.get("IdleFuelModifier")
        if idle_f is not None:
            gearbox_data["idle_f"] = float(idle_f)

        game_data = gearbox.find("GameData")
        if game_data is not None:
            gearbox_data["price"] = int(game_data.get("Price"))
            gearbox_data["ui_desc_id"] = game_data.find("UiDesc").get("UiDesc")
            gearbox_ui_name = game_data.find("UiDesc").get("UiName")
            if gearbox_ui_name in ui_dict:
                gearbox_data["name"] = ui_dict[gearbox_ui_name]
            else:
                gearbox_data["name"] = gearbox_ui_name

        rev_gear = gearbox.find("ReverseGear")
        if rev_gear is not None:
            gearbox_data["rev_v"] = float(rev_gear.get("AngVel"))
            gearbox_data["rev_f"] = float(rev_gear.get("FuelModifier"))
        high_gear = gearbox.find("HighGear")
        if high_gear is not None:
            gearbox_data["high_v"] = float(high_gear.get("AngVel"))
            gearbox_data["high_f"] = float(high_gear.get(
                "FuelModifier"
            ))
        lowest_vel = 10.0
        highest_vel = 0.0
        gear_count = 0
        for gear in gearbox.findall("Gear"):
            gear_count += 1
            vel = float(gear.attrib["AngVel"])
            fuel_modifier = float(gear.attrib["FuelModifier"])
            if vel < lowest_vel:
                lowest_vel = vel
            if vel > highest_vel:
                highest_vel = vel
            gearbox_data[f"g{gear_count}_v"] = vel
            gearbox_data[f"g{gear_count}_f"] = fuel_modifier

        gearbox_data["gear_count"] = gear_count
        gearbox_data["lowest_v"] = lowest_vel
        gearbox_data["highest_v"] = highest_vel

        rets[gearbox_data["id"]] = gearbox_data

    return rets


def get_all_gearbox_data(use_initial_files, ui_dict: dict[str, str], input_folder: str):
    all_gearbox_data: dict[str, dict] = {}
    gearbox_folder = Path(utils.root_path, f"{input_folder}/initial/[media]/classes/gearboxes")
    mod_folder = Path(utils.root_path, "input/mods")
    dlc_folder = Path(utils.root_path, f"{input_folder}/initial/[media]/_dlc")

    # Iterate through all XML files in the folder
    for file_path in gearbox_folder.glob("*.xml"):
        all_gearbox_data.update(get_gearbox_data(file_path, use_initial_files, ui_dict))

    for file_path in mod_folder.glob("*/classes/gearboxes/*.xml"):
        all_gearbox_data.update(get_gearbox_data(file_path, True, ui_dict))

    for file_path in dlc_folder.glob(
        "dlc_*/classes/gearboxes/*.xml", case_sensitive=False
    ):
        all_gearbox_data.update(get_gearbox_data(file_path, use_initial_files, ui_dict, all_gearbox_data))

    return all_gearbox_data


def process_gearbox_data(use_initial_files, ui_dict: dict[str, str], input_folder: str) -> dict[str, dict]:
    gearbox_dict: dict[str, dict] = get_all_gearbox_data(use_initial_files, ui_dict, input_folder)
    addition = ""
    if not use_initial_files:
        addition = "_edited"
    with open(f"../reference/info/gearbox_data{addition}.json", "w", encoding="utf-8") as f:
        json.dump(gearbox_dict, f, indent=4)
    return gearbox_dict


def update_gearbox_data_with_truck_data(truck_dict: dict[str, dict], gearbox_dict: dict[str, dict]) -> dict[str, dict]:
    for gearbox_id, gearbox_data in gearbox_dict.items():
        trucks = []
        for truck_id, truck_data in truck_dict.items():
            if gearbox_data["gearbox_file"] in truck_data["gearbox_type"]:
                trucks.append(truck_data["name"])

        gearbox_dict[gearbox_id]["trucks"] = ", ".join(trucks)
    return gearbox_dict