from typing import Any
import json

from lxml import etree  # ty:ignore[unresolved-import]
from pathlib import Path
from statistics import mean

import utils
from src.utils import (
    get_modified_file_if_possible,
    find_regex_in,
    xml_result,
    find_sum_of_regex,
    xml_result_count,
    xml_result_list,
)


def add_steering_info(contents: str, truck_data: dict, front_wheel: str) -> dict:
    steering_angle_1 = xml_result(contents, True, ["_templates", "Wheel", front_wheel, "SteeringAngle"], "float")
    if steering_angle_1 is not None:
        truck_data["steering_angle_1"] = steering_angle_1
    wrapped_xml_data = f"<fake_root>{contents}</fake_root>"
    parser = etree.XMLParser(recover=True)
    root = etree.fromstring(wrapped_xml_data, parser=parser)
    templates = root.find("_templates")
    if templates is not None:
        wheel_templates = templates.find("Wheel")
        if wheel_templates is not None:
            for wheel in wheel_templates:
                if wheel.tag != front_wheel:
                    if wheel.get("SteeringAngle") is not None:
                        truck_data["steering_angle_2"] = float(wheel.get("SteeringAngle"))

    return truck_data


def get_gearbox_options(gearbox_dict, gearbox_files) -> list[str]:
    gearbox_options: list[str] = []
    for _, gearbox_data in gearbox_dict.items():
        if gearbox_data["gearbox_file"] in gearbox_files:
            gearbox_options.append(gearbox_data["name"])

    return gearbox_options


def get_awd_status(contents, front_wheel, truck_name) -> str:
    front_torque:str = str(xml_result(
        contents, True, ["_templates", "Wheel", front_wheel, "Torque"], "str"
    )).lower()
    if front_torque.lower() == "default":
        return "Always"
    elif front_torque == "full" or front_torque == "connectable":
        return "Capable"
    elif front_torque == "none":
        return "None"
    else:
        print(f"AWD type {front_torque} from {truck_name} not recognized")
        return "None"


def get_dead_axle_status(contents) -> bool:
    if "<MiddleAxle" in contents:
        middle_axle = xml_result(
            contents, True, ["_templates", "Wheel", "MiddleAxle", "Torque"], "str"
        )
        if middle_axle == "none":
            return True
    return False


def get_difflock_status(contents, truck_id) -> str:
    manual_difflock = {
        "kirovets_k700": "Switchable",
        "kirovets_k7m": "Switchable",
        "derry_special_15c177": "Switchable",
        "zikz_566a": "Switchable",
        "navistar_5000mv": "None",
        "royal_bm17": "None",
        "western_star_57x": "None",
        "western_star_nf1430": "None",
        "gmc_8000": "Switchable",
    }
    if truck_id in manual_difflock:
        return manual_difflock[truck_id]
    diff_lock = xml_result(
        contents, True, ["Truck", "TruckData", "DiffLockType"], "str"
    )
    if diff_lock == "Always":
        return "Always"
    elif diff_lock == "None":
        return "None"
    else:
        trucks_folder = Path(utils.root_path, "input/initial/[media]/classes/trucks")
        dlc_folder = Path(utils.root_path, "input/initial/[media]/_dlc")
        if Path(f"{trucks_folder}/{truck_id}_tuning").exists():
            for dest in Path(f"{trucks_folder}/{truck_id}_tuning").glob("*diff*"):
                if "diff_lock" or "difflock" in str(dest):
                    return "Switchable"

        for file_path in dlc_folder.glob(
            "dlc_*/classes/trucks", case_sensitive=False
        ):
            if Path(f"{file_path}/{truck_id}_tuning").exists():
                for dest in Path(f"{file_path}/{truck_id}_tuning").glob("*diff*"):
                    if "diff_lock" or "difflock" in str(dest):
                        return "Switchable"
    print(f"Difflock type {diff_lock} for {truck_id} not recognized")
    return "None"


