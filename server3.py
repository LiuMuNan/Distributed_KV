import grpc
from time import sleep
from stream import stream_pb2, stream_pb2_grpc
from server import Server
import concurrent.futures as futures


# 运行一个服务器，端口9602
def test_grpc():
    grpcServer = grpc.server(futures.ThreadPoolExecutor(max_workers=5))
    user = {"carter": ["337790", 1], "susan": ["332211", 1], "milan": ["332211", 0]}
    s = Server(address="localhost:9602", neighbor=["localhost:9600", "localhost:9601"], path='mydict2', user=user)
    stream_pb2_grpc.add_StreamServiceServicer_to_server(s, grpcServer)

    grpcServer.add_insecure_port(s.address)
    grpcServer.start()

    while True:
        try:
            sleep(3)
            print(s.dict.db)
        except KeyboardInterrupt:
            grpcServer.stop(None)


if __name__ == '__main__':
    test_grpc()
