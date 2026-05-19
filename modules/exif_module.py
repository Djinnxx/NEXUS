import os
import struct
from datetime import datetime
from .base import ScanWorker

def _try_exifread(filepath):
    try:
        import exifread
        with open(filepath, "rb") as f:
            tags = exifread.process_file(f, details=False)
        return {str(k): str(v) for k, v in tags.items()}
    except Exception:
        return {}

def _try_pil(filepath):
    try:
        from PIL import Image
        from PIL.ExifTags import TAGS, GPSTAGS
        img   = Image.open(filepath)
        exif  = img._getexif() or {}
        clean = {}
        for tag_id, val in exif.items():
            tag = TAGS.get(tag_id, str(tag_id))
            clean[tag] = str(val)
        return clean
    except Exception:
        return {}

def _decode_gps(tags):
    """Extract GPS lat/lon from EXIF tags dict."""
    try:
        lat_ref = tags.get("GPS GPSLatitudeRef", tags.get("GPSLatitudeRef", ""))
        lon_ref = tags.get("GPS GPSLongitudeRef", tags.get("GPSLongitudeRef", ""))
        lat_raw = tags.get("GPS GPSLatitude",    tags.get("GPSLatitude",    ""))
        lon_raw = tags.get("GPS GPSLongitude",   tags.get("GPSLongitude",   ""))
        if not (lat_raw and lon_raw):
            return None

        def to_deg(s):
            parts = str(s).strip("[]").split(",")
            d = float(eval(parts[0].strip()))
            m = float(eval(parts[1].strip()))
            se = float(eval(parts[2].strip()))
            return d + m / 60 + se / 3600

        lat = to_deg(lat_raw)
        lon = to_deg(lon_raw)
        if "S" in str(lat_ref).upper():
            lat = -lat
        if "W" in str(lon_ref).upper():
            lon = -lon
        return {"latitude": round(lat, 6), "longitude": round(lon, 6)}
    except Exception:
        return None

def run_scan(target: str, **kwargs) -> dict:
    """Target = path to a file."""
    result = ScanWorker.empty_result(target)

    if not os.path.isfile(target):
        return ScanWorker.error_result(target, "File not found. Provide a valid local file path.")

    ext  = os.path.splitext(target)[1].lower()
    size = os.path.getsize(target)
    result["data"]["file"] = {
        "path": target,
        "name": os.path.basename(target),
        "size": size,
        "ext":  ext,
    }
    result["findings"].append(f"File: {os.path.basename(target)} ({size:,} bytes)")

    # -- EXIF (images) --------------------------------------------------------
    if ext in (".jpg", ".jpeg", ".tiff", ".heic", ".png"):
        raw = _try_exifread(target) or _try_pil(target)
        result["data"]["exif"] = raw

        important_tags = [
            "Image Make", "Image Model", "EXIF DateTimeOriginal",
            "EXIF LensModel", "EXIF Software",
            "Make", "Model", "DateTimeOriginal", "Software",
        ]
        for tag in important_tags:
            if tag in raw:
                result["findings"].append(f"  {tag}: {raw[tag]}")

        gps = _decode_gps(raw)
        if gps:
            result["data"]["gps"] = gps
            result["risk_score"]  = 80
            result["findings"].append(
                f"[CRITICAL] GPS Coordinates found: {gps['latitude']}, {gps['longitude']}"
            )
            result["findings"].append(
                f"  Maps: https://maps.google.com/?q={gps['latitude']},{gps['longitude']}"
            )

    # -- PDF ------------------------------------------------------------------
    elif ext == ".pdf":
        try:
            import PyPDF2
            with open(target, "rb") as f:
                reader = PyPDF2.PdfReader(f)
                meta   = reader.metadata or {}
            pdf_meta = {k.lstrip("/"): str(v) for k, v in meta.items()}
            result["data"]["pdf_meta"] = pdf_meta
            for k, v in pdf_meta.items():
                result["findings"].append(f"  {k}: {v}")
        except Exception as e:
            result["findings"].append(f"PDF parse error: {e}")

    # -- DOCX -----------------------------------------------------------------
    elif ext in (".docx", ".docm"):
        try:
            import docx
            doc  = docx.Document(target)
            core = doc.core_properties
            props = {
                "Author":         str(core.author),
                "Last Modified":  str(core.last_modified_by),
                "Created":        str(core.created),
                "Modified":       str(core.modified),
                "Revision":       str(core.revision),
                "Title":          str(core.title),
            }
            result["data"]["docx_meta"] = props
            for k, v in props.items():
                if v and v != "None":
                    result["findings"].append(f"  {k}: {v}")
        except Exception as e:
            result["findings"].append(f"DOCX parse error: {e}")

    else:
        result["findings"].append(f"Unsupported file type: {ext}")

    return result


class Worker(ScanWorker):
    def run(self):
        self.log(f"EXIF/Metadata analysis: {self.target}", "INFO")
        self.progress.emit(20)
        result = run_scan(self.target, **self.kwargs)
        self.progress.emit(100)
        self.log(f"Metadata extraction done ({result['status']})",
                 "SUCCESS" if result["status"] == "success" else "WARNING")
        self.result_ready.emit(result)
