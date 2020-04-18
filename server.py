import os
from time import sleep
import grpc
from hashlib import sha256
from concurrent import futures
from stream import stream_pb2, stream_pb2_grpc
from baseClass import KeyValue
import numpy as np
from threading import Thread, Lock, RLock, Semaphore


# 用sha256生成令牌，登陆后访问服务器时携带此令牌做身份验证
def encryption(request, insert="19214963"):
    text = request.password + insert + request.username
    x = sha256()
    x.update(text.encode('utf-8'))
    token = x.hexdigest()
    return token


# reader and writer lock
class RWLock:
    def __init__(self, mode="ReaderFirst"):
        self.rw = Semaphore()  # 访问资源的信号量
        self.mutex = Semaphore()  # 访问读者个数的信号量
        self.reader = 0  # 读者个数
        self.writer = 0  # 写者个数（0或1）
        self.mode = mode  # 读写锁模式，可设置为读者优先或读写公平
        if self.mode not in ["ReaderFirst", "Fair"]:
            raise ValueError("The mode of Rwlock should either be ReaderFirst or Fair")
        if self.mode == "Fair":
            self.w = Semaphore()  # 如果模式为读写公平，需要多加一个信号量

    # 写者获取资源
    def writer_acquire(self):
        if self.mode == "Fair":
            self.w.acquire()
        self.rw.acquire()
        self.writer = 1

    # 写者释放资源
    def writer_release(self):
        self.rw.release()
        if self.mode == "Fair":
            self.w.release()
        self.writer = 0

    # 读者获取资源
    def reader_acquire(self):
        if self.mode == "Fair":
            self.w.acquire()
        self.mutex.acquire()
        if self.reader == 0:
            self.rw.acquire()
        self.reader += 1
        self.mutex.release()
        if self.mode == "Fair":
            self.w.release()

    # 读者释放资源
    def reader_release(self):
        self.mutex.acquire()
        if self.reader == 1:
            self.rw.release()
        self.reader -= 1
        self.mutex.release()

    # 若没有put、delete等函数没有插入sleep，则可能无法显示
    def show(self):
        print("writer:%d, reader:%d" % (self.writer, self.reader))

    def block_reason(self):
        pass


