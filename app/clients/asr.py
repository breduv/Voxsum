import os
from pathlib import Path
from tempfile import TemporaryDirectory

import ffmpeg
import onnx_asr


class ASR:
    def __init__(self, model_name: str = "gigaam-v3-e2e-rnnt"):
        # Set the cache before Hugging Face is imported by onnx-asr.
        os.environ.setdefault(
            "HF_HOME", str(Path(__file__).resolve().parents[2] / "data" / "huggingface")
        )

        model = onnx_asr.load_model(model_name)
        vad = onnx_asr.load_vad("silero")

        self.model = model.with_vad(vad)

    def transcribe(self, audio_path: Path) -> str:
        with TemporaryDirectory(prefix="voxsum-asr-") as directory:
            wav_path = Path(directory) / "audio.wav"
            self._decode(audio_path, wav_path)

            return "\n\n".join(
                text
                for segment in self.model.recognize(wav_path)
                if (text := segment.text.strip())
            )

    def _decode(self, audio_path: Path, wav_path: Path) -> None:
        try:
            (
                ffmpeg.input(str(audio_path))
                .audio.output(
                    str(wav_path),
                    format="wav",
                    ac=1,
                    ar=16000,
                    acodec="pcm_s16le",
                )
                .global_args("-nostdin", "-hide_banner", "-loglevel", "error")
                .run(
                    overwrite_output=True,
                    capture_stderr=True,
                )
            )
        except ffmpeg.Error as exc:
            raise RuntimeError("Не удалось преобразовать аудиофайл в WAV") from exc
