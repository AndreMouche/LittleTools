##概述

该项目是在调研bpg时，顺手搭的web服务。东西很简单，大概耗时一个晚上。做此只是简单记录，意在方便今后类似的工作，也可以看做beego的demo项目。

##BPGManager项目简介
 
该项目通过搭建简单的问卷系统，调研同效果图片，不同格式之间大小差距。
  
使用转码工具，分别转出与原图jpg显示效果尽量接近的bpg,webp图片，查看其大小变化

###具体执行步骤

1. 准备50张线上图片作为样本，分别将其转为quality统一为75的jpg图片
2. 以一张jpg为原图，调整参数分别转出与原图尽量接近的bpg,webp图片
3. 使用步骤2的转码参数，转出剩余jpg图片的对应格式
4. 检查当前结果图片中各组图片的差异，若存在，继续步骤2
5. 准备问卷：编写基于golang [beego](http://beego.me/quickstart)的webp服务器，提供问卷及相关数据收集工作
6. 根据问卷结果，整理收集相关数据

## 服务搭建

### 编译项目

1. 安装[beego](http://beego.me/quickstart)
2. 编译项目

```
   go build main.go
```

###启动服务

指定静态页面static所在目录的父目录绝对路径作为 -d参数
```
   ./main -d=`pwd`
```

###相关页面

1. 问卷[http://localhost:8080/t/vote/s3](http://localhost:8080/t/vote/s3)
2. 问卷结果图片格式 [http://localhost:8080/t/vote/s3](http://localhost:8080/t/result/s3)
3. 问卷统计  [http://localhost:8080/t/stat](http://localhost:8080/t/stat)
4. 同质量图片筛选案例 [http://115.236.113.201/t/result/test5](http://115.236.113.201/t/result/test5)