import grpc
import numpy as np
from stream import stream_pb2, stream_pb2_grpc


# 客户端，写者1
def test_grpc():
    with grpc.insecure_channel("localhost:9600") as conn:   #打开
        client = stream_pb2_grpc.StreamServiceStub(channel=conn)      #构造一个通信类
        response = client.login(stream_pb2.Request5(username="carter", password="337790", type="writer"))    #调用login方法
        token = response.token      #返回token
        print(response.message)

        while True:
            try:
                # 随机更改bike的值
                value = np.random.random_integers(1, 1000)
                response = client.mychange(stream_pb2.Request01(key='bike', value=value, auth=token))
                print(value, response.message)
            except KeyboardInterrupt:
                print("结束")
                conn.close()
    # print(client.get(stream_pb2.Request1(key="coke")).message)
    # print(client.put(stream_pb2.Request2(key="coke", value=19)).message)
    # print(client.delete(stream_pb2.Request3(key="coke")).message)
    # print(client.show(stream_pb2.Request4()).message)


if __name__ == '__main__':
    test_grpc()
