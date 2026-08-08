from typing import Any

from qwen_omni_utils import process_mm_info
from transformers import (
    Qwen2_5OmniForConditionalGeneration,
    Qwen2_5OmniProcessor,
)


def media_value(value: Any) -> str:
    if isinstance(value, dict):
        return str(value.get("url") or value.get("data") or "")
    return str(value or "")


def qwen_messages(messages: list[dict[str, Any]]) -> list[dict[str, Any]]:
    converted = []
    for message in messages:
        content = message.get("content", "")
        if isinstance(content, str):
            converted.append(
                {"role": message.get("role", "user"), "content": content}
            )
            continue
        items = []
        for item in content if isinstance(content, list) else []:
            if not isinstance(item, dict):
                continue
            item_type = item.get("type")
            if item_type == "text":
                items.append({"type": "text", "text": str(item.get("text", ""))})
            elif item_type == "image_url":
                items.append(
                    {"type": "image", "image": media_value(item.get("image_url"))}
                )
            elif item_type in {"audio_url", "input_audio"}:
                items.append(
                    {
                        "type": "audio",
                        "audio": media_value(
                            item.get("audio_url") or item.get("input_audio")
                        ),
                    }
                )
        converted.append({"role": message.get("role", "user"), "content": items})
    return converted


class EndpointHandler:
    def __init__(self, path: str = ""):
        self.processor = Qwen2_5OmniProcessor.from_pretrained(path)
        self.model = Qwen2_5OmniForConditionalGeneration.from_pretrained(
            path,
            torch_dtype="auto",
            device_map="auto",
        )
        self.model.disable_talker()

    def __call__(self, data: dict[str, Any]) -> dict[str, Any]:
        messages = qwen_messages(data["inputs"])
        parameters = data.get("parameters") or {}
        prompt = self.processor.apply_chat_template(
            messages,
            add_generation_prompt=True,
            tokenize=False,
        )
        audios, images, videos = process_mm_info(
            messages,
            use_audio_in_video=True,
        )
        inputs = self.processor(
            text=prompt,
            audio=audios,
            images=images,
            videos=videos,
            return_tensors="pt",
            padding=True,
            use_audio_in_video=True,
        )
        inputs = inputs.to(self.model.device).to(self.model.dtype)
        temperature = float(parameters.get("temperature", 0.1))
        generated = self.model.generate(
            **inputs,
            use_audio_in_video=True,
            return_audio=False,
            max_new_tokens=int(parameters.get("max_new_tokens", 1024)),
            do_sample=temperature > 0,
            temperature=max(temperature, 0.000001),
        )
        content = self.processor.batch_decode(
            generated,
            skip_special_tokens=True,
            clean_up_tokenization_spaces=False,
        )[0]
        prompt_tokens = int(inputs["input_ids"].numel())
        completion_tokens = int(generated.numel())
        return {
            "choices": [{"message": {"role": "assistant", "content": content}}],
            "usage": {
                "prompt_tokens": prompt_tokens,
                "completion_tokens": completion_tokens,
            },
        }
