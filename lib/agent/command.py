from pathlib import Path
import asyncio
import platform
from queue import Queue

class Shell:
    def __init__(self):
        self.system = platform.system().lower()
        self.command_queue:Queue[Command] = Queue()
        if self.system == "windows":
            self.shell = asyncio.create_subprocess_exec(
                '/bin/bash', 
                stdin=asyncio.subprocess.PIPE,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
        else: # Linux
            self.shell = asyncio.create_subprocess_exec(
                '/bin/bash', 
                stdin=asyncio.subprocess.PIPE,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )

    def push_command(self, command:str, arguments:list[str | Path]):
        self.command_queue.put(Command(self, command, arguments))

class Command:
    def __init__(self, shell:Shell, command:str, arguments:list[str | Path]):
        self.shell = shell
        self.command = command
        self.arguments = arguments
        self.subprocess = None
        self.stdout_lines = []

    def get_command_string(self) -> str:
        return f"{self.command} {' '.join(self.arguments)}"
    
    def get_stdout_lines(self) -> list[str]:
        return self.stdout_lines

    async def approve(self) -> list[str]:
        """
        This function approves the command and executes it.
        """
        shell = await self.shell.shell
        shell.stdin.write(f"{self.get_command_string()}\necho __END_AGENT_COMMAND__\n".encode())
        await shell.stdin.drain()

        while True:
            line = await shell.stdout.readline()
            decoded_line = line.decode().strip()
            if "__END_AGENT_COMMAND__" in decoded_line:
                break
            if decoded_line:
                self.stdout_lines.append(decoded_line)

        return self.stdout_lines