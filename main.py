import logging
from concurrent import futures
import grpc
from backend_service import backend_service_pb2_grpc
from yaml import safe_load
from munch import munchify
from server.server import BackendServiceServicer


def serve() -> None:
    with open('config.yml') as cfg:
        config = munchify(safe_load(cfg))
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    backend_service_pb2_grpc.add_BackendServiceServicer_to_server(
        BackendServiceServicer(), server
    )
    server.add_insecure_port(config.server_grpc.addr) 
    server.start()
    server.wait_for_termination()

if __name__ == '__main__':
    logging.basicConfig()
    serve()