import src.gearbox_math
import json
from pathlib import Path

import utils
from src.utils import get_modified_file_if_possible
import lxml.etree as etree


def find_avg_gearbox_values(gearboxes) -> tuple[float, float, float, float, float]:
    fuels = []
    awd = []
    mins = []
    maxs = []
    maxs_fuels = []

    for gearbox in gearboxes:
        max_vel = 0.0
        min_vel = 10.0
        max_fuel = 0.0
        awd.append(float(gearbox.get("AWDConsumptionModifier")))
        fuels.append(float(gearbox.get("FuelConsumption")))
        gears = gearbox.findall("Gear")
        if len(gears) > 0:
            for gear in gears:
                vel = float(gear.get("AngVel"))
                if vel > max_vel:
                    max_vel = vel
                if vel < min_vel:
                    min_vel = vel
                fuel = float(gear.get("FuelModifier"))
                if fuel > max_fuel:
                    max_fuel = fuel

        mins.append(min_vel)
        maxs.append(max_vel)
        maxs_fuels.append(max_fuel)
    avg_awd = (2*(sum(awd) / len(awd))+1.3)/3.0
    return sum(fuels) / len(fuels), avg_awd, sum(mins) / len(mins), sum(maxs) / len(maxs), sum(maxs_fuels) / len(maxs_fuels)


def get_gears_for_gearbox(name:str, gears_dict: dict[str, dict], min_vel_avg:float, max_vel_avg:float, max_fuel_modifier:float, og_count:int):
    gb_types = ["offroad", "high", "fine"]
    min_vel = min_vel_avg
    max_vel = min(max(max_vel_avg,6),14)
    max_fuel_mod = min(max_fuel_modifier,2.5)
    curve = 1.1
    count = og_count
    for gb_type in gb_types:
        if gb_type in name:
            min_vel = (min_vel*gears_dict[gb_type]["velocity"]*2.0+1)/3.0
            max_vel = min(max_vel*gears_dict[gb_type]["velocity"], 20)
            count = max(gears_dict[gb_type]["gears_count"], og_count)
            curve = gears_dict[gb_type]["curve"]
            break
    print(f"Gearbox: {name}, min_vel: {min_vel}, max_vel: {max_vel}, count: {count}, curve: {curve}")
    gear_function = src.gearbox_math.generate_exp_func(curve, 1, min_vel, count, max_vel)
    gears = []
    modifier = (max_fuel_mod/float(count))*0.7
    for i in range(1, count + 1):
        gears.append(
            {
                "ang_vel": round(gear_function(i), 2),
                "fuel_modifier": max(round(0.2+max_fuel_mod -(modifier*i), 2), 1.0),
            }
        )
    return gears


