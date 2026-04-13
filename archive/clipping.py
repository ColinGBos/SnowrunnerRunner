import json
from pathlib import Path



def main():
    pass
    # file_paths = []
    # models_main_folder = Path("clipping/initial/[media]/classes/models")
    # dlc_folder = Path("clipping/initial/[media]/_dlc")
    #
    # # Iterate through all XML files in the folder
    # for file_path in models_main_folder.glob("*.xml"):
    #     file_paths.append(str(file_path).replace("clipping", "input"))
    #
    # for file_path in dlc_folder.glob(
    #     "*/classes/models/*.xml", case_sensitive=False
    # ):
    #     file_paths.append(str(file_path).replace("clipping", "input"))
    #
    # with open("reference/clipping.json", "w") as file:
    #     json.dump(file_paths, file, indent=4)



if __name__ == "__main__":
    main()