def get_saddle_height(socket, contents, wheel_max_size: float, max_rear_sus_height:float) -> float:
    wrapped_xml_data = f"<fake_root>{contents}</fake_root>"
    parser = etree.XMLParser(recover=True)
    root = etree.fromstring(wrapped_xml_data, parser=parser)
    wheels = root.find("Truck").find("TruckData").find("Wheels").findall("Wheel")
    wheel_y_offset = float(wheels[-1].get("Pos").split("; ")[1].replace(";", "").strip())
    saddle_y_offset = float(socket.get("Offset").split("; ")[1].replace(";", "").strip())
    return saddle_y_offset - wheel_y_offset + wheel_max_size * 0.0125 + max_rear_sus_height


def update_trucks_with_cargo_slots(truck_data: dict[str,dict], addon_data: dict[str, dict]) -> dict[str,dict]:
    for truck_name, truck_info in truck_data.items():
        cargo_slots = 0
        if "cargo_slots" in truck_info:
            cargo_slots = truck_info["cargo_slots"]
        for _, addon_info in addon_data.items():
            if "install_socket" in addon_info and addon_info["install_socket"] in truck_info["addon_sockets"]:
                if "cargo_slots" in addon_info and addon_info["cargo_slots"] > cargo_slots:
                    cargo_slots = addon_info["cargo_slots"]
        truck_data[truck_name]["cargo_slots"] = cargo_slots

    return truck_data


