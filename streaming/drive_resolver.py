import re


async def resolve_drive(url: str):

    match = re.search(r"/d/([a-zA-Z0-9_-]+)", url)

    if not match:
        return url

    file_id = match.group(1)

    return f"https://drive.google.com/uc?export=download&id={file_id}"
