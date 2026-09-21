from datetime import datetime, timezone
from pathlib import Path
import sys

from fastapi import APIRouter, Depends, HTTPException

from app.core.security import decode_token
from app.routes.auth import oauth2_scheme

project_root = Path(__file__).resolve().parents[3]
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from gan_generator import SimpleGANGenerator

router = APIRouter(tags=["generation"])
generator = SimpleGANGenerator(seed=7)
output_dir = project_root / "frontend" / "dist" / "generated"


@router.post("/generate")
def generate_images(payload: dict, token: str = Depends(oauth2_scheme)):
    try:
        decode_token(token)
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid token")

    style = payload.get("style", "nature")
    count = max(1, min(int(payload.get("count", 1)), 4))
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S%f")
    batch_dir = output_dir / timestamp

    try:
        generated = generator.generate(style, output_path=str(batch_dir), count=count)
    except (TypeError, ValueError) as error:
        raise HTTPException(status_code=400, detail=str(error))

    return {
        "style": style,
        "images": [
            {"url": f"/ui/generated/{timestamp}/{style}_{index}.png"}
            for index in range(1, count + 1)
        ],
    }