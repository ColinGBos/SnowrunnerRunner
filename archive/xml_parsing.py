import json
from pathlib import Path
import xml.etree.ElementTree as ET

def main():
    suspension_main_folder = Path("input/initial/[media]/classes/suspensions")
    # dlc_folder = Path("input/initial/[media]/_dlc")
    # for file_path in dlc_folder.glob(
    #     "dlc_*/classes/suspensions/*.xml", case_sensitive=False
    # ):
    #     buff_suspension_damping(file_path)

    # Iterate through all XML files in the folder
    for file_path in suspension_main_folder.glob("*.xml"):
        with open(file_path, "r") as file:
            xml_data = file.read()
            wrapped_xml_data = f"<fake_root>{xml_data}</fake_root>"
            # Parse the XML data from a string
            root = ET.fromstring(wrapped_xml_data)
            suspension_root = root.findall("SuspensionSetVariants")[0]
            for suspension_set in suspension_root.findall("SuspensionSet"):
                # damage = suspension_set.find("DamageCapacity")
                print(f"Parsed item value: {suspension_set.attrib['DamageCapacity']}")


if __name__ == "__main__":
    main()