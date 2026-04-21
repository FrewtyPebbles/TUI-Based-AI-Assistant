import datetime
import logging
from pathlib import Path
import asyncio
import platform
from queue import Queue

class Shell:
    def __init__(self):
        self.system = platform.system().lower()
        self.command_queue:asyncio.Queue[Command] = asyncio.Queue()  # Use asyncio.Queue
        
        # Determine the correct shell executable
        shell_exe = "bash" if self.system != "windows" else "cmd.exe"
        
        # Create a shell coroutine.
        self._setup_coro = asyncio.create_subprocess_exec(
            shell_exe,
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.STDOUT  # Merge stderr into stdout to prevent hangs
        )
        self.process = None

    async def ensure_process(self):
        """Ensures the process is actually started."""
        if self.process is None:
            self.process = await self._setup_coro
        return self.process

    async def push_command(self, command:str, arguments:list[str | Path]) -> "Command":
        cmd = Command(self, command, arguments)
        await self.command_queue.put(cmd)
        return cmd

class Command:
    def __init__(self, shell:Shell, command:str, arguments:list[str | Path]):
        self.shell = shell
        self.command = command
        self.arguments = arguments
        self.subprocess = None
        self.stdout_lines = []

    def get_command_string(self) -> str:
        args_serialized = [str(arg) for arg in self.arguments]
        return f"{self.command} {' '.join(args_serialized)}"
    
    def get_stdout_lines(self) -> list[str]:
        return self.stdout_lines

    async def approve(self) -> list[str]:
        process = await self.shell.ensure_process()
        cmd_str = self.get_command_string()
        
        # Use a unique delimiter for this specific execution
        delimiter = f"DONE_{datetime.datetime.now().timestamp()}"
        
        # Force the delimiter to print even if the command fails using ';'
        full_input = f"{cmd_str}\necho {delimiter}\n"
        process.stdin.write(full_input.encode())
        await process.stdin.drain()

        self.stdout_lines = []
        try:
            # Wrap the whole reading process in a timeout
            async with asyncio.timeout(10): 
                while True:
                    line = await process.stdout.readline()
                    if not line:
                        break
                    decoded = line.decode().strip()
                    logging.info(decoded)
                    if delimiter in decoded:
                        break
                    if decoded:
                        self.stdout_lines.append(decoded)
        except TimeoutError:
            self.stdout_lines.append("Error: Command timed out.")
        
        return self.stdout_lines