def add_addon_info(contents: str, truck_data: dict) -> dict:
    addon_dict: dict[str, dict[str, list[str] | bool]] = {
        "LargeSemitrailer": {"addons": ["High Saddle"], "use_partial_matches": True},
        "HeavySemitrailer": {"addons": ["High Saddle"], "use_partial_matches": True},
        "LargeSemitrailerOiltank": {
            "addons": ["High Saddle"],
            "use_partial_matches": True,
        },
        "Semitrailer": {"addons": ["Low Saddle"], "use_partial_matches": False},
        "SemitrailerOiltank": {"addons": ["Low Saddle"], "use_partial_matches": False},
        "SaddleLow": {"addons": ["Low Saddle"], "use_partial_matches": True},
        "SaddleHigh": {"addons": ["High Saddle"], "use_partial_matches": True},
        "FrameAddonTow": {"addons": ["Truck Trailer"], "use_partial_matches": True},
        "Trailer": {"addons": ["Truck Trailer"], "use_partial_matches": False},
        "ScautTrailer": {"addons": ["Scout Trailer"], "use_partial_matches": True},
        "SeismicVibrator": {
            "addons": ["Seismic Vibrator"],
            "use_partial_matches": True,
        },
        "MetalDetector": {"addons": ["Metal Detector"], "use_partial_matches": True},
        "RepairSmall": {"addons": ["Repair Supplies"], "use_partial_matches": True},
        "RepairKit": {"addons": ["Repair Supplies"], "use_partial_matches": True},
        "HeavyRepair": {"addons": ["Repair Supplies"], "use_partial_matches": True},
        "Supplies": {"addons": ["Repair Supplies"], "use_partial_matches": True},
        "RoofRrack": {"addons": ["Repair Supplies"], "use_partial_matches": True},
        "Roofrack": {"addons": ["Repair Supplies"], "use_partial_matches": True},
        "RepairBox": {"addons": ["Repair Supplies"], "use_partial_matches": True},
        "LogShort": {"addons": ["Short Logs"], "use_partial_matches": True},
        "LogMedium": {"addons": ["Medium Logs"], "use_partial_matches": True},
        "LogsShort": {"addons": ["Short Logs"], "use_partial_matches": True},
        "LogsMedium": {"addons": ["Medium Logs"], "use_partial_matches": True},
        "WaterTank": {"addons": ["Water Tank"], "use_partial_matches": True},
        "FuelTank": {"addons": ["Fuel Tank"], "use_partial_matches": True},
        "FrameAddonTank": {
            "addons": ["Fuel Tank", "Water Tank"],
            "use_partial_matches": True,
        },
        "FrameAddonTankLong": {
            "addons": ["Extended Fuel Tank", "Extended Water Tank"],
            "use_partial_matches": False,
        },
        "Minicrane": {"addons": ["Minicrane"], "use_partial_matches": True},
        "TatraCrane": {"addons": ["Minicrane"], "use_partial_matches": True},
        "ChimeraCrane": {"addons": ["Minicrane"], "use_partial_matches": True},
        "CraneSleiter": {"addons": ["Minicrane"], "use_partial_matches": True},
        "BigCrane": {"addons": ["Heavy Crane"], "use_partial_matches": True},
        "LogLift": {"addons": ["Log Crane"], "use_partial_matches": True},
        "BunkLog": {"addons": ["Long Logs"], "use_partial_matches": True},
        "LogBunk": {"addons": ["Long Logs"], "use_partial_matches": True},
        "LogTrailer": {"addons": ["Futom Trailer"], "use_partial_matches": False},
        "FrameAddonMaintainer": {
            "addons": ["Maintainer Frame"],
            "use_partial_matches": True,
        },
        "FrameAddonMaintainerBig": {
            "addons": ["Big Maintainer Frame"],
            "use_partial_matches": True,
        },
        "Kung": {"addons": ["Van Body"], "use_partial_matches": True},
        "ServiceBody": {"addons": ["Van Body"], "use_partial_matches": True},
        "FrameAddonTowPlatform": {
            "addons": ["Tow Platform"],
            "use_partial_matches": True,
        },
        "SemitrailerFoldableLog": {
            "addons": ["HydroLift Saddle"],
            "use_partial_matches": True,
        },
    }
    ignore_list = [
        "bumper",
        "farkop",
        "wings",
        "sticker",
        "visor",
        "fender",
        "airfilter",
        "lights",
        "headlamp",
        "exhaust",
        "horn",
        "wheel",
        "protector",
        "protection",
        "threshold",
        "searchlight",
        "gabarite",
        "motorized",
        "difflock",
        "snorkel",
        "beacon",
        "spotlight",
        "hood",
        "conditioner",
        "transferbox",
    ]
    wrapped_xml_data = f"<fake_root>{contents}</fake_root>"
    parser = etree.XMLParser(recover=True)
    root = etree.fromstring(wrapped_xml_data, parser=parser)
    game_data = root.find("Truck").find("GameData")
    addon_sockets = game_data.findall("AddonSockets")
    known_sockets = []
    for addon_socket_set in addon_sockets:
        for socket in addon_socket_set.findall("Socket"):
            socket_names = socket.get("Names")
            in_cockpit = socket.get("InCockpit")
            ignore = False
            for ignore_name in ignore_list:
                if ignore_name in socket_names.lower():
                    ignore = True
            if socket_names is not None and in_cockpit is None and not ignore:
                for socket_name in socket_names.split(", "):
                    known_sockets.append(socket_name)
                    for addon_type, addon_data in addon_dict.items():
                        if addon_type == socket_name or (
                            addon_data["use_partial_matches"]
                            and addon_type.lower() in socket_name.lower()
                        ):
                            if addon_type == "Semitrailer":
                                truck_data["low_saddle_height"] = get_saddle_height(
                                    socket,
                                    contents,
                                    truck_data["max_wheel_size"],
                                    truck_data["max_rear_sus_height"],
                                )
                            elif addon_type == "LargeSemitrailer":
                                truck_data["high_saddle_height"] = get_saddle_height(
                                    socket,
                                    contents,
                                    truck_data["max_wheel_size"],
                                    truck_data["max_rear_sus_height"],
                                )
                            if isinstance(addon_data["addons"], list):
                                for addon_name in addon_data["addons"]:
                                    truck_data[addon_name.lower().replace(" ", "_")] = (
                                        True
                                    )
    truck_data["addon_sockets"] = known_sockets

    return truck_data


def get_max_wheel_mass(wheel_types, wheel_dict) -> int:
    wheel_mass = 0
    for wheel_type in wheel_types:
        for wheel_data in wheel_dict.values():
            if wheel_data["file"] == wheel_type and wheel_data["Mass"] > wheel_mass:
                wheel_mass = wheel_data["Mass"]
    return wheel_mass


def calculate_pulling_quotient(
    truck_name: str,
    torque: float,
    wheel_size: float,
    drive_wheel_count: int,
    difflock,
    awd,
    mass: int,
    dead_axle: bool,
    has_doubles: bool,
):
    q = torque / (mass + 15000)
    bonus = 1.0
    if has_doubles:
        bonus *= 1.15
    if difflock == "Always":
        bonus *= 1.2
    elif difflock == "Switchable":
        bonus *= 1.125
    if awd != "None":
        bonus *= 1.2
    elif awd == "None":
        bonus *= 0.8
    bonus += 25 / (90 - wheel_size)
    if drive_wheel_count <= 4:
        bonus -= 0.1
    else:
        bonus += drive_wheel_count * 0.05
    if dead_axle:
        bonus -= 0.25

    q = q * bonus
    return round(q, 2)


