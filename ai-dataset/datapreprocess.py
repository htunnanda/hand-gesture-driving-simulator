from pathlib import Path
from PIL import Image, ImageOps
from rembg import remove, new_session

# =====================================
# CONFIGURATION
# =====================================

BASE_DIR = Path(__file__).resolve().parent.parent

RAW_DIR = BASE_DIR / "ai-dataset" / "ai_dataset"
OUTPUT_DIR = BASE_DIR / "ai-dataset" / "processed-dataset"

GESTURES = [
    "fist",
    "left_dir",
    "palm",
    "right_dir"
]

IMAGE_SIZE = 64
PADDING = 4

SUPPORTED_FORMATS = {
    ".jpg", ".jpeg", ".png", ".webp", ".bmp"
}

# =====================================
# LOAD BACKGROUND REMOVAL MODEL
# =====================================

print("Loading background removal model...")

session = new_session("u2net")

print("Model loaded successfully!")

# =====================================
# PREPROCESSING FUNCTION
# =====================================

def preprocess_image(image_path):

    # 1. Load image
    with Image.open(image_path) as img:
        image = ImageOps.exif_transpose(img).convert("RGB")

    # 2. Remove background
    hand = remove(image, session=session)
    hand = hand.convert("RGBA")

    # 3. Get foreground bounding box
    alpha = hand.getchannel("A")
    bbox = alpha.getbbox()

    if bbox is None:
        return None

    # 4. Crop transparent area
    hand = hand.crop(bbox)

    # 5. Resize while preserving aspect ratio
    target_size = IMAGE_SIZE - (PADDING * 2)

    hand.thumbnail(
        (target_size, target_size),
        Image.Resampling.LANCZOS
    )

    # 6. Create black background
    canvas = Image.new(
        "RGB",
        (IMAGE_SIZE, IMAGE_SIZE),
        (0, 0, 0)
    )

    # 7. Center hand
    x = (IMAGE_SIZE - hand.width) // 2
    y = (IMAGE_SIZE - hand.height) // 2

    canvas.paste(
        hand,
        (x, y),
        hand.getchannel("A")
    )

    return canvas


# =====================================
# PROCESS DATASET
# =====================================

def process_dataset():

    total_processed = 0
    total_skipped = 0

    for gesture in GESTURES:

        input_folder = RAW_DIR / gesture
        output_folder = OUTPUT_DIR / gesture

        output_folder.mkdir(
            parents=True,
            exist_ok=True
        )

        if not input_folder.exists():
            print(f"Folder not found: {input_folder}")
            continue

        print(f"\nProcessing: {gesture}")

        processed = 0
        skipped = 0

        for image_path in sorted(input_folder.iterdir()):

            if image_path.suffix.lower() not in SUPPORTED_FORMATS:
                continue

            try:

                processed_image = preprocess_image(image_path)

                if processed_image is None:
                    print(f"Skipped: {image_path.name}")
                    skipped += 1
                    continue

                output_path = (
                    output_folder / f"{image_path.stem}.png"
                )

                processed_image.save(output_path)

                processed += 1

            except Exception as e:

                print(f"Error: {image_path.name} - {e}")
                skipped += 1

        total_processed += processed
        total_skipped += skipped

        print(f"{gesture}: {processed} images saved")
        print(f"{gesture}: {skipped} images skipped")

    print("\n================================")
    print("PREPROCESSING COMPLETED")
    print("================================")

    print(f"Total processed: {total_processed}")
    print(f"Total skipped: {total_skipped}")


# =====================================
# MAIN
# =====================================

if __name__ == "__main__":
    process_dataset()