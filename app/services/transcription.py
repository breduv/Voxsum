import asyncio
from pathlib import Path
from time import perf_counter

from loguru import logger

from app.clients.asr import ASR
from app.core.errors import EmptyRequestError, TranscriptionError
from app.models.transcription import Transcription


class TranscriptionService:
    def __init__(self, asr: ASR):
        self.asr = asr
        self._lock = asyncio.Lock()

    async def transcribe(self, audio_path: Path) -> Transcription:
        logger.debug("ASR: waiting for worker")
        async with self._lock:
            started = perf_counter()
            logger.debug("ASR: transcribing")
            # Cancellation cannot stop native inference. Keep the lock and input
            # file alive until the worker finishes, then propagate cancellation.
            worker = asyncio.create_task(
                asyncio.to_thread(self.asr.transcribe, audio_path)
            )
            try:
                text = await asyncio.shield(worker)
            except asyncio.CancelledError:
                while not worker.done():
                    try:
                        await asyncio.shield(worker)
                    except asyncio.CancelledError:
                        continue
                    except Exception:  # noqa: BLE001
                        break
                if not worker.cancelled() and (error := worker.exception()) is not None:
                    logger.opt(exception=error).error(
                        "ASR: worker failed after request cancellation"
                    )
                raise
            except Exception as exc:
                raise TranscriptionError("ASR transcription failed") from exc

        text = text.strip()
        if not text:
            raise EmptyRequestError("No speech recognized")
        logger.info(
            "ASR: transcribed, characters={} ({:.1f}s)",
            len(text),
            perf_counter() - started,
        )
        return Transcription(text=text)
