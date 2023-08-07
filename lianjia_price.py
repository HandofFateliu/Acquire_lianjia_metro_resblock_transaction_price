from selenium.webdriver.edge.options import Options
from bs4 import BeautifulSoup
from time import sleep
import requests
from selenium import webdriver
import json
import os
import math
import pandas as pd
import csv

# 工作路径
path = 'D:\\'
# 地铁房链接
need_call = 'https://gz.lianjia.com/ditiefang/li2120036910023169/pg'

x_pi = math.pi * 3000.0 / 180.0
a = 6378245.0  # // 长半轴
ee = 0.00669342162296594323  # // 扁率

# 获取所需地铁房小区id并填入列表
def fill_id_list(catch_url):
    id_list = list()
    # 链家页数上限为100页
    for i in range(1,101):
        need_call = catch_url + str(i) + '/'
        r = requests.get(need_call)
        r.encoding = r.apparent_encoding
        bs = BeautifulSoup(r.text, 'html.parser')
        bs1 = bs.body.find(class_ = 'sellListContent')

        for child in bs1.children:
            # 循环获取子节点，'data-lj_action_resblock_id'的值为所需要的
            li1 = child.attrs
            resbolck_id_not_exist = True
            # 获取小区节点会有大量重复
            for j in range (len(id_list)) :
                # 写入前对比列表中已经存在的元素
                if (li1['data-lj_action_resblock_id'] == id_list[j] ):
                    resbolck_id_not_exist = False
            # ！标记不为1，就写入（可以试着用bool型重写，让代码更易读）
            if (resbolck_id_not_exist):
                id_list.append(li1['data-lj_action_resblock_id'])
    return id_list

def save_id_list(id_list):
    with open( path + 'id_list.txt', 'w') as file:
    # 请不要使用csv，id写入csv会造成数据溢出错误
        for i in range(len(id_list)-1):
            file.write( id_list[i] + '\n' )
        file.write(id_list[len(id_list)-1])
    return 0

def read_id_list():
    id_list = list()
    with open( path + 'id_list.txt', 'r') as file:
        # 读取第一行
        line = file.readline() 
        while line:
            # 可将字符串变为元组
            txt_data = eval(line) 
            # 列表增加
            id_list.append(txt_data) 
            # 读取下一行
            line = file.readline() 
    return id_list

def get_name(id):
    r = requests.get( 'https://gz.lianjia.com/xiaoqu/' + id )
    r.encoding = r.apparent_encoding
    bs = BeautifulSoup(r.text, 'html.parser')
    bs1 = bs.body.find(class_ = 'detailTitle')
    xiaoqu_name = str(bs1)
    xiaoqu_name = xiaoqu_name.replace('<h1 class="detailTitle">','',1)
    xiaoqu_name = xiaoqu_name.replace('</h1>','',1)
    return xiaoqu_name

def get_detail_name(id):
    r = requests.get( 'https://gz.lianjia.com/xiaoqu/' + id )
    r.encoding = r.apparent_encoding
    bs = BeautifulSoup(r.text, 'html.parser')
    bs1 = bs.body.find(class_ = 'detailDesc')
    xiaoqu_name = str(bs1)
    xiaoqu_name = xiaoqu_name.replace('<div class="detailDesc">','',1)
    xiaoqu_name = xiaoqu_name.replace('</div>','',1)
    return xiaoqu_name


def get_baiducoord(id):
    r = requests.get( 'https://gz.lianjia.com/xiaoqu/' + id )
    r.encoding = r.apparent_encoding
    bs = BeautifulSoup(r.text, 'html.parser')
    bs1 = bs.body.find(type = 'text/javascript')
    x = str(bs1)
    y = x.index('resblockPosition:\'')
    z = x.index('\',\n    resblockName')
    output = x[y + 18 : z]
    coords = [output.split(',')[0],output.split(',')[1]]
    return coords

