import re
import httpx


# ---------------------------
# extrai ID do google drive
# ---------------------------
def extract_drive_id(url: str):
    patterns = [
        r"/file/d/([^/]+)",
        r"id=([^&]+)"
    ]

    for p in patterns:
        match = re.search(p, url)
        if match:
            return match.group(1)

    return None


# ---------------------------
# resolve link direto
# ---------------------------
async def resolve_drive_url(url: str):

    file_id = extract_drive_id(url)
    if not file_id:
        return url

    base = "https://drive.google.com/uc?export=download"

    async with httpx.AsyncClient(
        follow_redirects=True,
        headers={"User-Agent": "Mozilla/5.0"}
    ) as client:

        r = await client.get(f"{base}&id={file_id}")

        # se já for download direto
        if "Content-Disposition" in r.headers:
            return str(r.url)

        # procura confirm token (arquivo grande)
        token_match = re.search(
            r"confirm=([0-9A-Za-z_]+)",
            r.text
        )

        if token_match:
            token = token_match.group(1)

            r2 = await client.get(
                f"{base}&confirm={token}&id={file_id}"
            )

            return str(r2.url)

    return url
