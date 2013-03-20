###Weibo-Spy
微博自身的发展，导致信息冗余，很多时候并不想看到那么多信息；

更多的时候，总有一个人或者几个人特别关注，想知道他/她最近做了什么；

于是弄了这个小东西练手。

实现对于设置的账户，在一个设定的时间内查询该微博，若有新微博产生，则自动将新微博内容作为邮件发送到指定邮箱。

本应用需要GAE帐号，新浪开发者帐号，邮箱；

在config.py中，设置你的新浪开发者帐号，就直接申请一个OK了；邮件地址From填你的GAE帐号，To随便填那个想接收的帐号；

app.yaml中填写你的APP-ID；

cron.yaml中填写你想要的时间间隔，默认每四小时一次；

上传成功后，打开你的APP应用，设置。可以多设置几个关注人；每次有信息都是按照以关注人为主题，分别发送邮件；

没有做删除跟踪的功能，只要进GAE管理台，自己删数据就OK了。

新浪Oauth认证学习了这份[源码](https://github.com/PinkyJie/Twitter2Sina)。

###UPDATE 2013.3.20

这个东西完成后不久，新浪就把认证迁移到OAUTH2去了。

现在也能支持了。

用了[廖雪峰](http://www.liaoxuefeng.com/articles)的 [sdk](https://github.com/michaelliao/sinaweibopy/wiki/OAuth2-HOWTO)。在此感谢。