# 将交易日期和交易时间写入列表
def enter_and_get_dealDate_unitPrice(id):
    catch_url = 'https://gz.lianjia.com/chengjiao/c' + id
    # 打开保存的cookie文件
    with open(( path + 'cookies.txt'),'r') as f:
        cookies_file = f.read()
    # 将读取的文件转为json格式
    cookie_list = json.loads(cookies_file)
    # 这些设置可能提高网页打开速度
    my_options = webdriver.EdgeOptions()
    my_options.page_load_strategy = 'eager'
    my_options.add_argument('--ignore-certificate-errors')
    # 打开浏览器
    browser = webdriver.Edge(options=my_options)
    # 打开与链家有关的网址
    start_url = 'https://gz.lianjia.com/'
    browser.get(start_url)
    # 加载cookie
    #  打开并读取链家网站是一个漫长的过程，请耐心
    for cookie in cookie_list:
        browser.add_cookie(cookie)
    dealDate_list = []
    unitprice_list = []
    # 页数上限为100
    for i in range(1,101):
        page_url2 = catch_url + 'pg' +str(i)
        browser.get(page_url2)
        sleep(0.2)
        r = browser.page_source
        bs = BeautifulSoup(r, 'html.parser')
        bs1 = bs.body.find(class_ = 'listContent')
        # ！设置标记（看看能不能bool重写），该标记关于该小区目前交易页面是否有数据
        flag = bs1.find('li') or 0  
        if flag == 0:
            break
        else:
            for child in bs1.children:
                dealDate = str(child.find(class_ = 'dealDate'))
                unitPrice = str(child.find(class_ = 'unitPrice').find(class_ = 'number'))
                dealDate = dealDate.replace('<div class="dealDate">','',1)
                dealDate = dealDate.replace('</div>','',1)
                dealDate_list.append(dealDate)
                unitPrice = unitPrice.replace('<span class="number">','',1)
                unitPrice = unitPrice.replace('</span>','',1)
                unitprice_list.append(unitPrice)
    # 将其压成字典便于传输，看起来简洁
    date_price = dict(zip(dealDate_list, unitprice_list))
    return calculate_unit_price(date_price)


# 计算年平均成交价格
def calculate_unit_price(date_price):
    # 需要被统计的年份，链家数据仅到2016年
    years_need_summarize = [2023,2022,2021,2020,2019,2018,2017,2016]
    # 建立交易次数和交易总额字典，以年份做键，值填充0
    deal_num = dict.fromkeys(years_need_summarize,0)
    deal_sum = dict.fromkeys(years_need_summarize,0)
    for date in date_price.keys():
        # 从日期字符串中分割出所需的年份字符串
        year = date.split('.')[0]
        #将传入值和年份匹配
        for i in range(2023,2015,-1):
            # 更新年交易总量和年交易次数字典
            if year == str(i):
                deal_sum[i] = deal_sum[i] + int(date_price[date])
                deal_num[i] = deal_num[i] + 1
    #年平均交易价格            
    aver_year = []
    for i in range(2023,2015,-1):
        if deal_num[i] == 0 :
            aver_year.append(0)
        else:
            aver_year.append(deal_sum[i]/deal_num[i]) 
    aver_year_dict = dict(zip(years_need_summarize, aver_year))
    return aver_year_dict

def bd09towgs84(baiducoord):
    hx = bd09togcj02(baiducoord)
    wgs84 = gcj02towgs84(hx)
    return wgs84

def bd09togcj02(baiducoord):
    x = float(baiducoord[0]) - 0.0065
    y = float(baiducoord[1]) - 0.006
    z = math.sqrt(x * x + y * y) - 0.00002 * math.sin(y * x_pi)
    theta = math.atan2(y, x) - .000003 * math.cos(x * x_pi)
    hx = [0,0]
    hx[0] = z * math.cos(theta)
    hx[1] = z * math.sin(theta)
    return hx

