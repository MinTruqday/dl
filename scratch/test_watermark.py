import re

def encode_watermark(payload: str) -> str:
    binary = ''.join(format(ord(c), '08b') for c in payload)
    zero_width = binary.replace('0', '\u200B').replace('1', '\u200C')
    return f"\u200D{zero_width}\u200D"

def decode_watermark(text: str) -> str:
    matches = re.findall(r'\u200D([\u200B\u200C]+)\u200D', text)
    if not matches:
        return None
    binary = matches[0].replace('\u200B', '0').replace('\u200C', '1')
    chars = [chr(int(binary[i:i+8], 2)) for i in range(0, len(binary), 8)]
    return ''.join(chars)

encoded = encode_watermark("USER-1234")
print(f"Encoded length: {len(encoded)}")
print(f"Decoded: {decode_watermark(encoded)}")
