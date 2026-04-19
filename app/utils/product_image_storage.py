from pathlib import Path
from uuid import uuid4

from fastapi import UploadFile


def save_product_image(file: UploadFile, id_empresa: int) -> str:
    media_root = Path("media")
    relative_dir = Path("products") / f"empresa_{id_empresa}"
    target_dir = media_root / relative_dir
    target_dir.mkdir(parents=True, exist_ok=True)

    suffix = Path(file.filename or "").suffix.lower() or ".jpg"
    filename = f"{uuid4().hex}{suffix}"
    target_path = target_dir / filename

    with target_path.open("wb") as out:
        out.write(file.file.read())

    return f"/media/{(relative_dir / filename).as_posix()}"