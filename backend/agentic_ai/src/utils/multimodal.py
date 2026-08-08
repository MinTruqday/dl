import base64
import binascii

def decode_data_url(value: str) -> tuple[bytes, str]:
    if not value.startswith("data:") or "," not in value:
        raise ValueError("invalid_multimodal_data")
    header, encoded = value.split(",", 1)
    if ";base64" not in header:
        raise ValueError("invalid_multimodal_encoding")
    media_type = header[5:].split(";", 1)[0].lower()
    try:
        payload = base64.b64decode(encoded, validate=True)
    except (binascii.Error, ValueError) as error:
        raise ValueError("invalid_multimodal_payload") from error
    if not payload or len(payload) > 20_000_000:
        raise ValueError("multimodal_payload_size_invalid")
    return payload, media_type


def validate_audio(value: str) -> None:
    _, media_type = decode_data_url(value)
    if not media_type.startswith("audio/"):
        raise ValueError("invalid_audio_type")


def validate_image(value: str) -> None:
    _, media_type = decode_data_url(value)
    if not media_type.startswith("image/"):
        raise ValueError("invalid_image_type")
