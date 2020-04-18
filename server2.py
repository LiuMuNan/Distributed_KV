import grpc
from time import sleep
from stream import stream_pb2, stream_pb2_grpc
from server import Server
import concurrent.futures as futures


# 运行一个服务器，端口9601
def test_grpc():
    grpcServer = grpc.server(futures.ThreadPoolExecutor(max_workers=5))     #开启一个grpc服务器，接收消息
    user = {"carter": ["337790", 1], "susan": ["332211", 1], "milan": ["332211", 0]}     #用户列表
    s = Server(address="localhost:9601", neighbor=["localhost:9600", "localhost:9602"], path='mydict2', user=user)    #
    stream_pb2_grpc.add_StreamServiceServicer_to_server(s, grpcServer)      #给服务器添加服务

    grpcServer.add_insecure_port(s.address)        #给服务器添加端口
    grpcServer.start()      #开始服务

    while True:
        try:
            sleep(2)
            print(s.dict.db)
        except KeyboardInterrupt:
            grpcServer.stop(None)


if __name__ == '__main__':
    test_grpc()
