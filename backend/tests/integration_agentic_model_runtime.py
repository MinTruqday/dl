import asyncio
import base64
import io
import wave

from src.utils.local_models import local_model_client


def audio_data_url() -> str:
    stream = io.BytesIO()
    with wave.open(stream, "wb") as audio:
        audio.setnchannels(1)
        audio.setsampwidth(2)
        audio.setframerate(16000)
        audio.writeframes(b"\x00\x00" * 4000)
    return "data:audio/wav;base64," + base64.b64encode(stream.getvalue()).decode()


async def complete(messages):
    response = await local_model_client.chat_completion(
        messages=messages,
        max_tokens=24,
        temperature=0,
    )
    content = response.choices[0].message.content
    assert isinstance(content, str) and content.strip()


async def main():
    image = (
        "data:image/png;base64,"
        "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNk+A8AAQUBAScY42YAAAAASUVORK5CYII="
    )
    await complete([{"role": "user", "content": "Reply with one word"}])
    await complete(
        [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": "Identify the dominant color"},
                    {"type": "image_url", "image_url": {"url": image}},
                ],
            }
        ]
    )
    await complete(
        [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": "Describe this audio briefly"},
                    {
                        "type": "audio_url",
                        "audio_url": {"url": audio_data_url()},
                    },
                ],
            }
        ]
    )
    print("agentic model runtime integration passed")


asyncio.run(main())
