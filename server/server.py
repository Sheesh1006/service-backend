from typing import Iterator
from backend_service import backend_service_pb2_grpc
from backend_service.backend_service_pb2 import (
    GetNotesRequest, GetNotesResponse
)
from chatgpt_service.chatgpt_service_pb2_grpc import ChatGPTServiceStub
from chatgpt_service.chatgpt_service_pb2 import (
    GetRawNotesRequest, GetRawNotesResponse,
    GetKeyFramesRequest, GetKeyFramesResponse,
    GetTimestampsRequest, GetTimestampsResponse
)
from munch import munchify
from yaml import safe_load
import grpc
from .notes import Notes2pdf


def createClient() -> ChatGPTServiceStub:
    with open('config.yml') as cfg:
        config = munchify(safe_load(cfg))
    channel = grpc.insecure_channel(config.chatgpt_client.addr)
    stub = ChatGPTServiceStub(channel)
    return stub

class BackendServiceServicer(backend_service_pb2_grpc.BackendServiceServicer):
    stub: ChatGPTServiceStub = createClient()

    def GetNotes(
        self,
        request_iterator: Iterator[GetNotesRequest],
        context
    ) -> Iterator[GetNotesResponse]:
        video_chunks = []
        pres_chunks = []
        for req in request_iterator:
            video_chunks.append(req.video)
            pres_chunks.append(req.presentation)

        if not video_chunks:
            context.set_code(grpc.StatusCode.INVALID_ARGUMENT)
            context.set_details("No video data received")
            return
        full_video = b''.join(video_chunks)
        presentation = b''.join(pres_chunks)

        def raw_req_stream() -> Iterator[GetRawNotesRequest]:
            CHUNK = 2 * 1024 * 1024  # 5 MB
            # первый пакет приходит с presentation, остальные без
            first = True
            for i in range(0, len(full_video), CHUNK):
                chunk = full_video[i : i + CHUNK]
                if first:
                    yield GetRawNotesRequest(
                        video=chunk,
                        presentation=presentation
                    )
                    first = False
                else:
                    yield GetRawNotesRequest(video=chunk)

        raw_notes = []
        raw_notes_resp: GetRawNotesResponse = self.stub.GetRawNotes(raw_req_stream())
        for resp in raw_notes_resp:
            chunk = resp.raw_notes
            # if the ChatGPTService accidentally sent bytes, force it to str
            if isinstance(chunk, (bytes, bytearray)):
                chunk = chunk.decode("utf-8")
            raw_notes.extend(chunk.split("###"))

        timestamps = []
        timestamps_resp: GetTimestampsResponse = self.stub.GetTimestamps(GetTimestampsRequest())
        for resp in timestamps_resp:
            ts = resp.timestamps
            if isinstance(ts, (bytes, bytearray)):
                ts = ts.decode("utf-8")
            timestamps.extend(ts.split("###"))
        
        converter = Notes2pdf(timestamps, raw_notes, None)
        pdf_bytes = converter.export_pdf()

        CHUNK_OUT = 4 * 1024 * 1024  # 4 MB
        for i in range(0, len(pdf_bytes), CHUNK_OUT):
            yield GetNotesResponse(notes=pdf_bytes[i : i + CHUNK_OUT])