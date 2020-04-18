本项目实现了一个基础的分布式键值系统，使用grpc进行通信

stream是grpc的代码，其中stream.proto是自己编写的函数输入输出格式，剩余两个是自动生成的代码文件

baseClass是对python字典的简单封装，供主程序调用
server是程序的主体，实现了服务器类

运行server,server2,server3以启动三个服务器节点
运行client,client2,client3以启动三个用户节点，其中，client执行写操作，client2、client3执行读操作
请确保在启动用户端之前运行服务器端，避免用户端报错

mydict、mydict2是字典的本地存储，供文件读取

更加详细的注释和说明在各份代码中，请查阅

Raft的实现在另一个压缩包中