# 实现了服务器类，是程序的主体
class Server(stream_pb2_grpc.StreamServiceServicer):
    def __init__(self, address, neighbor, path, user, rw_mode="ReaderFirst", write_down=20):
        self.dict = KeyValue(path)  # 数据
        self.user = user  # 格式为用户名：{用户密码，是否有写权限}
        self.loginUser = {"admin": "Writer"}  # 登陆的用户,admin是服务器间相互传递信息的登录令牌
        self.rwlock = RWLock(rw_mode)  # 读写锁

        self.write_down = write_down # 发生一定次数写操作后统一保存，减少io次数
        self.write_counter = 0 # 当前的写操作次数

        self.address = address
        self.neighbor = neighbor
        self.temp = [None, None, 0]

    def get(self, request, context):
        authError = self.auth(request, True)
        if authError != "Ok":
            return stream_pb2.Response1(message=authError)
        self.rwlock.reader_acquire()
        message, value = self.dict.get(request.key)
        self.rwlock.reader_release()
        print(message)
        return stream_pb2.Response1(message=message, value=value)

    def put(self, request, context):
        print(self.temp)
        if self.temp[0] is not None:
            self.broadcast()
        authError = self.auth(request, False)
        if authError != "Ok":
            return stream_pb2.Response2(message=authError)
        self.rwlock.writer_acquire()
        sleep(2)  # 延时以显示writer和reader个数
        message = (self.dict.put(request.key, request.value))
        self.save_change()
        self.rwlock.writer_release()
        #print(self.rwlock.writer)
        self.temp = ["put", request.key, request.value]
        print(message)
        return stream_pb2.Response2(message=message)

    def delete(self, request, context):
        if self.temp[0] is not None:
            self.broadcast()
        authError = self.auth(request, False)
        if authError != "Ok":
            return stream_pb2.Response3(message=authError)
        self.rwlock.writer_acquire()
        message = (self.dict.delete(request.key))
        self.save_change()
        self.rwlock.writer_release()
        self.temp = ["del", request.key, 0]
        print(message)
        return stream_pb2.Response3(message=message)

    def show(self, request, context):
        authError = self.auth(request, True)
        if authError != "Ok":
            return stream_pb2.Response4(message=authError)
        self.rwlock.reader_acquire()
        sleep(2)  # 延时以显示writer和reader个数
        data = self.dict.show()
        self.rwlock.reader_release()
        message = "Read successfully."
        print(message)
        return stream_pb2.Response4(message=message, data=data)

    # 用户登录，返回令牌，登录信息，登录身份
    def login(self, request, context):
        token = None
        type = None
        if not (self.user.__contains__(request.username) and self.user[request.username][0] == request.password):
            message = "Authorization failed."
        else:
            message = "Authorization passed "
            if request.type == "" or request.type.lower() == "writer":
                if self.user[request.username][1] == 1:
                    message += "and set the type successfully."
                    type = "Writer"
                    token = encryption(request)
                    self.loginUser[token] = type
                else:
                    message += "but failed to set the type. You don't have permission to set the type as \"writer\"."
            elif request.type.lower() == "reader":
                message += "and set the type successfully."
                type = "Reader"
                token = encryption(request)
                self.loginUser[token] = type
            else:
                message += "but failed to set the type. " \
                           "The type of user can either be \"reader\" or \"writer\"(default: \"writer\")."
        return stream_pb2.Response5(message=message, type=type, token=token)

    # 身份校验
    def auth(self, request, read_only=False):
        if request.auth not in self.loginUser:
            return "Authorization failed."
        elif not read_only and self.loginUser[request.auth] == "Reader":
            return "You don't have permission to write."
        else:
            return "Ok"

    # 写操作一定次数后，统一写入磁盘
    def save_change(self):
        self.write_counter += 1
        if self.write_counter == self.write_down:
            self.dict.save()
            self.write_counter = 0

    # 在上面函数的基础上的自定义读取
    def myshow(self, request, context):
        data = self.show(request, context)
        return stream_pb2.Response00(message=data.message, data=data.data)

    # 在上面函数的基础上的自定义写入
    def mychange(self, request, context):
        data = self.put(request, context)
        return stream_pb2.Response01(message=data.message)

    # 在本次写操作前广播上一次的写操作
    def broadcast(self):
        if self.neighbor is not None:
            for address in self.neighbor:
                with grpc.insecure_channel(address) as conn:
                    client = stream_pb2_grpc.StreamServiceStub(channel=conn)
                    if self.temp[0] == "put":
                        response = client.put(stream_pb2.Request2(key=self.temp[1], value=self.temp[2], auth="admin"))
                    else:
                        response = client.delete(stream_pb2.Request3(key=self.temp[1], auth="admin"))
                    print(address, response.message)
                    conn.close()


# 运行一个服务器，端口9600
def test_grpc():
    grpcServer = grpc.server(futures.ThreadPoolExecutor(max_workers=5))
    user = {"carter": ["337790", 1], "susan": ["332211", 1], "milan": ["332211", 0]}
    s = Server(address="localhost:9600", neighbor=["localhost:9601", "localhost:9602"], path='mydict', user=user, rw_mode="Fair")
    stream_pb2_grpc.add_StreamServiceServicer_to_server(s, grpcServer)

    grpcServer.add_insecure_port(s.address)
    grpcServer.start()

    while True:
        try:
            sleep(3)
            print(s.dict.db)
            # s.rwlock.show()  #  测试读者写者时使用
        except KeyboardInterrupt:
            grpcServer.stop(None)


if __name__ == '__main__':
    path = "/project/keyValue"  # 改成你存放的目录
    os.system('cd %s/stream/ && '
              'python -m grpc_tools.protoc -I. --python_out=. --grpc_python_out=. ./stream.proto' % path)

    test_grpc()