def gcj02towgs84(hx):
    dlat = transformlat(hx[0] - 105.0, hx[1] - 35.0)
    dlng = transformlng(hx[0] - 105.0, hx[1] - 35.0)
    radlat = hx[0] / 180.0 * math.pi
    magic = math.sin(radlat)
    magic = 1 - ee * magic * magic
    sqrtmagic = math.sqrt(magic)
    dlat = (dlat * 180.0) / ((a * (1 - ee)) / (magic * sqrtmagic) * math.pi)
    dlng = (dlng * 180.0) / (a / sqrtmagic * math.cos(radlat) * math.pi)
    wgs84 = [0,0]
    mglat = hx[1] + dlat
    mglng = hx[0] + dlng
    wgs84[1] = hx[1] * 2 - mglat
    wgs84[0] = hx[0] * 2 - mglng
    return wgs84

# /*辅助函数*/
# //转换lat
def transformlat(lng: float, lat: float) -> float:
    ret = -100.0 + 2.0 * lng + 3.0 * lat + 0.2 * lat * \
        lat + 0.1 * lng * lat + 0.2 * math.sqrt(abs(lng))
    ret += (20.0 * math.sin(6.0 * lng * math.pi) + 20.0 *
            math.sin(2.0 * lng * math.pi)) * 2.0 / 3.0
    ret += (20.0 * math.sin(lat * math.pi) + 40.0 *
            math.sin(lat / 3.0 * math.pi)) * 2.0 / 3.0
    ret += (160.0 * math.sin(lat / 12.0 * math.pi) + 320 *
            math.sin(lat * math.pi / 30.0)) * 2.0 / 3.0
    return ret


# /*辅助函数*/
# //转换lng
def transformlng(lng: float, lat: float) -> float:
    ret = 300.0 + lng + 2.0 * lat + 0.1 * lng * lng + \
        0.1 * lng * lat + 0.1 * math.sqrt(abs(lng))
    ret += (20.0 * math.sin(6.0 * lng * math.pi) + 20.0 *
            math.sin(2.0 * lng * math.pi)) * 2.0 / 3.0
    ret += (20.0 * math.sin(lng * math.pi) + 40.0 *
            math.sin(lng / 3.0 * math.pi)) * 2.0 / 3.0
    ret += (150.0 * math.sin(lng / 12.0 * math.pi) + 300.0 *
            math.sin(lng / 30.0 * math.pi)) * 2.0 / 3.0
    return ret

def is_cookie_exists():
    if os.path.exists(path + 'cookies.txt'):
        return True
    else:
        return False

def save_cookies():
    if not os.path.exists(path + 'cookies.txt'):
        lianjia_url = 'https://gz.lianjia.com/chengjiao/(pg2)c2111103316366/'
        browser = webdriver.Edge()
        browser.get(lianjia_url)
        print('请在60秒内完成登录')
        sleep(60)
        cookies = browser.get_cookies()
        with open(os.path.join(path,path= path + 'cookie.txt'),mode='w') as f:
            f.write(json.dumps(cookies))
        browser.close()

