"""Optional SAM 3.1 request builder; DOES NOT call Meta or parse model output.

Object segmentation is equipment inventory assistance, not fault detection and
never an input to electrical control authorization. No user-supplied remote URLs.
"""
import base64
from typing import Literal

from pydantic import Field
from eden.sentinel.twin import TwinModel

MAX_IMAGE_BYTES = 2 * 1024 * 1024
EquipmentConcept = Literal["solar panel", "inverter", "battery cabinet"]


class SegmentationRequestSummary(TwinModel):
    model: Literal["sam-3.1"] = "sam-3.1"
    purpose: Literal["equipment_inventory_only"] = "equipment_inventory_only"
    concept: EquipmentConcept
    image_bytes: int = Field(gt=0, le=MAX_IMAGE_BYTES)
    network_call_made: Literal[False] = False


def build_sam_request(image: bytes, concept: EquipmentConcept) -> tuple[dict, SegmentationRequestSummary]:
    if concept not in ("solar panel", "inverter", "battery cabinet"):
        raise ValueError("unsupported equipment concept")
    if not isinstance(image, bytes) or not image or len(image) > MAX_IMAGE_BYTES:
        raise ValueError("image bytes missing or exceed 2 MB")
    if image.startswith(b"\x89PNG\r\n\x1a\n"):
        mime = "image/png"
    elif image.startswith(b"\xff\xd8\xff"):
        mime = "image/jpeg"
    else:
        raise ValueError("only PNG and JPEG files accepted")
    uri = f"data:{mime};base64," + base64.b64encode(image).decode("ascii")
    request = {
        "model": "sam-3.1",
        "input": [{"type": "message", "role": "user", "content": [
            {"type": "input_text", "text": concept},
            {"type": "input_image", "image_url": uri},
        ]}],
        "stream": True,
    }
    return request, SegmentationRequestSummary(concept=concept, image_bytes=len(image))
