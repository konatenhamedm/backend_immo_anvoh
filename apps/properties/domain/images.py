"""
Optimisation des photos à l'envoi (spécification §35 : « compression des photos », « images optimisées »).

Règles pures : redresse selon l'orientation EXIF, réduit à `max_side` pixels, enregistre en JPEG progressif
(les transparences sont posées sur fond blanc). Une photo de 6 Mo prise au téléphone pèse ensuite 150 à 400 Ko :
c'est ce qui permet un affichage rapide avec une connexion mobile moyenne.
"""

from io import BytesIO

from django.core.files.base import ContentFile
from PIL import Image, ImageOps

MAX_PIXELS = 50_000_000  # garde-fou contre les « bombes de décompression » (images minuscules qui se déploient en Go)
MAX_UPLOAD_BYTES = 15 * 1024 * 1024
FULL_SIDE = 1600
THUMB_SIDE = 480


def optimize_image(source, max_side: int = FULL_SIDE, quality: int = 82, stem: str = "photo") -> ContentFile:
    """Renvoie un fichier JPEG redimensionné (plus grand côté ≤ max_side). Lève ValueError si l'image est inexploitable."""
    try:
        source.seek(0)
    except Exception:  # noqa: BLE001 — certains objets fichier ne se rembobinent pas : on lit depuis la position courante
        pass
    try:
        img = Image.open(source)
        if img.width * img.height > MAX_PIXELS:
            raise ValueError("Image trop grande (nombre de pixels).")
        img = ImageOps.exif_transpose(img)  # une photo prise à la verticale reste à la verticale
        if img.mode in ("RGBA", "LA") or (img.mode == "P" and "transparency" in img.info):
            flat = Image.new("RGB", img.size, (255, 255, 255))
            flat.paste(img.convert("RGBA"), mask=img.convert("RGBA").split()[-1])
            img = flat
        else:
            img = img.convert("RGB")
        img.thumbnail((max_side, max_side), Image.Resampling.LANCZOS)  # ne grossit jamais une petite image
        out = BytesIO()
        img.save(out, format="JPEG", quality=quality, optimize=True, progressive=True)
    except (OSError, SyntaxError) as e:  # fichier corrompu ou format non reconnu
        raise ValueError("Fichier image illisible.") from e
    return ContentFile(out.getvalue(), name=f"{stem}.jpg")
