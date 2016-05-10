# ProxyServer
a proxy server by python

一个基于tornado开发的代理服务器：

依赖：python2.7或者python3.5，tornado4.x

安装：git clone git@github.com:panjf2000/ProxyServer.git

运行：python proxy_server.py -p 8888 -tp 80

-p参数代表代理端口（即proxy server要监听的端口），-tp参数代表转发端口（即proxy server实际转发到的端口）

结构：

ProxyServer/proxy_server.py        #server入口

ProxyServer/handler/               #tornado的转发类，负责转发请求以及处理response的数据

ProxyServer/custom_handler/        

二次开发：

之所以考虑用程序的方式来做代理而不是直接用Nginx来做代理，是因为用程序对转发的请求有较大的控制度，可以控制代理特定的请求，屏蔽特定的请求，甚至可以重写特定的请求。
另外，有时候项目需要用到第三方的服务并对返回的数据进行自定义修改，调用第三方的API（比如百度地图），利用proxy server可以很容易的控制第三方API返回的数据并进行自定义修改。

现在这个proxy server已经实现了最基本的内容转发代理，可以把转发端口的response完整地返回给代理端口，也可以进行二次开发，目前提供二次开发入口，若需要更复杂的转发或者需要适配特定项目需求的转发，
只需要修改ProxyServer/custom_handler/目录下的my_handler.py脚本的代码，修改MyHandler class中的静态方法on_response_handle(),在此方法中实现自己的需求即可，这个函数的实现可参考MyHandler class中的on_response_handle()函数。
还可以重写MyHandler class中的get()、post()、和put()等方法，然后在入口proxy_server.py脚本中，修改tornado的监听的RequestHandler为MyHandler,实现过滤request的需求。


