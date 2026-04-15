from pathlib import Path


class LangRegistry:
    def __init__(self, file_path: Path | None = None):
        """
        Initialize the LangRegistry and optionally load entries from a file.
        """
        self._entries: dict[str, str] = {}
        self._new_entries: dict[str, str] = {}
        if file_path:
            self.load_strings_file(file_path)

    def load_strings_file(self, file_path: Path) -> None:
        """
        Loads entries from a .str file (UTF-16LE, tab-separated).
        """
        if not file_path.exists():
            print(f"Warning: Language file not found: {file_path}")
            return

        with open(file_path, "r", encoding="utf-16LE") as f:
            for line in f:
                if not line.strip() or "\t" not in line:
                    continue
                parts = line.split("\t")
                ui_id: str = parts[0].strip()
                # Extraction logic mirroring data_process.py for compatibility
                if '"' in line:
                    try:
                        name: str = line.split('"', 1)[1].strip()
                        if name.endswith('"'):
                            name = name[:-1]
                        self._entries[ui_id] = name
                    except IndexError:
                        pass
                else:
                    if len(parts) > 1:
                        self._entries[ui_id] = parts[1].strip()

    def get(self, key: str, default: str | None = None) -> str:
        """
        Returns the localized string for the given key.
        """
        return self._entries.get(key, default if default is not None else key)

    def __getitem__(self, key: str) -> str:
        return self.get(key)

    def __contains__(self, key: str) -> bool:
        return key in self._entries

    @property
    def entries(self) -> dict[str, str]:
        return self._entries.copy()

    @property
    def new_entries(self) -> dict[str, str]:
        """
        Returns a dictionary of entries added via add_entry.
        """
        return self._new_entries.copy()

    def add_entry(self, key: str, value: str) -> None:
        """
        Adds or updates a language entry and marks it as a new entry.
        """
        self._entries[key] = value
        self._new_entries[key] = value
