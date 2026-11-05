from dataclasses import dataclass


@dataclass(frozen=True)
class Transcription:
    text: str
