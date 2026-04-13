from turtle import towards
import src.gearbox_math
import json
from pathlib import Path

from src import utils
from src.utils import get_modified_file_if_possible
import lxml.etree as etree  # ty:ignore[unresolved-import]


def modify_all_engines():
    root_path: Path = Path(__file__).resolve().parents[2]
    engines_folder = Path(root_path, "input/initial/[media]/classes/engines")
    dlc_folder = Path(root_path, "input/initial/[media]/_dlc")
    for engine_file in engines_folder.glob("*.xml", case_sensitive=False):
        modify_engine(engine_file)
    for engine_file in dlc_folder.glob("*/classes/engines/*.xml", case_sensitive=False):
        modify_engine(engine_file)


def modify_engine(file_path: Path):
    contents = get_modified_file_if_possible(file_path, False)
    if "_parent" in contents:
        print(f"Warning, parented gearbox file: {file_path}, skipping.")
    else:
        wrapped_xml_data = f"<fake_root>{contents}</fake_root>"
        root = etree.fromstring(wrapped_xml_data)
        engine_variants = root.find("EngineVariants")
        if engine_variants is not None:
            engines = engine_variants.findall("Engine")
            if len(engines) < 3:
                return
            engine_profiles = []
            for engine in engines:
                name = str(engine.get("Name"))
                torque = int(engine.get("Torque"))
                consumption = float(engine.get("FuelConsumption"))
                efficiency = round(torque / consumption / 1000.0, 2)
                engine_profiles.append({
                    "name": name,
                    "torque": torque,
                    "consumption": consumption,
                    "efficiency": efficiency,
                })
            engine_profiles.sort(key=lambda x: x["torque"], reverse=False)

            percent_decrease = (engine_profiles[-1]["torque"] - engine_profiles[0]["torque"]) / engine_profiles[-1][
                "torque"]
            engine_count = len(engine_profiles)
            top_efficiency = engine_profiles[-1]["efficiency"]
            top_consumption = engine_profiles[-1]["consumption"]
            top_torque = engine_profiles[-1]["torque"]
            min_torque = engine_profiles[0]["torque"]
            if "scout" in file_path.name.lower():
                new_percent_decrease = (percent_decrease + 0.42 * engine_count) / engine_count
            else:
                new_percent_decrease = (percent_decrease + 0.25 * engine_count) / engine_count
            ind_decrease = new_percent_decrease / engine_count
            print(f"Individually decreasing {engine_count} engines by {ind_decrease}%")
            engine_profiles.sort(key=lambda x: x["torque"], reverse=True)
            i = 0
            for engine in engine_profiles:
                engine["perf_vs_top"] = engine["efficiency"] / top_efficiency
                if engine["torque"] < top_torque:
                    engine["new_torque"] = int(round(top_torque - top_torque * ind_decrease * i, -3))
                    engine["new_consumption"] = round(top_consumption - top_consumption * ind_decrease * 1.35 * i, 2)
                i += 1

            print(engine_profiles)

            for file_engine in engines:
                for engine_profile in engine_profiles:
                    if engine_profile["name"] == file_engine.get("Name"):
                        if "new_torque" in engine_profile:
                            file_engine.set("Torque", str(engine_profile["new_torque"]))
                            file_engine.set("FuelConsumption", str(engine_profile["new_consumption"]))

            etree.indent(root)
            new_contents = etree.tostring(root, pretty_print=True).decode("utf-8")
            new_contents = new_contents.replace("<fake_root>", "").replace("</fake_root>", "")
            utils.write_to_output(file_path, new_contents)


if __name__ == "__main__":
    modify_all_engines()
