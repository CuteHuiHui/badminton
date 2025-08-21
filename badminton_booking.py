import requests
import json
import time
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List
import qrcode
from PIL import Image
import io
import os
import pytz

class BadmintonBooking:
    def __init__(self):
        self.base_url = "https://dns.jzyxt.ruizhiedu.com:9071/xinshan/opensc"
        self.token = None
        self.user_id = None
        self.phone_str = None
        self.session = requests.Session()
        
    def send_sms_code(self, phone: str) -> Dict[str, Any]:
        """
        步骤1: 发送验证码
        """
        url = f"{self.base_url}/user/loginSms"
        data = {
            "phone": phone
        }
        
        try:
            response = self.session.post(url, data=data)
            result = response.json()
            print(f"发送验证码结果: {result}")
            return result
        except Exception as e:
            print(f"发送验证码失败: {e}")
            return {"error": str(e)}
    
    def login_with_sms(self, phone: str, sms_code: str, open_id: str = "") -> Dict[str, Any]:
        """
        步骤2: 手机号和验证码登录
        """
        url = f"{self.base_url}/user/SOLoginPhone"
        data = {
            "phone": phone,
            "smsCode": sms_code,
            "openId": open_id
        }
        
        try:
            response = self.session.post(url, data=data)
            result = response.json()
            
            if result.get("actionState") == 0 and "data" in result:
                self.token = result["data"].get("token")
                self.user_id = result["data"].get("userId")
                # 设置后续请求的token，使用大写的Token
                self.session.headers.update({"Token": self.token})

            print(f"登录结果: {result}")
            return result
        except Exception as e:
            print(f"登录失败: {e}")
            return {"error": str(e)}
    
    def get_available_courts(self, date: str, space_id: str = "111162", sport_type: str = "2") -> Dict[str, Any]:
        """
        步骤3: 获取指定日期的可预约场地
        """
        # 参数直接放在URL中，就像Postman的curl命令一样
        url = f"{self.base_url}/open/getSpaceOrderDetailsNew?spaceId={space_id}&sportType={sport_type}&time={date}"

        try:
            # 使用POST请求，直接使用session的headers
            response = self.session.post(url)
            
            if response.status_code == 200:
                result = response.json()
                print(f"可预约场地: {result}")
                return result
            else:
                print(f"响应内容: {response.text}")
                return {"error": f"HTTP {response.status_code}: {response.text}"}
                
        except Exception as e:
            print(f"获取场地信息失败: {e}")
            return {"error": str(e)}
    
    def get_user_verified_info(self) -> Dict[str, Any]:
        """
        步骤4: 获取用户实名认证信息
        """
        url = f"{self.base_url}/user/verifiedInfo"
        
        try:
            response = self.session.post(url)
            result = response.json()
            
            if result.get("actionState") == 1 and "data" in result:
                self.phone_str = result["data"].get("phonestr")

            print(f"用户认证信息: {result}")
            return result
        except Exception as e:
            print(f"获取用户信息失败: {e}")
            return {"error": str(e)}
    
    def create_order(self, court_id: str) -> Dict[str, Any]:
        """
        步骤5: 创建预约订单
        """
        url = f"{self.base_url}/order/createOrderBatch"
        
        order_data = {
            "apiVersion": "1.4.121",
            "orderType": 1,
            "userId": self.user_id,
            "orderUser": 1,
            "soOpenid": court_id,
            "phones": [self.phone_str],
            "fullPath": f"http://kfxy.ruizhiedu.com/#/pages/space/orderBatch?openid={court_id}"
        }
        
        try:
            response = self.session.post(url, json=order_data)
            result = response.json()
            print(f"创建订单结果: {result}")
            return result
        except Exception as e:
            print(f"创建订单失败: {e}")
            return {"error": str(e)}
    
    def find_available_courts_by_time(self, courts_data: Dict[str, Any], time_slot: str) -> List[Dict[str, str]]:
        """
        根据时间段查找所有可用场地，按场地名称倒序排列
        """
        if "data" not in courts_data or "openSlice" not in courts_data["data"]:
            return []
            
        open_slice = courts_data["data"]["openSlice"]
        available_courts = []
        
        for court_id, court_info in open_slice.items():
            if (court_info.get("slice_time") == time_slot and
                court_info.get("is_lock") != 1):
                available_courts.append({
                    "court_id": court_id,
                    "court_name": court_info.get("slice_name", "")
                })
        
        # 按场地名称倒序排列
        available_courts.sort(key=lambda x: x["court_name"], reverse=True)
        return available_courts

    def complete_booking_process(self, phone: str, sms_code: str, date: str, time_slot: str) -> Dict[str, Any]:
        """
        完整的预约流程
        """
#         步骤2: 登录
        print("\n步骤2: 登录")
        login_result = self.login_with_sms(phone, sms_code)
        if "error" in login_result or not self.token:
            return login_result

