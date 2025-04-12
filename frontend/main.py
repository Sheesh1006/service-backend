import os
import json
import tempfile
import shutil
from http.server import SimpleHTTPRequestHandler, HTTPServer
from urllib.parse import unquote, urlparse
import grpc
from email.parser import BytesParser
from email.policy import HTTP
from concurrent import futures

# Импорт сгенерированных gRPC модулей
from gen import chatgpt_service_pb2
from gen import chatgpt_service_pb2_grpc

PORT = 8000
GRPC_SERVER_ADDRESS = "localhost:50051"

class ChatGPTServiceClient:
    def __init__(self):
        self.channel = grpc.insecure_channel(GRPC_SERVER_ADDRESS)
        self.stub = chatgpt_service_pb2_grpc.ChatGPTServiceStub(self.channel)
    
    def generate_notes(self, video_path=None, presentation_path=None):
        """Отправляет запрос в ML-сервис через gRPC"""
        try:
            request = chatgpt_service_pb2.GetRawNotesRequest(
                video=1 if video_path else 0,
                presentation=1 if presentation_path else 0
            )
            response = self.stub.GetRawNotes(request, timeout=30.0)
            return response
        except grpc.RpcError as e:
            raise Exception(f"gRPC Error [{e.code()}]: {e.details()}")

class MyHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        self.grpc_client = ChatGPTServiceClient()
        super().__init__(*args, directory="frontend/static", **kwargs)
    
    def parse_multipart(self, content_type):
        """Современная замена cgi.FieldStorage для обработки multipart/form-data"""
        content_length = int(self.headers.get('Content-Length', 0))
        post_data = self.rfile.read(content_length)
        
        parser = BytesParser(policy=HTTP)
        message = parser.parsebytes(
            b'Content-Type: ' + content_type.encode() + b'\r\n\r\n' + post_data
        )
        
        form_data = {}
        for part in message.iter_parts():
            name = part.get_param('name', header='content-disposition')
            if part.get_filename():  # Это файл
                form_data[name] = [part.get_payload(decode=True)]
            else:  # Обычное поле
                form_data[name] = [part.get_payload(decode=True)]
        
        return form_data

    def do_POST(self):
        if self.path == '/api/process':
            temp_dir = None
            try:
                # Проверка Content-Type
                content_type = self.headers.get('Content-Type', '')
                if not content_type.startswith('multipart/form-data'):
                    raise ValueError("Only multipart/form-data is supported")
                
                # Создание временной директории
                temp_dir = tempfile.mkdtemp()
                video_path, presentation_path = None, None
                
                # Парсинг данных формы
                form_data = self.parse_multipart(content_type)
                
                # Обработка видео
                if 'video_file' in form_data:
                    video_path = os.path.join(temp_dir, 'video.mp4')
                    with open(video_path, 'wb') as f:
                        f.write(form_data['video_file'][0])
                elif 'video_url' in form_data:
                    video_url = form_data['video_url'][0].decode('utf-8')
                    if not self.is_valid_url(video_url):
                        raise ValueError("Invalid video URL format")
                
                # Обработка презентации
                if 'presentation_file' in form_data:
                    presentation_path = os.path.join(temp_dir, 'presentation.pdf')
                    with open(presentation_path, 'wb') as f:
                        f.write(form_data['presentation_file'][0])
                
                # Вызов gRPC сервиса
                response = self.grpc_client.generate_notes(
                    video_path=video_path,
                    presentation_path=presentation_path
                )
                
                # Успешный ответ
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({
                    "status": "success",
                    "message": "Processing completed",
                    "download_url": f"/download/{response.result_id}.pdf"
                }).encode())
                
            except Exception as e:
                self.send_error(500, str(e))
            finally:
                if temp_dir and os.path.exists(temp_dir):
                    shutil.rmtree(temp_dir)
        else:
            self.send_error(404, "Endpoint not found")
    
    def is_valid_url(self, url):
        try:
            result = urlparse(url)
            return all([result.scheme, result.netloc])
        except ValueError:
            return False

def run_server():
    server_address = ('', PORT)
    httpd = HTTPServer(server_address, MyHandler)
    print(f'Server running at http://localhost:{PORT}')
    httpd.serve_forever()

if __name__ == '__main__':
    # Проверка наличия gRPC сервера
    try:
        channel = grpc.insecure_channel(GRPC_SERVER_ADDRESS)
        grpc.channel_ready_future(channel).result(timeout=5)
        print(f"Connected to gRPC server at {GRPC_SERVER_ADDRESS}")
    except grpc.FutureTimeoutError:
        print(f"Warning: gRPC server not available at {GRPC_SERVER_ADDRESS}")
    
    run_server()