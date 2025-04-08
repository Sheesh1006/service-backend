from typing import Iterator
from backend_service import backend_service_pb2_grpc
from backend_service.backend_service_pb2 import (
    GetNotesRequest, GetNotesResponse
)
from chatgpt_service.chatgpt_service_pb2_grpc import ChatGPTServiceStub
from chatgpt_service.chatgpt_service_pb2 import (
    GetRawNotesRequest, GetRawNotesResponse
)
from munch import munchify
from yaml import safe_load
import grpc


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
          for request in request_iterator:
            raw_request_iter = iter([
                GetRawNotesRequest(
                    video=request.video,
                    presentation=request.presentation
                )
            ])
            raw_responses: Iterator[GetRawNotesResponse] = self.stub.GetRawNotes(raw_request_iter)
            for raw_resp in raw_responses:
                yield GetNotesResponse(notes=raw_resp.raw_notes.encode('utf-8'))
        