def save_data(id_list):
    with open( path + 'result.txt','w', encoding='utf-8') as file:
        title_list = ['xiaoqu_id','xiaoqu_name','xiaoqu_detail_name','baiducoord_x','baiducoord_y','1984coord_x','1984coord_y','aver_2023','aver_2022','aver_2021','aver_2020','aver_2019','aver_2018','aver_2017','aver_2016']
        file.write(";".join(title_list))
        #写抬头
        for id in range (len(id_list)):
            print (str(id + 1) + '/' + str(len(id_list)))
            # id 在csv中会读写错误，请无视这个错误。
            # 如需要，可以从之前的记事本中查看id
            xiaoqu_id = str(id_list [id])
            # 名字
            xiaoqu_name = get_name(xiaoqu_id)
            # 详细名字
            xiaoqu_detail_name = get_detail_name(xiaoqu_id)
            # 坐标
            baidu_coords = get_baiducoord(xiaoqu_id)
            WGS84 = bd09towgs84(baidu_coords)
            WGS84_x = WGS84 [0]
            WGS84_y = WGS84 [1]
            # 进入链家,并且获得交易日期和金额
            aver_year = enter_and_get_dealDate_unitPrice(xiaoqu_id)
            file.write("\n")
            file.write(xiaoqu_id)
            file.write(";")
            file.write(xiaoqu_name)
            file.write(";")
            file.write(xiaoqu_detail_name)
            file.write(";")
            file.write(baidu_coords[0])
            file.write(";")
            file.write(baidu_coords[1])
            file.write(";")
            file.write(str(WGS84_x))
            file.write(";")
            file.write(str(WGS84_y))
            file.write(";")
            file.write(str(aver_year[2023]))
            file.write(";")
            file.write(str(aver_year[2022]))
            file.write(";")
            file.write(str(aver_year[2021]))
            file.write(";")
            file.write(str(aver_year[2020]))
            file.write(";")
            file.write(str(aver_year[2019]))
            file.write(";")
            file.write(str(aver_year[2018]))
            file.write(";")
            file.write(str(aver_year[2017]))
            file.write(";")
            file.write(str(aver_year[2016]))
    return 0

