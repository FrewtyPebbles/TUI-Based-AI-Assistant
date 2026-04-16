import asyncio

import ollama as oll
from typing import TYPE_CHECKING, Any, Literal
from queue import Queue
import datetime
from zoneinfo import ZoneInfo
from pathlib import Path
import os
import platform
from lib.agent.command import Shell
from lib.session_manager import SessionData
if TYPE_CHECKING:
    from main import AppGUI

def get_file_type(file:Path):
    file_type = "?"
    if file.is_dir():
        file_type = "folder"
    if file.is_file():
        file_type = "file"
    elif file.is_symlink():
        file_type = "symlink"
    elif file.is_socket():
        file_type = "socket"
    elif file.is_fifo():
        file_type = "FIFO/named pipe"
    elif file.is_block_device():
        file_type = "block device"
    elif file.is_char_device():
        file_type = "character device"

class Agent:
    app:"AppGUI"
    def __init__(self):
        self.oll_client = oll.AsyncClient()
        self.shell = Shell()

    def call_tool(self, function_name:str, arguments:dict) -> Any:
        match function_name:
            case "request_command":
                return self.request_command(**arguments)
            case "run_command":
                return self.run_command(**arguments)
            case "get_datetime":
                return self.get_datetime(**arguments)
            case "get_operating_system":
                return self.get_operating_system(**arguments)
            case "list_items_in_directory":
                return self.list_items_in_directory(**arguments)
            case "get_current_working_directory":
                return self.get_current_working_directory(**arguments)
            case "read_file":
                return self.read_file(**arguments)

    async def prompt(self):
        return await self.oll_client.chat(model=self.app.current_model.model, messages=self.app.session_data.get_history(),
            think=False,
            stream=True,
            tools=[
                self.request_command,
                self.run_command,
                self.get_datetime,
                self.get_operating_system,
                self.list_items_in_directory,
                self.get_current_working_directory,
                self.read_file
            ]
        )
    
    # TOOLS
    async def request_command(self, command:str, command_arguments:list[str|Path]) -> None:
        """
        Request to run a shell command on the user's pc. The command is executed in the format:
        
        {command} {command_arguments[0]} {command_arguments[1]} {command_arguments[...]} {command_arguments[n-1]} {command_arguments[n]}

        Args:
            command: The command/program name.
            command_arguments: The command line interface arguments for the command.
        """
        self.shell.push_command(command, command_arguments)

    async def run_command(self, command:str, command_arguments:list[str|Path]) -> str:
        """
        Run a shell command on the user's pc. The command is executed in the format:
        
        {command} {command_arguments[0]} {command_arguments[1]} {command_arguments[...]} {command_arguments[n-1]} {command_arguments[n]}

        Args:
            command: The command/program name.
            command_arguments: The command line interface arguments for the command.
        """
        self.shell.push_command(command, command_arguments)
        return self.shell.command_queue.get().approve()

    async def get_datetime(self,
    timezone_name: Literal[
        "UTC", 
        "America/New_York", 
        "America/Los_Angeles", 
        "Europe/London", 
        "Europe/Paris", 
        "Asia/Tokyo", 
        "Asia/Dubai", 
        "Australia/Sydney"
    ] | None = None
    ) -> str:
        """
        Request the current date and time for a specific timezone.

        Args:
            timezone_name: The time zone to get the current date and time for. If left as None, it will use the user's time zone. The options are "UTC", "America/New_York", "America/Los_Angeles", "Europe/London", "Europe/Paris", "Asia/Tokyo", "Asia/Dubai", and "Australia/Sydney"
        """
        return datetime.datetime.now(ZoneInfo(timezone_name)).strftime("%d/%m/%Y, %I:%M:%S %p")
    
    def get_operating_system(self) -> str:
        """
        Get the current operating system. Possible operating systems include: Windows, Linux, Darwin, and Java.  Other more rare operating systems include: FreeBSD, NetBSD, OpenBSD, SunOS, and AIX.
        If the operating system cannot be determined, the operating system will be unknown.
        """
        operating_system = platform.system()
        return operating_system if operating_system != "" else "unknown"
    
    def get_current_working_directory(self) -> str:
        """
        Get the user's terminal's current working directory.
        """
        return f"{Path.cwd()}"
    
    def list_items_in_directory(self, directory:str|Path) -> str:
        # Docstring set elsewhere for formatting purposes
        ret = f"File system items in \"{directory}\":\n"
        directory = Path(directory)
        if not directory.exists():
            return f"The file system directory \"{directory}\" does not exist."
        if not directory.is_dir():
            return f"The file system path \"{directory}\" points to a {get_file_type(directory)} not a folder."
        for file in directory.iterdir():
            ret += f" - file system item name: {file.name}, type: {get_file_type(file)}\n"
        ret += f"Listed {len([*directory.iterdir()])} file system items in directory."

    def read_file(self, file_path:str|Path) -> str:
        """
        Read the contents of a file from the users computer at a specific file system path.

        Args:
            file_path: The file system path to the file on the user's computer to read the contents of.
        """
        file_path = Path(file_path)
        if not file_path.exists():
            return f"The file path \"{file_path}\" does not point to an existing file."
        if not file_path.is_file() and not file_path.is_symlink():
            return f"The file path \"{file_path}\" points to a {get_file_type(file_path)} not a file."
        return file_path.read_text("utf-8")

if platform.system().lower() == "windows":
    Agent.list_items_in_directory.__doc__ = """
    List the items inside of a directory at a specific file system path. Each item's type will be listed too. Possible types include file, folder, and symlink.

    Args:
        directory: The string or Path object of the file system path to the directory on the user's system. All of the items inside of this directory will be listed.
    """
else:
    Agent.list_items_in_directory.__doc__ = """
    List the items inside of a directory at a specific file system path. Each item's type will be listed too. Possible types include file, folder, symlink, socket, FIFO/named pipe, block device, and character device.

    Args:
        directory: The string or Path object of the file system path to the directory on the user's system. All of the items inside of this directory will be listed.
    """