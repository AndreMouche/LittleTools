## GOTO Host

该脚本用于方便地ssh到其它机器

### 安装

1.将hosts里面的文件内容为需要配置ssh的服务器，信息填写格式如下

```
baidu 10.112.123.132 ubuntu baidu.com
web_online 10.25.239.124 ubuntu www.web.com
web_test 10.15.14.22 ubuntu test.web.com
test 10.11.11.213 ubuntu test
```
即：

|host名称|登陆IP|登陆账号|备注信息|
|:---|:---|:---|:---|
|baidu|10.112.123.132|ubuntu|baidu.com|
|web_online|10.25.239.124|ubuntu|www.web.com|
|web_test|10.15.14.22|ubuntu|test.web.com|
|test|10.11.11.213|ubuntu|test|

2.配置无密码访问以上机器权限
即：

* 本机通过ssh-keyge生成公私钥
* 将本机公钥拷贝到服务器的/home/ubuntu/.ssh/authorized_keys里
* 本机ssh服务器，能无密码访问则为成功

3.将goto里面的gotohosts改成以上文件的绝对地址

```
#!/bin/bash
gotohosts="/path/to/hosts"
```

给goto文件添加执行权限，并将文件拷贝到/user/local/bin下

```
chmod +x goto
cp goto /usr/local/bin/
```

4.执行goto

```
goto
Usage:./goto host
Avaiable hostlist:
10.112.123.132	-- baidu (baidu.com) 
10.25.239.124	-- web_online (www.web.com) 
10.15.14.22	-- web_test (test.web.com) 
10.11.11.213	-- test (test) 

```

如想要跳到10.112.123.132机器上，执行

```
goto baidu
```
