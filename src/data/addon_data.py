import json

from pathlib import Path

import utils
from src.utils import (
    get_modified_file_if_possible,
    find_regex_in,
    xml_result,
    find_sum_of_regex,
)

def update_addon_name(install_socket:str, name:str, truck_data:dict[str, dict]) -> str:
    socket_users:list[str] = []
    for _, truck in truck_data.items():
        if install_socket in truck["addon_sockets"]:
            socket_users.append(truck["name"])
    if len(socket_users) == 1:
        return f"{name} ({socket_users[0]})"
    return name


def get_addon_data(file_path, use_initial_files, truck_data:dict[str,dict], ui_dict: dict[str, str]) -> tuple[str, dict]:
    addon_id = file_path.stem
    addon_data: dict = {}
    contents = get_modified_file_if_possible(file_path, use_initial_files)

    addon_name_id: str = str(find_regex_in(contents, "UiName=", "str"))
    if addon_name_id in ui_dict:
        addon_name: str = ui_dict[addon_name_id]
    else:
        return "None", {}
    addon_data["name"] = addon_name
    addon_data["addon_name_id"] = addon_name_id
    addon_data["id"] = addon_id

    addon_mass = find_sum_of_regex(contents, "Mass=", "int")
    worth_adding=False
    if "crane" in addon_name.lower():
        worth_adding=True
    fuel_capacity = xml_result(
        contents, True, ["TruckAddon", "TruckData", "FuelCapacity"], "int"
    )
    if fuel_capacity is not None and int(fuel_capacity) > 0:
        addon_data["fuel_capacity"] = fuel_capacity
        fuel_mass = xml_result(contents, True, ["TruckAddon", "FuelMass", "Body", "Mass"], "int")
        if fuel_mass is not None:
            if addon_mass is not None:
                main_body_mass = xml_result(contents, True, ["TruckAddon", "PhysicsModel", "Body", "Mass"], "int")
                if main_body_mass is not None:
                    addon_data["full_mass"] = int(addon_mass) - int(main_body_mass)
                addon_mass -= int(fuel_mass)
        worth_adding=True
    water_capacity = xml_result(
        contents, True, ["TruckAddon", "TruckData", "WaterCapacity"], "int"
    )
    if water_capacity is not None and int(water_capacity) > 0:
        addon_data["water_capacity"] = water_capacity
        water_mass = xml_result(contents, True, ["TruckAddon", "WaterMass", "Body", "Mass"], "int")
        if water_mass is not None:
            if addon_mass is not None:
                main_body_mass = xml_result(contents, True, ["TruckAddon", "PhysicsModel", "Body", "Mass"], "int")
                if main_body_mass is not None:
                    addon_data["full_mass"] = int(addon_mass) - int(main_body_mass)
                addon_mass -= int(water_mass)
        worth_adding = True

    repair_capacity = xml_result(
        contents, True, ["TruckAddon", "TruckData", "RepairsCapacity"], "int"
    )
    if repair_capacity is not None and int(repair_capacity) > 0:
        addon_data["repair_capacity"] = repair_capacity
        worth_adding = True
    spare_wheels = xml_result(
        contents, True, ["TruckAddon", "TruckData", "WheelRepairsCapacity"], "int"
    )
    if spare_wheels is not None and int(spare_wheels) > 0:
        addon_data["spare_wheels"] = spare_wheels
        worth_adding = True
    cargo_slots = xml_result(
        contents, True, ["TruckAddon", "GameData", "AddonSlots", "Quantity"], "int"
    )
    if cargo_slots is not None:
        addon_data["cargo_slots"] = int(cargo_slots)
        worth_adding = True
    addon_data["price"] = xml_result(
        contents, True, ["TruckAddon", "GameData", "Price"], "int"
    )
    install_socket = xml_result(
        contents, True, ["TruckAddon", "GameData", "InstallSocket", "Type"], "str"
    )
    if install_socket is not None:
        addon_data["install_socket"] = install_socket
        addon_data["name"] = update_addon_name(str(install_socket), addon_data["name"], truck_data)
    if addon_mass is not None:
        addon_data["mass"] = int(addon_mass)
    if not worth_adding:
        return "None", {}
    return addon_id, addon_data


def get_all_addon_data(use_initial_files, truck_data:dict[str,dict], ui_dict: dict[str, str], input_folder: str) -> dict[str, dict]:
    all_addon_data: dict[str, dict] = {}
    truck_folder = Path(utils.root_path, f"{input_folder}/initial/[media]/classes/trucks")
    mod_folder = Path(utils.root_path, "input/mods")
    dlc_folder = Path(utils.root_path, f"{input_folder}/initial/[media]/_dlc")

    for file_path in truck_folder.glob("addons/*.xml"):
        addon_name, addon_data = get_addon_data(
            file_path, use_initial_files, truck_data, ui_dict
        )
        if addon_name != "None":
            all_addon_data[addon_name] = addon_data

    for file_path in mod_folder.glob("*/classes/addons/*.xml"):
        addon_name, addon_data = get_addon_data(
            file_path, True, truck_data, ui_dict
        )
        if addon_name != "None":
            all_addon_data[addon_name] = addon_data

    for file_path in truck_folder.glob("*_tuning/*.xml"):
        addon_name, addon_data = get_addon_data(
            file_path, use_initial_files, truck_data, ui_dict
        )
        if addon_name != "None":
            all_addon_data[addon_name] = addon_data

    for file_path in dlc_folder.glob(
        "dlc_*/classes/trucks/addons/*.xml", case_sensitive=False
    ):
        addon_name, addon_data = get_addon_data(
            file_path, use_initial_files, truck_data, ui_dict
        )
        if addon_name != "None":
            all_addon_data[addon_name] = addon_data

    for file_path in dlc_folder.glob(
        "dlc_*/classes/trucks/*_tuning/*.xml", case_sensitive=False
    ):
        addon_name, addon_data = get_addon_data(
            file_path, use_initial_files, truck_data, ui_dict
        )
        if addon_name != "None":
            all_addon_data[addon_name] = addon_data

    for file_path in dlc_folder.glob(
        "dlc_*/classes/trucks/*_tunning/*.xml", case_sensitive=False
    ):
        addon_name, addon_data = get_addon_data(
            file_path, use_initial_files, truck_data, ui_dict
        )
        if addon_name != "None":
            all_addon_data[addon_name] = addon_data

    return all_addon_data


def process_addon_data(use_initial_files, truck_data:dict[str, dict],ui_dict: dict[str, str], input_folder: str) -> dict[str, dict]:
    data_dict: dict[str, dict] = get_all_addon_data(use_initial_files, truck_data, ui_dict, input_folder)
    addition = ""
    if not use_initial_files:
        addition = "_edited"
    with open(f"../reference/info/addon_data{addition}.json", "w", encoding="utf-8") as f:
        json.dump(data_dict, f, indent=4)
    return data_dict
