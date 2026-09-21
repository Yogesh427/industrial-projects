from csv import DictReader, DictWriter
from datetime import datetime, timezone
from io import BytesIO, StringIO
import random
from pathlib import Path
from typing import Any

import numpy as np
from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from PIL import Image, ImageEnhance, ImageFilter, ImageOps

from app.core.security import decode_token
from app.routes.auth import oauth2_scheme
from app.services.training_engine import train

router = APIRouter(tags=["training"])
generated_image_root = Path(__file__).resolve().parents[3] / "frontend" / "trainer" / "generated"

SUPPORTED_ALGORITHMS = {
    "image-recognition",
    "vision-classifier",
    "spam-classifier",
    "logistic-regression",
    "linear-regression",
    "random-forest",
}


def authenticate(token: str) -> None:
    try:
        decode_token(token)
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid token")


def parse_rows(data: str) -> list[dict[str, str]]:
    rows = list(DictReader(StringIO(data.strip())))
    if not rows or not rows[0]:
        raise HTTPException(status_code=400, detail="Provide CSV data with a header row.")
    if len(rows) < 2:
        raise HTTPException(status_code=400, detail="Provide at least two data rows.")
    return rows


def numeric_values(rows: list[dict[str, str]]) -> list[float]:
    values = []
    for row in rows:
        for key, value in row.items():
            if key.lower() in {"label", "class", "target", "text", "filename"}:
                continue
            try:
                values.append(float(value))
            except (TypeError, ValueError):
                continue
    return values


@router.post("/training/preview")
def preview_training_data(payload: dict[str, Any], token: str = Depends(oauth2_scheme)):
    authenticate(token)
    rows = parse_rows(str(payload.get("data", "")))
    columns = list(rows[0].keys())
    label_column = next((column for column in columns if column.lower() in {"label", "class", "target"}), None)
    labels = sorted({row.get(label_column, "") for row in rows}) if label_column else []
    return {
        "rows": len(rows),
        "columns": columns,
        "label_column": label_column,
        "labels": labels,
        "numeric_features": len(numeric_values(rows)),
        "sample": rows[:5],
    }


@router.post("/training/image-preview")
async def preview_images(files: list[UploadFile] = File(...), token: str = Depends(oauth2_scheme)):
    authenticate(token)
    if not files:
        raise HTTPException(status_code=400, detail="Choose at least one image.")

    rows = []
    for upload in files[:100]:
        content = await upload.read()
        try:
            with Image.open(BytesIO(content)) as image:
                rows.append({
                    "filename": upload.filename or "image",
                    "label": (upload.filename or "image").split("_")[0],
                    "width": str(image.width),
                    "height": str(image.height),
                    "mean_red": str(round(float(np.asarray(image.convert("RGB")).mean(axis=(0, 1))[0]), 3)),
                    "mean_green": str(round(float(np.asarray(image.convert("RGB")).mean(axis=(0, 1))[1]), 3)),
                    "mean_blue": str(round(float(np.asarray(image.convert("RGB")).mean(axis=(0, 1))[2]), 3)),
                    "mode": image.mode,
                })
        except Exception:
            continue

    if not rows:
        raise HTTPException(status_code=400, detail="No valid image files were uploaded.")

    csv_output = StringIO()
    writer = DictWriter(csv_output, fieldnames=list(rows[0].keys()))
    writer.writeheader()
    writer.writerows(rows)
    return {
        "rows": len(rows),
        "columns": list(rows[0].keys()),
        "labels": sorted({row["label"] for row in rows}),
        "sample": rows[:5],
        "data": csv_output.getvalue(),
    }


@router.post("/training/generate-images")
async def generate_real_images(
    files: list[UploadFile] = File(...),
    mode: str = Form("similar"),
    count: int = Form(8),
    token: str = Depends(oauth2_scheme),
):
    authenticate(token)
    if mode not in {"similar", "different"}:
        raise HTTPException(status_code=400, detail="Mode must be similar or different.")
    count = max(1, min(count, 100))
    valid_images = []
    for upload in files[:100]:
        try:
            image = Image.open(BytesIO(await upload.read())).convert("RGB")
            valid_images.append(image)
        except Exception:
            continue
    if not valid_images:
        raise HTTPException(status_code=400, detail="No valid images were uploaded.")

    batch_id = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S%f")
    batch_dir = generated_image_root / batch_id
    batch_dir.mkdir(parents=True, exist_ok=True)
    randomizer = random.Random(42)
    results = []
    for index in range(count):
        image = valid_images[index % len(valid_images)].copy()
        if mode == "similar":
            image = ImageEnhance.Brightness(image).enhance(randomizer.uniform(0.92, 1.08))
            image = ImageEnhance.Contrast(image).enhance(randomizer.uniform(0.94, 1.06))
            image = image.rotate(randomizer.uniform(-6, 6), resample=Image.Resampling.BICUBIC, expand=False)
        else:
            image = ImageOps.mirror(image) if index % 2 else image.rotate(randomizer.uniform(-18, 18), expand=False)
            image = ImageEnhance.Color(image).enhance(randomizer.uniform(0.65, 1.45))
            image = ImageEnhance.Contrast(image).enhance(randomizer.uniform(0.7, 1.35))
            if index % 3 == 0:
                image = image.filter(ImageFilter.SHARPEN)
        filename = f"{mode}_{index + 1:04d}.jpg"
        image.save(batch_dir / filename, quality=92)
        results.append({"url": f"/trainer/generated/{batch_id}/{filename}", "filename": filename})

    return {"mode": mode, "count": len(results), "images": results}


@router.post("/training/train")
def train_model(payload: dict[str, Any], token: str = Depends(oauth2_scheme)):
    authenticate(token)
    algorithm = str(payload.get("algorithm", "")).lower()
    if algorithm not in SUPPORTED_ALGORITHMS:
        raise HTTPException(status_code=400, detail="Unsupported training algorithm.")

    rows = parse_rows(str(payload.get("data", "")))
    try:
        result = train(rows, algorithm)
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error))

    return {**result, "status": "TRAINED", "message": f"Real {algorithm} training completed and saved as {result['artifact_id']}."}


@router.post("/training/generate")
def generate_training_data(payload: dict[str, Any], token: str = Depends(oauth2_scheme)):
    authenticate(token)
    rows = parse_rows(str(payload.get("data", "")))
    mode = str(payload.get("mode", "similar")).lower()
    count = max(1, min(int(payload.get("count", 10)), 100))
    if mode not in {"similar", "different"}:
        raise HTTPException(status_code=400, detail="Mode must be similar or different.")

    randomizer = random.Random(42)
    generated = []
    for index in range(count):
        source = rows[index % len(rows)]
        item = {}
        for key, value in source.items():
            try:
                number = float(value)
                spread = 0.08 if mode == "similar" else 0.35
                changed = number * (1 + randomizer.uniform(-spread, spread))
                item[key] = f"{changed:.4f}"
            except (TypeError, ValueError):
                if key.lower() in {"label", "class", "target"} and mode == "different":
                    item[key] = f"generated_{index + 1}"
                elif key.lower() == "filename":
                    item[key] = f"generated_{mode}_{index + 1}.jpg"
                else:
                    item[key] = f"{value}_{'variant' if mode == 'similar' else 'new'}"
        generated.append(item)

    output = StringIO()
    writer = DictWriter(output, fieldnames=list(rows[0].keys()))
    writer.writeheader()
    writer.writerows(generated)
    return {"mode": mode, "count": len(generated), "rows": generated, "csv": output.getvalue()}