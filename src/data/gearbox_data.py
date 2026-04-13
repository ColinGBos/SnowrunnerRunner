import json

from lxml import etree  # ty:ignore[unresolved-import]
from pathlib import Path
from statistics import mean

from src.utils import (
    get_modified_file_if_possible,
    find_regex_in,
    xml_result,
    find_sum_of_regex,
    xml_result_count,
    xml_result_list,
)


def get_gearbox_data(file_path: Path, use_initial_files: bool, ui_dict: dict[str, str]) -> dict[str, dict]:
    rets: dict[str, dict] = {}
    gearbox_file = file_path.stem
    contents = get_modified_file_if_possible(file_path, use_initial_files)

    parser = etree.XMLParser(recover=True)
    gearbox_variants = etree.fromstring(contents, parser=parser)
    for gearbox in gearbox_variants.findall("Gearbox"):
        gearbox_data: dict = {}
        gearbox_id = gearbox.get("Name")
        gearbox_data["id"] = gearbox_id
        gearbox_data["gearbox_file"] = gearbox_file
        gearbox_data["awd_modifier"] = float(gearbox.get("AWDConsumptionModifier"))
        gearbox_data["critical_damage_threshold"] = float(gearbox.get("CriticalDamageThreshold"))
        gearbox_data["damage_capacity"] = int(gearbox.get("DamageCapacity"))
        gearbox_data["fuel_consumption"] = float(gearbox.get("FuelConsumption"))
        gearbox_data["idle_f"] = float(gearbox.get("IdleFuelModifier"))
        gearbox_data["price"] = int(gearbox.find("GameData").get("Price"))
        gearbox_ui_name = gearbox.find("GameData").find("UiDesc").get("UiName")
        if gearbox_ui_name in ui_dict:
            gearbox_data["name"] = ui_dict[gearbox_ui_name]
        else:
            gearbox_data["name"] = gearbox_ui_name
        gearbox_data["rev_v"] = float(gearbox.find("ReverseGear").get("AngVel"))
        gearbox_data["rev_f"] = float(gearbox.find("ReverseGear").get("FuelModifier"))
        gearbox_data["high_v"] = float(gearbox.find("HighGear").get("AngVel"))
        gearbox_data["high_f"] = float(gearbox.find("HighGear").get(
            "FuelModifier"
        ))
        lowest_vel = 10.0
        highest_vel = 0.0
        gear_count = 1
        for gear in gearbox.findall("Gear"):
            vel = float(gear.attrib["AngVel"])
            fuel_modifier = float(gear.attrib["FuelModifier"])
            if vel < lowest_vel:
                lowest_vel = vel
            if vel > highest_vel:
                highest_vel = vel
            gearbox_data[f"g{gear_count}_v"] = vel
            gearbox_data[f"g{gear_count}_f"] = fuel_modifier

            gear_count += 1
        gearbox_data["lowest_v"] = lowest_vel
        gearbox_data["highest_v"] = highest_vel

        rets[f"{gearbox_file}-{gearbox_id}"] = gearbox_data

    return rets


def get_all_gearbox_data(use_initial_files, ui_dict: dict[str, str]):
    all_gearbox_data: dict[str, dict] = {}
    gearbox_folder = Path("input/initial/[media]/classes/gearboxes")
    dlc_folder = Path("input/initial/[media]/_dlc")

    # Iterate through all XML files in the folder
    for file_path in gearbox_folder.glob("*.xml"):
        all_gearbox_data.update(get_gearbox_data(file_path, use_initial_files, ui_dict))

    for file_path in dlc_folder.glob(
        "dlc_*/classes/gearboxes/*.xml", case_sensitive=False
    ):
        all_gearbox_data.update(get_gearbox_data(file_path, use_initial_files, ui_dict))

    return all_gearbox_data


def process_gearbox_data(use_initial_files, ui_dict: dict[str, str]) -> dict[str, dict]:
    gearbox_dict: dict[str, dict] = get_all_gearbox_data(use_initial_files, ui_dict)
    addition = ""
    if not use_initial_files:
        addition = "_edited"
    with open(f"reference/info/gearbox_data{addition}.json", "w", encoding="utf-8") as f:
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