def get_front_wheel(contents: str, truck_name: str) -> str:
    front_wheel_names = [
        "FirstAxle",
        "Front",
        "First",
        "FirstWheel",
        "FrontWheel",
        "FrontAxle",
    ]
    wrapped_xml_data = f"<fake_root>{contents}</fake_root>"
    parser = etree.XMLParser(recover=True)
    root = etree.fromstring(wrapped_xml_data, parser=parser)
    templates = root.find("_templates")
    if templates is not None and templates.find("Wheel") is not None:
        wheels = templates.find("Wheel")
    else:
        wheels = root.find("Truck").find("TruckData").find("Wheels")
    wheel_names = [wheel.tag for wheel in wheels]
    for wheel_name in wheel_names:
        if wheel_name in front_wheel_names:
            return wheel_name
    for wheel in wheels:
        if wheel.get("Location").lower() == "front":
            return wheel.tag
    print(f"No front wheel found for {truck_name}, wheel names: {wheel_names}")
    return "None"


def get_drive_wheel_count(contents, truck_name) -> int:
    wrapped_xml_data = f"<fake_root>{contents}</fake_root>"
    parser = etree.XMLParser(recover=True)
    root = etree.fromstring(wrapped_xml_data, parser=parser)
    templates = root.find("_templates")
    if templates is not None:
        wheel_templates = templates.find("Wheel")
        if wheel_templates is not None:
            drive_flags = ["default", "full", "connectable"]
            powered_template = []
            for wheel in wheel_templates:
                template = wheel.get("_template")
                if template is not None:
                    torque = wheel_templates.find(template).get("Torque")
                else:
                    torque = wheel.get("Torque")
                if torque is not None and torque.lower() in drive_flags:
                    powered_template.append(wheel.tag)
            count = 0
            wheels = root.find("Truck").find("TruckData").find("Wheels").findall("Wheel")
            for wheel in wheels:
                if wheel.get("_template") in powered_template:
                    count += 1
            return count
    return 0


def get_truck_has_doubles(wheel_types, truck_name):
    if wheel_types is not None:
        for wheel_type in wheel_types:
            if "double" in str(wheel_type).lower():
                return True
    return False


def get_dlc_from_file_path(file_path: Path) -> str:
    dlc_dict = {
        "1_1": "Kola Peninsula",
        "1_2": "Kola Peninsula",
        "2_1": "Yukon",
        "2_2": "Yukon",
        "3": "Wisconsin",
        "4": "Amur",
        "4_1": "Anniversary Pack (Free)",
        "5": "Don",
        "6": "Maine",
        "7": "Tennessee",
        "8": "Belozersk Glades",
        "9": "Ontario",
        "10": "British Columbia",
        "11": "Scandinavia",
        "12": "North Carolina",
        "13": "Almaty",
        "14": "Austria",
        "15": "Quebec",
        "16": "Washington",
        "17": "Zurdania",
    }
    if "_dlc" in str(file_path).lower():
        return "DLC"
    if "mods" in str(file_path).lower():
        return "Mod"
    return "Base Game"


def get_avg_gearbox_info(
    gearbox_dict: dict[str, dict[str,Any]], gearbox_files: list[str]
) -> tuple[float, float, float]:
    consumptions = []
    high_vels = []
    awd_modifiers = []
    for _, gearbox_data in gearbox_dict.items():
        if gearbox_data["gearbox_file"] in gearbox_files:
            # if "offroad" in gearbox_data["id"].lower():
            high_vels.append(gearbox_data["high_v"])
            awd_modifiers.append(gearbox_data["awd_modifier"])
            base_fuel_consumption = gearbox_data["fuel_consumption"]
            high_fuel_consumption = gearbox_data["high_f"]
            gears_fuel = []
            for i in range(1, 9):
                if f"g{i}_f" in gearbox_data:
                    gears_fuel.append(gearbox_data[f"g{i}_f"])
            consumptions.append(mean([high_fuel_consumption, mean(gears_fuel)]) * base_fuel_consumption)
    if len(consumptions) > 0 and len(high_vels) > 0 and len(awd_modifiers) > 0:
        return mean(consumptions), mean(high_vels), mean(awd_modifiers)
    return 0.0, 0.0, 0.0


