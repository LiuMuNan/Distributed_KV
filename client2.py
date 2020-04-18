import grpc
from time import sleep
from stream import stream_pb2, stream_pb2_grpc


# 客户端，读者1
def test_grpc():

    with grpc.insecure_channel("localhost:9600") as conn:
        client = stream_pb2_grpc.StreamServiceStub(channel=conn)
        response = client.login(stream_pb2.Request5(username="susan", password="332211", type="reader"))
        token = response.token
        print(response.message)

        while True:
            try:
                # 读取所有数据
                response = client.myshow(stream_pb2.Request00(auth=token))
                print(response.message, response.data)
            except KeyboardInterrupt:
                conn.close()


if __name__ == '__main__':
    test_grpc()
