# 链家地铁房交易价格爬虫项目
该项目可用于爬取登记在链家网站上按地铁线路分布的小区历史交易价格，并以年为单位计算出平均价格记录在本地。当然，该项目也能改写成爬取地铁房所有交易记录。

该项目会在工作路径下创建'id_list.txt'，'cookies.txt','result.txt','result.csv','Predicted_result.csv','aver_rating.txt'文件。
## 文件内容
id_list.txt文件包含了需要爬取的地铁房所在小区id，你可以以形如''https://gz.lianjia.com/xiaoqu/'+ id_list()来访问该小区页面。

cookies.txt文件为登陆链家的cookie文件，当程序多次无法正常运行时需要删除该文件

result.txt和result.csv为爬取出小区年平均交易价格的原始数据，单位为元/m²。
    
aver_rating.txt文件为统计所爬取小区数据计算出沿地铁线小区交易价格年增长率。

Predicted_result.csv文件为以aver_rating.txt文件为基础进行预测，补全小区空缺年份交易价格。

## 使用方法
在命令行界面输入pip install -r requirement.txt安装项目所需依赖。

用编辑器打开‘链家地铁房价格爬取.py’，在全局变量path中写入工作路径，在need_call中写入所需爬取的地铁房链接。

安装edge浏览器，如无法正常运行程序，安装与edge浏览器版本号匹配的msedgediver并将可执行文件msedgediver所在的文件夹添加到你的 PATH 环境变量。

在弹出的登陆窗口登陆链家网站，获得登陆cookie。注意，该登陆cookie并不是永久的，如出现AttributeError: 'NoneType' object has no attribute 'find'错误，考虑删除工作路径的cookies.txt文件，重新开始程序登陆。

由于模拟打开链家网站时间较长，请确定网络稳定。如遇到网络问题导致程序断开，可以从已有result.txt文件中查看当前进度，在id_list文件中删除已下载id，并将已有result.txt文件重命名，，可以从上次未下载地方开始运行。

**注意：程序断开会导致出现的result.csv和aver_rating.txt和Predicted_result.csv文件都不完整，请尽量一次性完成。**

## 未来计划
- [ ] 完成断点续传的功能
    
- [ ] 实现多链接写入

- [ ] 实现cookie过期自动重新登录

- [ ] 考虑其他方式实现预测小区缺失数据

- [ ] 重构一部分代码

- [ ] 写注释