def get_max_rear_suspension_height(
    suspension_types: str, suspension_dict: dict[str, dict]
) -> float:
    max_height = 0.0
    for _, suspension_data in suspension_dict.items():
        if suspension_data["suspension_file"] in suspension_types:
            if suspension_data["rear_max_height"] > max_height:
                max_height = suspension_data["rear_max_height"]
    return max_height


def get_engine_torques(
    engine_dict: dict[str, dict], engine_types: list[str]
) -> list[int]:
    engine_torques: list[int] = []
    for _, engine_data in engine_dict.items():
        if engine_data["engine_file"] in engine_types:
            engine_torques.append(int(engine_data["torque"]))
    return engine_torques


def get_max_engine_fuel(
    engine_dict: dict[str, dict], engine_types: list[str]
) -> float:
    engine_fuel: float = 0
    for _, engine_data in engine_dict.items():
        if engine_data["engine_file"] in engine_types:
            if engine_data["fuel_consumption"] > engine_fuel:
                engine_fuel = engine_data["fuel_consumption"]
    return engine_fuel


def clean_name(name:str):
    return name.replace("'", '"').replace("“", '"').replace("”",'"').replace("\\",'')


def get_truck_data(
    file_path: Path,
    use_initial_files: bool,
    engine_dict: dict[str, dict],
    gearbox_dict: dict[str, dict],
    wheel_dict: dict[str, dict],
    sus_dict: dict[str, dict],
    ui_dict: dict[str, str],
) -> tuple[str, dict]:
    truck_id = file_path.stem
    print(f"Processing {truck_id}")
    truck_data: dict = {}
    contents = get_modified_file_if_possible(file_path, use_initial_files)

    truck_name: str = str(xml_result(
        contents, True, ["Truck", "GameData", "UiDesc", "UiName"], "str"
    ))
    if truck_name == "" or truck_name == "None":
        truck_name = str(find_regex_in(contents, "UiName=", "str"))
    if truck_name in ui_dict:
        truck_data["name"] = clean_name(ui_dict[truck_name])
    elif truck_name != "" and truck_name != "None":
        print(f"No Ui Lang found for {truck_name}, using file name")
        truck_data["name"] = truck_name
    else:
        truck_data["name"] = truck_id
    truck_data["id"] = truck_id
    truck_data["dlc"] = get_dlc_from_file_path(file_path)
    truck_data["class"] = xml_result(
        contents, True, ["Truck", "TruckData", "TruckType"], "str"
    )
    fuel_capacity = xml_result(
        contents, True, ["Truck", "TruckData", "FuelCapacity"], "int"
    )
    if fuel_capacity is not None:
        fuel_capacity = int(fuel_capacity)
    truck_data["fuel_capacity"] = fuel_capacity
    truck_mass = find_sum_of_regex(contents, "Mass=", "int")
    if truck_mass is not None:
        truck_data["mass"] = int(truck_mass)
    truck_data["price"] = xml_result(
        contents, True, ["Truck", "GameData", "Price"], "int"
    )
    truck_data["region"] = xml_result(
        contents, True, ["Truck", "GameData", "Country"], "str"
    )
    requires_exploration = xml_result(
        contents, True, ["Truck", "GameData", "UnlockByExploration"], "bool"
    )
    if requires_exploration:
        truck_data["requires_exploration"] = True
    truck_data["unlock_rank"] = xml_result(
        contents, True, ["Truck", "GameData", "UnlockByRank"], "int"
    )
    front_wheel = get_front_wheel(contents, truck_name)
    truck_data["awd"] = get_awd_status(contents, front_wheel, truck_name)
    desc_ui_id = xml_result(
        contents, True, ["Truck", "GameData", "UiDesc", "UiDesc"], "str"
    )
    truck_data["desc_ui_id"] = desc_ui_id
    has_dead_axel: bool = get_dead_axle_status(contents)
    if has_dead_axel:
        truck_data["dead_axle"] = True
    truck_data["difflock"] = get_difflock_status(contents, truck_id)
    truck_data = add_steering_info(contents, truck_data, front_wheel)
    truck_data["steer_speed"] = xml_result(
        contents, True, ["Truck", "TruckData", "SteerSpeed"], "float"
    )
    truck_data["back_steer_speed"] = xml_result(
        contents, True, ["Truck", "TruckData", "BackSteerSpeed"], "float"
    )
    truck_data["responsiveness"] = xml_result(
        contents, True, ["Truck", "TruckData", "Responsiveness"], "float"
    )
    truck_data["engine_start_delay"] = xml_result(
        contents, True, ["Truck", "TruckData", "EngineStartDelay"], "float"
    )
    truck_data["wheel_count"] = xml_result_count(
        contents, True, ["Truck", "TruckData", "Wheels", "Wheel"]
    )
    truck_data["drive_wheel_count"] = get_drive_wheel_count(contents, truck_name)
    wheel_sizes = xml_result_list(
        contents, True, ["Truck", "TruckData", "CompatibleWheels", "Scale"], "float"
    )
    max_wheel_size = 0.0
    if wheel_sizes is not None:
        wheel_sizes = [round(float(size) * 2.0 * 39.37008, 1) for size in wheel_sizes]
        truck_data["min_wheel_size"] = min(wheel_sizes)
        max_wheel_size = max(wheel_sizes)
        truck_data["max_wheel_size"] = max_wheel_size
    wheel_types = xml_result_list(
        contents, True, ["Truck", "TruckData", "CompatibleWheels", "Type"], "str"
    )
    max_wheel_mass = 100
    has_doubles = False
    if wheel_types is not None:
        truck_data["wheel_types"] = wheel_types
        has_doubles = get_truck_has_doubles(wheel_types, truck_name)
        if has_doubles:
            truck_data["has_doubles"] = True
        max_wheel_mass = get_max_wheel_mass(wheel_types, wheel_dict)
        truck_data["max_wheel_mass"] = max_wheel_mass
    truck_data["engine_default"] = xml_result(
        contents, True, ["Truck", "TruckData", "EngineSocket", "Default"], "str"
    )
    engine_types = xml_result(
        contents, True, ["Truck", "TruckData", "EngineSocket", "Type"], "str"
    )
    cargo_slots = xml_result(
        contents, True, ["Truck", "GameData", "AddonSlots", "Quantity"], "int"
    )
    if cargo_slots is not None:
        truck_data["cargo_slots"] = int(cargo_slots)
    engine_fuel: float = 0.0
    if engine_types is not None and isinstance(engine_types, str):
        engine_files = engine_types.split(", ")
        truck_data["engine_types"] = engine_files
        engine_torques: list[int] = get_engine_torques(engine_dict, engine_files)
        engine_fuel = get_max_engine_fuel(engine_dict, engine_files)
        truck_data["min_engine_torque"] = min(engine_torques)
        max_torque = max(engine_torques)
        truck_data["max_engine_torque"] = max_torque
        if max_torque > 0 and truck_mass is not None:
            wheel_multiplier = ((((max_wheel_mass**0.5) * 2) ** 0.5) + 1) / 6.0
            adj_torque = int(round(max_torque * wheel_multiplier, -2))
            truck_data["pure_p/w"] = round(max_torque / truck_mass, 2)
            truck_data["adj_p/w"] = round(adj_torque / truck_mass, 2)
            truck_data["adj_p/w+"] = round(adj_torque / (truck_mass + 5000), 2)
            truck_data["adj_p/w++"] = round(adj_torque / (truck_mass + 15000), 2)
            truck_data["wheel_adj_power"] = adj_torque
    gearbox_type = xml_result(
        contents, True, ["Truck", "TruckData", "GearboxSocket", "Type"], "str"
    )
    gearbox_fuel: float = 0.0
    high_vel: float = 0.0
    awd_modifier: float = 0.0
    if gearbox_type is not None and isinstance(gearbox_type, str):
        gearbox_files = gearbox_type.split(", ")
        truck_data["gearbox_type"] = gearbox_files
        gearbox_options = get_gearbox_options(gearbox_dict, gearbox_files)
        gearbox_fuel, high_vel, awd_modifier = get_avg_gearbox_info(gearbox_dict, gearbox_files)
        truck_data["gearbox_options"] = gearbox_options

    truck_data["gearbox_default"] = xml_result(
        contents, True, ["Truck", "TruckData", "GearboxSocket", "Default"], "str"
    )

    if high_vel > 0 and max_wheel_size > 0:
        truck_data["avg_high_speed"] = round(0.0585 * max_wheel_size * high_vel, 1)

    net_fuel_consumption = engine_fuel * gearbox_fuel
    if awd_modifier > 0 and truck_data["awd"] is not None and truck_data["awd"] == "Always":
        net_fuel_consumption *= awd_modifier
    if net_fuel_consumption > 0 and fuel_capacity is not None and fuel_capacity > 0:
        truck_data["fuel_use_rate"] = net_fuel_consumption
        truck_data["engine_on_time"] = round(
            float(fuel_capacity) / float(net_fuel_consumption), 1
        )

    suspension_types = xml_result(
        contents, True, ["Truck", "TruckData", "SuspensionSocket", "Type"], "str"
    )
    if suspension_types is not None:
        truck_data["suspension_type"] = suspension_types
        truck_data["max_rear_sus_height"] = get_max_rear_suspension_height(
            str(suspension_types), sus_dict
        )

    truck_data = add_addon_info(contents, truck_data)
    truck_data["pulling_quotient"] = calculate_pulling_quotient(
        truck_name,
        truck_data["wheel_adj_power"],
        truck_data["max_wheel_size"],
        truck_data["drive_wheel_count"],
        truck_data["difflock"],
        truck_data["awd"],
        truck_data["mass"],
        has_dead_axel,
        has_doubles,
    )

    return truck_id, truck_data