#         步骤3: 获取用户认证信息
        print("\n步骤3: 获取用户认证信息")
        user_info_result = self.get_user_verified_info()
        if "error" in user_info_result or not self.phone_str:
            return user_info_result

        # 步骤4: 获取可预约场地
        print("\n步骤4: 获取可预约场地")
        courts_result = self.get_available_courts(date)
        if "error" in courts_result:
            return courts_result
        
        # 查找符合时间段的所有可用场地，按名称倒序
        available_courts = self.find_available_courts_by_time(courts_result, time_slot)
        if not available_courts:
            return {"error": f"未找到时间段：{time_slot} 的可用场地"}
        
        print(f"\n找到 {len(available_courts)} 个可用场地，按名称倒序：")
        for court in available_courts:
            print(f"  - {court['court_name']} (ID: {court['court_id']})")
        
            # 等待到北京时间上午10:00整
        print("\n⏰ 等待北京时间上午10:00整开始抢票...")
        self.wait_until_10am_beijing()
        
        # 轮询尝试预约，从名称倒序的第一个开始
        for court in available_courts:
            court_id = court["court_id"]
            court_name = court["court_name"]
            
            print(f"\n尝试预约场地：{court_name} (ID: {court_id})")
            
            # 步骤5: 创建订单
            print("\n步骤5: 创建预约订单")
            order_result = self.create_order(court_id)
            
            if "error" not in order_result:
                # 步骤6: 获取支付二维码URL
                if (order_result.get("actionState") == 1 and
                    "data" in order_result and
                    "codeUrl" in order_result["data"]):
                    
                    code_url = order_result["data"]["codeUrl"]
                    print(f"\n步骤6: 获取支付二维码URL: {code_url}")
                    
                    return {
                        "success": True,
                        "message": f"预约成功 - 场地：{court_name}",
                        "court_name": court_name,
                        "payment_url": code_url,
                        "order_info": order_result["data"]
                    }
                else:
                    print(f"场地 {court_name} 预约失败，尝试下一个场地")
                    continue
            else:
                print(f"场地 {court_name} 预约失败：{order_result.get('error', '未知错误')}，尝试下一个场地")
                continue
        
        return {"error": "所有可用场地预约都失败了"}

    def generate_qr_code(self, payment_url: str, filename: str = "payment_qr.png") -> str:
        """
        生成支付二维码
        """
        try:
            # 创建二维码实例
            qr = qrcode.QRCode(
                version=1,
                error_correction=qrcode.constants.ERROR_CORRECT_L,
                box_size=10,
                border=4,
            )
            
            # 添加数据
            qr.add_data(payment_url)
            qr.make(fit=True)
            
            # 创建二维码图片
            img = qrcode.make_image(payment_url)
            
            # 保存图片
            img.save(filename)
            print(f"\n二维码已生成并保存为: {filename}")
            
            return filename
        except Exception as e:
            print(f"生成二维码失败: {e}")
            return ""

    def wait_until_10am_beijing(self):
        """
        等待到北京时间当天上午10:00整
        """
        # 设置北京时区
        beijing_tz = pytz.timezone('Asia/Shanghai')
        
        while True:
            # 获取当前北京时间
            now_beijing = datetime.now(beijing_tz)
            
            # 计算今天上午10:00的时间
            target_time = now_beijing.replace(hour=14, minute=35, second=0, microsecond=0)
            
            # 如果已经过了今天的10:00，则设置为明天的10:00
            if now_beijing >= target_time:
                target_time = target_time + timedelta(days=1)
            
            # 计算剩余时间
            time_diff = target_time - now_beijing
            total_seconds = int(time_diff.total_seconds())
            
            if total_seconds <= 0:
                print("\n🎯 北京时间10:00整，开始创建订单！")
                break
            
            # 格式化倒计时显示
            hours = total_seconds // 3600
            minutes = (total_seconds % 3600) // 60
            seconds = total_seconds % 60
            
            print(f"\r⏰ 距离北京时间10:00还有: {hours:02d}:{minutes:02d}:{seconds:02d} ", end="", flush=True)
            
            # 每秒更新一次
            time.sleep(1)
        
        print()  # 换行

# 使用示例
def main():
    # 创建预约实例
    booking = BadmintonBooking()
    
    # 配置参数
    phone = "18273475755"  # 手机号
    # 预约第二天
    tomorrow = datetime.now() + timedelta(days=1)
    date = tomorrow.strftime("%Y-%m-%d")
    time_slot = "16:30--18:30"  # 时间段

    print(f"=== 开始湘湖小学羽毛球场地预约流程 (预约日期: {date}) ===")
    
    # 步骤1: 发送验证码
    print("\n步骤1: 发送验证码")
    sms_result = booking.send_sms_code(phone)
    if "error" in sms_result:
        print(f"发送验证码失败: {sms_result['error']}")
        return
    
    # 等待用户输入验证码
    print("\n")
    sms_code = input("请输入收到的验证码: ")
    
    # 执行剩余的预约流程
    result = booking.complete_booking_process(
        phone=phone,
        sms_code=sms_code,
        date=date,
        time_slot=time_slot
    )
    
    print("\n=== 预约结果 ===")
    print(json.dumps(result, indent=2, ensure_ascii=False))
    
    if result.get("success"):
        print(f"\n预约成功！场地：{result.get('court_name')}")
        print(f"请使用以下链接进行支付：")
        print(result["payment_url"])
        
        # 生成支付二维码
        qr_filename = booking.generate_qr_code(result["payment_url"])
        if qr_filename:
            print(f"\n支付二维码已生成，请扫描 {qr_filename} 进行支付")
            
            # 可选：尝试打开二维码图片
            try:
                if os.name == 'nt':  # Windows
                    os.startfile(qr_filename)
                elif os.name == 'posix':  # macOS/Linux
                    os.system(f'open {qr_filename}')  # macOS
                    # os.system(f'xdg-open {qr_filename}')  # Linux
                print("二维码图片已自动打开")
            except:
                print("请手动打开二维码图片文件")
    else:
        print("\n预约失败,请重新预约")

if __name__ == "__main__":
    main()