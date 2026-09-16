import json

from pathlib import Path

import utils
from src.utils import (
    get_modified_file_if_possible,
    find_regex_in,
    xml_result,
    find_sum_of_regex,
)


def get_trailer_data(file_path, use_initial_files, ui_dict: dict[str, str]) -> tuple[str, dict]:
    trailer_id = file_path.stem
    trailer_data: dict = {}
    contents = get_modified_file_if_possible(file_path, use_initial_files)

    trailer_name_id: str = str(find_regex_in(contents, "UiName=", "str"))
    if trailer_name_id in ui_dict:
        trailer_data["name"] = ui_dict[trailer_name_id]
    else:
        trailer_data["name"] = trailer_name_id
    trailer_data["trailer_name_id"] = trailer_name_id
    trailer_data["id"] = trailer_id
    addon_mass = find_sum_of_regex(contents, "Mass=", "int")
    fuel_capacity = xml_result(
        contents, True, ["Truck", "TruckData", "FuelCapacity"], "int"
    )
    if fuel_capacity is not None and int(fuel_capacity) > 0:
        trailer_data["fuel_capacity"] = fuel_capacity
        fuel_mass = xml_result(contents, True, ["Truck", "FuelMass", "Body", "Mass"], "int")
        if fuel_mass is not None:
            if addon_mass is not None:
                main_body_mass = xml_result(contents, True, ["Truck", "PhysicsModel", "Body", "Mass"], "int")
                if main_body_mass is not None:
                    trailer_data["full_mass"] = int(addon_mass) - int(main_body_mass)
                addon_mass -= int(fuel_mass)


    water_capacity = xml_result(
        contents, True, ["Truck", "TruckData", "WaterCapacity"], "int"
    )
    if water_capacity is not None and int(water_capacity) > 0:
        trailer_data["water_capacity"] = water_capacity
        water_mass = xml_result(contents, True, ["Truck", "WaterMass", "Body", "Mass"], "int")
        if water_mass is not None:
            if addon_mass is not None:
                main_body_mass = xml_result(contents, True, ["Truck", "PhysicsModel", "Body", "Mass"], "int")
                if main_body_mass is not None:
                    trailer_data["full_mass"] = int(addon_mass) - int(main_body_mass)
                addon_mass -= int(water_mass)

    repair_capacity = xml_result(
        contents, True, ["Truck", "TruckData", "RepairsCapacity"], "int"
    )
    if repair_capacity is not None and int(repair_capacity) > 0:
        trailer_data["repair_capacity"] = repair_capacity
    spare_wheels = xml_result(
        contents, True, ["Truck", "TruckData", "WheelRepairsCapacity"], "int"
    )
    if spare_wheels is not None and int(spare_wheels) > 0:
        trailer_data["spare_wheels"] = spare_wheels
    cargo_slots = xml_result(
        contents, True, ["Truck", "GameData", "AddonSlots", "Quantity"], "int"
    )
    if cargo_slots is not None:
        trailer_data["cargo_slots"] = int(cargo_slots)
    if addon_mass is not None:
        trailer_data["mass"] = int(addon_mass)
    trailer_data["price"] = xml_result(
        contents, True, ["Truck", "GameData", "Price"], "int"
    )
    trailer_data["trailer_type"] = xml_result(
        contents, True, ["Truck", "GameData", "InstallSocket", "Type"], "str"
    )

    return trailer_id, trailer_data


def get_all_trailer_data(use_initial_files, ui_dict: dict[str, str], input_folder: str) -> dict[str, dict]:
    all_trailer_data: dict[str, dict] = {}
    trailer_folder = Path(utils.root_path, f"{input_folder}/initial/[media]/classes/trucks/trailers")
    mod_folder = Path(utils.root_path, "input/mods")
    dlc_folder = Path(utils.root_path, f"{input_folder}/initial/[media]/_dlc")

    # Iterate through all XML files in the folder
    for file_path in trailer_folder.glob("*.xml"):
        trailer_name, trailer_data = get_trailer_data(
            file_path, use_initial_files, ui_dict
        )
        all_trailer_data[trailer_name] = trailer_data

    for file_path in mod_folder.glob("*/classes/trucks/trailers/*.xml"):
        trailer_name, trailer_data = get_trailer_data(
            file_path, True, ui_dict
        )
        all_trailer_data[trailer_name] = trailer_data

    for file_path in dlc_folder.glob(
        "dlc_*/classes/trucks/trailers/*.xml", case_sensitive=False
    ):
        trailer_name, trailer_data = get_trailer_data(
            file_path, use_initial_files, ui_dict
        )
        all_trailer_data[trailer_name] = trailer_data
    return all_trailer_data


def process_trailer_data(use_initial_files, ui_dict: dict[str, str], input_folder: str):
    data_dict: dict[str, dict] = get_all_trailer_data(use_initial_files, ui_dict, input_folder)
    addition = ""
    if not use_initial_files:
        addition = "_edited"
    with open(f"../reference/info/trailer_data{addition}.json", "w", encoding="utf-8") as f:
        json.dump(data_dict, f, indent=4)
    return data_dict