def get_all_truck_data(
    use_initial_files: bool, engine_dict: dict[str, dict], gearbox_dict: dict[str, dict], wheel_dict: dict[str, dict], sus_dict: dict[str, dict],ui_dict: dict[str, str], input_folder: str
) -> dict[str, dict]:
    all_truck_data: dict[str, dict] = {}
    trucks_folder = Path(utils.root_path, f"{input_folder}/initial/[media]/classes/trucks")
    mod_folder = Path(utils.root_path, "input/mods")
    dlc_folder = Path(utils.root_path, f"{input_folder}/initial/[media]/_dlc")

    # Iterate through all XML files in the folder
    for file_path in trucks_folder.glob("*.xml"):
        truck_name, truck_data = get_truck_data(
            file_path, use_initial_files, engine_dict, gearbox_dict, wheel_dict, sus_dict, ui_dict
        )
        all_truck_data[truck_name] = truck_data

    for file_path in mod_folder.glob("*/classes/trucks/*.xml"):
        truck_name, truck_data = get_truck_data(
            file_path, True, engine_dict, gearbox_dict, wheel_dict, sus_dict, ui_dict
        )
        all_truck_data[truck_name] = truck_data

    for file_path in dlc_folder.glob(
        "dlc_*/classes/trucks/*.xml", case_sensitive=False
    ):
        truck_name, truck_data = get_truck_data(
            file_path, use_initial_files, engine_dict, gearbox_dict, wheel_dict, sus_dict, ui_dict
        )
        all_truck_data[truck_name] = truck_data
    return all_truck_data


def process_truck_data(engine_dict: dict[str, dict], gearbox_dict: dict[str, dict], wheel_dict: dict[str, dict], sus_dict: dict[str, dict], ui_dict: dict[str, str],use_initial_files=True, input_folder: str="input") -> dict[str, dict]:
    truck_dict: dict[str, dict] = get_all_truck_data(use_initial_files, engine_dict, gearbox_dict, wheel_dict, sus_dict,ui_dict, input_folder)
    addition = ""
    if not use_initial_files:
        addition = "_edited"
    with open(f"../reference/info/trucks_data{addition}.json", "w", encoding="utf-8") as f:
        json.dump(truck_dict, f, indent=4)
    return truck_dict