def modify_gearbox(file_path: Path, gears_dict: dict[str, dict]):
    contents = get_modified_file_if_possible(file_path, True)

    if "_parent" in contents:
        print(f"Warning, parented gearbox file: {file_path}, skipping.")
    else:
        parser = etree.XMLParser(recover=True)
        wrapped_xml_data = f"<fake_root>{contents}</fake_root>"
        root = etree.fromstring(wrapped_xml_data, parser=parser)

        gearbox_variants = root.find("GearboxVariants")
        if gearbox_variants is not None:
            gearboxes = gearbox_variants.findall("Gearbox")
            avg_fuel, avg_awd, min_vel_avg, max_vel_avg, max_fuel = find_avg_gearbox_values(gearboxes)
            for gearbox in gearbox_variants.findall("Gearbox"):
                og_gear_count = len(gearbox.findall("Gear"))
                replace = False
                awd_modifier:float = float(gearbox.get("AWDConsumptionModifier"))
                fuel_consumption:float = float(gearbox.get("FuelConsumption"))
                name = str(gearbox.get("Name"))
                if "offroad" in name:
                    new_awd:float = round((avg_awd*gears_dict["offroad"]["awd"]+1.0)/2.0,2)
                    new_fuel:float = round((avg_fuel*gears_dict["offroad"]["fuel"]),2)
                    replace = True
                elif "high" in name:
                    new_awd:float = round((avg_awd*gears_dict["high"]["awd"]+1.0)/2.0,2)
                    new_fuel: float = round((avg_fuel * gears_dict["high"]["fuel"]), 2)
                    replace = True
                elif "fine" in name:
                    new_awd:float = round((avg_awd*gears_dict["fine"]["awd"]+1.0)/2.0,2)
                    new_fuel: float = round((avg_fuel * gears_dict["fine"]["fuel"]), 2)
                    replace = True
                else:
                    new_awd:float = round((avg_awd+1.3)/2.0,2)
                    new_fuel: float = round(avg_fuel, 2)
                gearbox.set("AWDConsumptionModifier", str(min(new_awd,1.5)))
                gearbox.set("FuelConsumption", str(new_fuel))

                print(f"AWD Consumption Modifier for {name}: {awd_modifier} -> {new_awd}")
                print(f"Fuel Consumption for {name}: {fuel_consumption} -> {new_fuel}")
                print(f"Modified {name}")
                if replace:
                    gears: list[dict[str, float]] = get_gears_for_gearbox(name, gears_dict, min_vel_avg,
                                                                          max_vel_avg, max_fuel, og_gear_count)
                    gear_vels = [gear["ang_vel"] for gear in gears]
                    highest_vel = max(gear_vels)
                    for gear in gearbox.findall("Gear"):
                        gearbox.remove(gear)
                    for new_gear in gears:
                        etree.SubElement(gearbox, "Gear", AngVel=str(new_gear["ang_vel"]), FuelModifier=str(new_gear["fuel_modifier"]))
                else:
                    highest_vel = max(min(float(gearbox.findall("Gear")[-1].get("AngVel")),18.0),4.5)
                    lowest_vel = float(gearbox.findall("Gear")[0].get("AngVel"))
                    count = max(len(gearbox.findall("Gear")),5)
                    func = src.gearbox_math.generate_exp_func(1.1, 1, float(lowest_vel), count, float(highest_vel))
                    all_gears = gearbox.findall("Gear")
                    for i in range(1, count+1):
                        new_ang_vel = str(round(func(i), 2))
                        if len(all_gears) >= i:
                            gear = all_gears[i - 1]
                            gear.set("AngVel", new_ang_vel)
                        else:
                            etree.SubElement(gearbox, "Gear", AngVel=new_ang_vel, FuelModifier="1.0")

                high = min(max(highest_vel * 0.7, 4.25), 12)
                high_gear = gearbox.find("HighGear")
                high_f = float(high_gear.get("FuelModifier"))
                high_gear.set("AngVel", str(round(high, 2)))
                high_gear.set("FuelModifier", str(round((high_f + 1.6) / 2.0, 2)))
                idle_f = float(gearbox.get("IdleFuelModifier"))
                gearbox.set("IdleFuelModifier", str(round(min(0.35, idle_f), 2)))


        # etree.indent(root)
        # output_file_path = str(file_path).replace("input", "output",1)
        # directory = os.path.dirname(output_file_path)
        # os.makedirs(directory, exist_ok=True)
        # etree.ElementTree(root).write(output_file_path, encoding="utf-8")

        etree.indent(root)
        new_contents: str = etree.tostring(root, pretty_print=True).decode("utf-8")
        new_contents = new_contents.replace("<fake_root>", "").replace("</fake_root>", "")
        utils.write_to_output(file_path, new_contents.strip())


def modify_all_gearbox():
    root_path: Path = Path(__file__).resolve().parents[2]
    gearbox_dict: dict[str, dict] = {}
    with open(Path(root_path, "reference/gearbox_adjustments.json"), "r", encoding="utf-8") as f:
        gearbox_dict = json.load(f)
    gearboxes_folder = Path(root_path, "input/initial/[media]/classes/gearboxes")
    dlc_folder = Path(root_path, "input/initial/[media]/_dlc")
    for gearbox_file in gearboxes_folder.glob("*.xml", case_sensitive=False):
        modify_gearbox(gearbox_file, gearbox_dict)
    for gearbox_file in dlc_folder.glob("*/classes/gearboxes/*.xml", case_sensitive=False):
        modify_gearbox(gearbox_file, gearbox_dict)


# if __name__ == "__main__":
#     modify_all_gearbox()