def predict_statistic():
    df = pd.read_csv( path + 'result.csv',encoding='utf-8')
    dataframe_length = len(df)
    
    all_house_price_every_year_list = list()
    rating_23_22 = list()
    rating_22_21 = list()
    rating_21_20 = list()
    rating_20_19 = list()
    rating_19_18 = list()
    rating_18_17 = list()
    rating_17_16 = list()

    for i in range(dataframe_length):
        per_house_price_every_year_list = list()
        for j in range (7,15):
            per_house_price_every_year_list.append(float(df.loc[i][j]))
        all_house_price_every_year_list.append(per_house_price_every_year_list)

    for i in range(dataframe_length):
        if(all_house_price_every_year_list[i][0] == 0 or all_house_price_every_year_list[i][1] == 0):
            pass
        else:
            rating = all_house_price_every_year_list[i][0] / all_house_price_every_year_list[i][1]
            rating_23_22.append(rating)

        if(all_house_price_every_year_list[i][1] == 0 or all_house_price_every_year_list[i][2] == 0):
            pass
        else:
            rating = all_house_price_every_year_list[i][1] / all_house_price_every_year_list[i][2]
            rating_22_21.append(rating)

        if(all_house_price_every_year_list[i][2] == 0 or all_house_price_every_year_list[i][3] == 0):
            pass
        else:
            rating = all_house_price_every_year_list[i][2] / all_house_price_every_year_list[i][3]
            rating_21_20.append(rating)

        if(all_house_price_every_year_list[i][3] == 0 or all_house_price_every_year_list[i][4] == 0):
            pass
        else:
            rating = all_house_price_every_year_list[i][3] / all_house_price_every_year_list[i][4]
            rating_20_19.append(rating)

        if(all_house_price_every_year_list[i][4] == 0 or all_house_price_every_year_list[i][5] == 0):
            pass
        else:
            rating = all_house_price_every_year_list[i][4] / all_house_price_every_year_list[i][5]
            rating_19_18.append(rating)

        if(all_house_price_every_year_list[i][5] == 0 or all_house_price_every_year_list[i][6] == 0):
            pass
        else:
            rating = all_house_price_every_year_list[i][5] / all_house_price_every_year_list[i][6]
            rating_18_17.append(rating)

        if(all_house_price_every_year_list[i][6] == 0 or all_house_price_every_year_list[i][7] == 0):
            pass
        else:
            rating = all_house_price_every_year_list[i][6] / all_house_price_every_year_list[i][7]
            rating_17_16.append(rating)

    aver_rating_23_22 = sum(rating_23_22)/len(rating_23_22)
    aver_rating_22_21 = sum(rating_22_21)/len(rating_22_21)
    aver_rating_21_20 = sum(rating_21_20)/len(rating_21_20)
    aver_rating_20_19 = sum(rating_20_19)/len(rating_20_19)
    aver_rating_19_18 = sum(rating_19_18)/len(rating_19_18)
    aver_rating_18_17 = sum(rating_18_17)/len(rating_18_17)

    if(len(rating_17_16) == 0 ):
        aver_rating_17_16 = 0
    else:
        aver_rating_17_16 = sum(rating_17_16)/len(rating_17_16)

    for i in range(dataframe_length):
        flag1 = [0,0,0,0,0,0,0,0]
        for l in range(99):
            if(all_house_price_every_year_list[i][0] == 0):
                if(all_house_price_every_year_list[i][1] == 0):
                    pass
                else:
                    all_house_price_every_year_list[i][0] = all_house_price_every_year_list[i][1] * aver_rating_23_22
            else: 
                flag1[0] = 1

            if(all_house_price_every_year_list[i][1] == 0):
                if(all_house_price_every_year_list[i][0] == 0 and all_house_price_every_year_list[i][2] == 0):
                    pass
                elif(all_house_price_every_year_list[i][0] == 0):
                    all_house_price_every_year_list[i][1] = all_house_price_every_year_list[i][2] * aver_rating_22_21
                elif(all_house_price_every_year_list[i][2] == 0):
                    all_house_price_every_year_list[i][1] = all_house_price_every_year_list[i][0]/aver_rating_23_22
                else:
                    all_house_price_every_year_list[i][1] = all_house_price_every_year_list[i][0]/aver_rating_23_22*0.5 + all_house_price_every_year_list[i][2]*aver_rating_22_21*0.5

            if(all_house_price_every_year_list[i][2] == 0):
                if(all_house_price_every_year_list[i][1] == 0 and all_house_price_every_year_list[i][3] == 0):
                    pass
                elif(all_house_price_every_year_list[i][1] == 0):
                    all_house_price_every_year_list[i][2] = all_house_price_every_year_list[i][3] * aver_rating_21_20
                elif(all_house_price_every_year_list[i][3] == 0):
                    all_house_price_every_year_list[i][2] = all_house_price_every_year_list[i][1]/aver_rating_22_21
                else:
                    all_house_price_every_year_list[i][2] = all_house_price_every_year_list[i][1]/aver_rating_22_21*0.5 + all_house_price_every_year_list[i][3]*aver_rating_21_20*0.5

            if(all_house_price_every_year_list[i][3] == 0):
                if(all_house_price_every_year_list[i][2] == 0 and all_house_price_every_year_list[i][4] == 0):
                    pass
                elif(all_house_price_every_year_list[i][2] == 0):
                    all_house_price_every_year_list[i][3] = all_house_price_every_year_list[i][4] * aver_rating_20_19
                elif(all_house_price_every_year_list[i][4] == 0):
                    all_house_price_every_year_list[i][3] = all_house_price_every_year_list[i][2]/aver_rating_21_20
                else:
                    all_house_price_every_year_list[i][3] = all_house_price_every_year_list[i][2]/aver_rating_21_20*0.5 + all_house_price_every_year_list[i][4]*aver_rating_20_19*0.5

            if(all_house_price_every_year_list[i][4] == 0):
                if(all_house_price_every_year_list[i][3] == 0 and all_house_price_every_year_list[i][5] == 0):
                    pass
                elif(all_house_price_every_year_list[i][3] == 0):
                    all_house_price_every_year_list[i][4] = all_house_price_every_year_list[i][5] * aver_rating_19_18
                elif(all_house_price_every_year_list[i][5] == 0):
                    all_house_price_every_year_list[i][4] = all_house_price_every_year_list[i][3]/aver_rating_20_19
                else:
                    all_house_price_every_year_list[i][4] = all_house_price_every_year_list[i][3]/aver_rating_20_19*0.5 + all_house_price_every_year_list[i][5]*aver_rating_19_18*0.5

            if(all_house_price_every_year_list[i][5] == 0):
                if(all_house_price_every_year_list[i][4] == 0 and all_house_price_every_year_list[i][6] == 0):
                    pass
                elif(all_house_price_every_year_list[i][4] == 0):
                    all_house_price_every_year_list[i][5] = all_house_price_every_year_list[i][6] * aver_rating_18_17
                elif(all_house_price_every_year_list[i][6] == 0):
                    all_house_price_every_year_list[i][5] = all_house_price_every_year_list[i][4]/aver_rating_19_18
                else:
                    all_house_price_every_year_list[i][5] = all_house_price_every_year_list[i][4]/aver_rating_19_18*0.5 + all_house_price_every_year_list[i][6]*aver_rating_18_17*0.5

            if(all_house_price_every_year_list[i][6] == 0):
                if(all_house_price_every_year_list[i][5] == 0 and all_house_price_every_year_list[i][7] == 0):
                    pass
                elif(all_house_price_every_year_list[i][5] == 0):
                    all_house_price_every_year_list[i][6] = all_house_price_every_year_list[i][7] * aver_rating_17_16
                elif(all_house_price_every_year_list[i][7] == 0):
                    all_house_price_every_year_list[i][6] = all_house_price_every_year_list[i][5]/aver_rating_18_17
                else:
                    all_house_price_every_year_list[i][6] = all_house_price_every_year_list[i][5]/aver_rating_18_17*0.5 + all_house_price_every_year_list[i][7]*aver_rating_17_16*0.5

            if(all_house_price_every_year_list[i][7] == 0):
                if(all_house_price_every_year_list[i][6] == 0):
                    pass
                else:
                    all_house_price_every_year_list[i][7] = all_house_price_every_year_list[i][6]/aver_rating_17_16

            else:
                flag1[0] = 1

            if (sum(flag1) == 8):
                break
            elif (sum(flag1) == 0):
                break

    df1 = pd.DataFrame(all_house_price_every_year_list,columns=['aver_2023','aver_2022','aver_2021','aver_2020','aver_2019','aver_2018','aver_2017','aver_2016'])

    df2 = df[df.columns[0:7]].join(df1)

    df2.to_csv( path + "Predicted_result.csv",index=False,encoding='utf-8')

    with open( path + 'aver_rating.txt','w', encoding='utf-8') as file:
        list1 = ["aver_rating_23_22: "+str(aver_rating_23_22),"aver_rating_22_21: "+str(aver_rating_22_21),
                "aver_rating_21_20: "+str(aver_rating_21_20),"aver_rating_20_19: "+str(aver_rating_20_19),
                "aver_rating_19_18: "+str(aver_rating_19_18),"aver_rating_18_17: "+str(aver_rating_18_17),
                "aver_rating_17_16: "+str(aver_rating_17_16)]
        file.write("\n".join(list1))
        print ('finish')

def trans_txt_to_csv():
    out = open( path + 'result.csv', 'w', newline='',encoding='utf-8')
    csv_writer = csv.writer(out, dialect='excel')
    
    f = open( path +"result.txt", "r",encoding='utf-8')
    for line in f.readlines():
        list = line.split(';')  # 将字符串转为列表，从而可以按单元格写入csv
        csv_writer.writerow(list)

if __name__ == '__main__':
    id_list = list()
    if os.path.exists(path + 'id_list.txt'):
        id_list = read_id_list()
    else:
        id_list = fill_id_list(need_call)
        save_id_list(id_list)
        print('Id_list collection finish')
    while (True):
        if (is_cookie_exists()):
            save_data(id_list)
            trans_txt_to_csv()
            predict_statistic()
            break
        else:
            save_cookies()