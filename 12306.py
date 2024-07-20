
import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select
from selenium.common.exceptions import NoSuchElementException, ElementNotInteractableException

# 创建浏览器对象
driver = webdriver.Edge()
# 打开12306网站
url = "https://www.12306.cn/index/"
driver.get(url)
driver.maximize_window() #窗口最大化
driver.implicitly_wait(10)#等待10秒
# 切换到登录页面
driver.find_element(By.LINK_TEXT,"登录").click()

def search_leftTicket(from_station_code,to_station_code,time_train):
    # 起始站的代号设置
    from_station_input = driver.find_element(by=By.ID, value="fromStation")
    driver.execute_script("arguments[0].value='%s'" % from_station_code, from_station_input)

    #终点站的代号设置
    to_station_input = driver.find_element(by=By.ID, value="toStation")
    driver.execute_script("arguments[0].value='%s'" % to_station_code, to_station_input)

    # 设置时间
    train_date_input = driver.find_element(by=By.ID, value="train_date")
    driver.execute_script("arguments[0].value='%s'" % time_train, train_date_input)

    # 执行查询操作
    search_btn = driver.find_element(by=By.ID, value="query_ticket")
    search_btn.click()


# 当提取进入界面的时候还不可以预定车票，这时候就要一直循环，直到点击预定车票后退出循环
def search_ticket(train_number):
    # 解析车次信息
    WebDriverWait(driver, 1000,0.01).until(
        EC.presence_of_element_located((By.XPATH, "//tbody[@id='queryLeftTable']/tr"))
    )
    train_trs = driver.find_elements(by=By.XPATH, value="//tbody[@id='queryLeftTable']/tr[not(@datatran)]")
    # 定义一个变量，当选取到所需的座位时使变量变成True
    searched = False
    while True:
        # 获得所有车票的信息
        for train_tr in train_trs:
            infos = train_tr.text.replace("\n", " ").split(" ")
            number = infos[0]
            # 从所有车票信息中选取自己所要的车票
            if number in train_number:
                seat_types = train_number[number]
                for seat_type in seat_types:
                    # 选取座位
                    if seat_type == "O":
                        count = infos[9]
                        if count.isdigit() or count == "有":
                            searched = True
                            break#终止掉第二层For循环
                    elif seat_type == "M":
                        count = infos[8]
                        if count.isdigit() or count == "有":
                            searched = True
                            break#终止掉第二层For循环
                # 找到车票后执行点击操作
                if searched:
                    select_number = number
                    order_btn = train_tr.find_element(by=By.XPATH, value=".//a[@class='btn72']")
                    order_btn.click()
                    # 找到车票预定后退出
                    return
                
                
def confirm_passengers(person,train_number):
    # 显式等待进入提交订单的url
    confirm_url = "https://kyfw.12306.cn/otn/confirmPassenger/initDc"
    WebDriverWait(driver, 1000,0.01).until(
        EC.url_contains(confirm_url)
    )
    # 显式等待进入乘客标签显示
    WebDriverWait(driver, 1000,0.01).until(
        EC.presence_of_element_located((By.XPATH, "//ul[@id='normal_passenger_id']/li/label"))
    )

    # 确认需要购票的乘客
    passenger_labels = driver.find_elements(by=By.XPATH, value="//ul[@id='normal_passenger_id']/li/label")
    for passenger_label in passenger_labels:
        name = passenger_label.text
        if name in person:
            passenger_label.click()
    
    # 等待提交按钮可以点击
    WebDriverWait(driver, 1000,0.01).until(
        EC.element_to_be_clickable((By.ID, "submitOrder_id"))
    )
    # 点击提交订单
    submit_btn = driver.find_element(by=By.ID, value="submitOrder_id")
    submit_btn.click()

    # 判断选座对话框出现及确认按钮可以点击
    WebDriverWait(driver, 1000,0.01).until(
        EC.presence_of_element_located((By.CLASS_NAME, "dhtmlx_window_active"))
    )
    WebDriverWait(driver, 1000,0.01).until(
        EC.element_to_be_clickable((By.ID, "qr_submit_id"))
    )
    # 执行点击操作
    submit_btn = driver.find_element(by=By.ID, value="qr_submit_id")
    # 有时候会出现点击一次没反应的情况，这时候我们需要循环点击，直到退出点击所在对话框为止
    while submit_btn:
        try:
            submit_btn.click()
            submit_btn = driver.find_element(by=By.ID, value="qr_submit_id")
        except ElementNotInteractableException:
            break
            
#VNP：KBF:开封北，ZAF：郑州东
from_station_code="KBF"
to_station_code = "ZAF"
time_train = "2024-07-15"
train_number={"G2207": ["O", "M"]}
person = ["朱孝宇(学生)"]

#设置抢购时间
start_times = datetime.datetime.now().strftime('%Y-%m-%d')+ " " + "14:30:00"
start_times =datetime.datetime.strptime(start_times,"%Y-%m-%d %H:%M:%S")
driver.get("https://kyfw.12306.cn/otn/leftTicket/init")
#开始抢票
while True:
    now = datetime.datetime.now()
    if now >= start_times:
        print("查询车票信息")
        search_leftTicket(from_station_code,to_station_code,time_train)
        print("等待车票预订，并预订")
        search_ticket(train_number)
        print("勾选乘车人，并提交订单")
        confirm_passengers(person,train_number)
        print(datetime.datetime.now(),"完成购票，尽快支付")
        break
