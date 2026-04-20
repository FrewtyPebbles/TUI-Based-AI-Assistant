from typing import Any

def repr_tool_args(args:dict[str, Any]) -> str:
    return ", ".join([f"{arg}={val}" for arg, val in args.items()])

def format_contact_embedding_string(name:str, email:str | None = None, phone_number:str | None = None, notes:str | None = None):
    return f"Name: {name}\nEmail: {email or ''}\nPhone Number: {phone_number or ''}\nNotes:\n{notes or ''}"