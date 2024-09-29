import os
import ctypes
from datetime import datetime
from colorama import Fore, Style, init

class Console:
    def __init__(self) -> None:
        init(autoreset=True)
        self.colors = {
            "green": Fore.GREEN, "red": Fore.RED, "yellow": Fore.YELLOW,
            "blue": Fore.BLUE, "magenta": Fore.MAGENTA, "cyan": Fore.CYAN,
            "white": Fore.WHITE, "black": Fore.BLACK, "reset": Style.RESET_ALL,
            "lightblack": Fore.LIGHTBLACK_EX, "lightred": Fore.LIGHTRED_EX,
            "lightgreen": Fore.LIGHTGREEN_EX, "lightyellow": Fore.LIGHTYELLOW_EX,
            "lightblue": Fore.LIGHTBLUE_EX, "lightmagenta": Fore.LIGHTMAGENTA_EX,
            "lightcyan": Fore.LIGHTCYAN_EX, "lightwhite": Fore.LIGHTWHITE_EX,
        }

    def clear(self):
        os.system("cls" if os.name == "nt" else "clear")

    def timestamp(self):
        return datetime.now().strftime("%H:%M:%S")

    def success(self, message, obj=None):
        obj_text = f" {obj}" if obj else ""
        print(f"{self.colors['lightblack']}{self.timestamp()} » {self.colors['lightgreen']}SUCCESS {self.colors['lightblack']}• {self.colors['white']}{message}{obj_text} {self.colors['reset']}")

    def error(self, message, obj=None):
        obj_text = f" {obj}" if obj else ""
        print(f"{self.colors['lightblack']}{self.timestamp()} » {self.colors['lightred']}ERROR   {self.colors['lightblack']}• {self.colors['white']}{message}{obj_text} {self.colors['reset']}")

    def warning(self, message, obj=None):
        obj_text = f" {obj}" if obj else ""
        print(f"{self.colors['lightblack']}{self.timestamp()} » {self.colors['lightyellow']}WARN    {self.colors['lightblack']}• {self.colors['white']}{message}{obj_text} {self.colors['reset']}")

    def info(self, message, obj=None):
        obj_text = f" {obj}" if obj else ""
        print(f"{self.colors['lightblack']}{self.timestamp()} » {self.colors['lightblue']}INFO    {self.colors['lightblack']}• {self.colors['white']}{message}{obj_text} {self.colors['reset']}")

    def skip(self, message, obj=None):
        obj_text = f" {obj}" if obj else ""
        print(f"{self.colors['lightblack']}{self.timestamp()} » {self.colors['lightcyan']}SKIP    {self.colors['lightblack']}• {self.colors['white']}{message}{obj_text} {self.colors['reset']}")

    def sleeping(self, message, obj=None):
        obj_text = f" {obj}" if obj else ""
        print(f"{self.colors['lightblack']}{self.timestamp()} » {self.colors['lightmagenta']}SLEEP     {self.colors['lightblack']}• {self.colors['white']}{message}{obj_text} {self.colors['reset']}")

    def custom(self, message, obj=None, color='white'):
        obj_text = f" {obj}" if obj else ""
        print(f"{self.colors['lightblack']}{self.timestamp()} » {self.colors[color.upper()]}{color.upper()} {self.colors['lightblack']}• {self.colors['white']}{message}{obj_text} {self.colors['reset']}")