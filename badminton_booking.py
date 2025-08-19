import requests
import json
import time
from typing import Dict, Any, Optional

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
    
    def create_order(self, court_id: str, so_open_id: str = "1000187088") -> Dict[str, Any]:
        """
        步骤5: 创建预约订单
        """
        url = f"{self.base_url}/order/createOrderBatch"
        
        order_data = {
            "apiVersion": "1.4.121",
            "orderType": 1,
            "userId": self.user_id,
            "orderUser": 1,
            "soOpenid": so_open_id,
            "openid": court_id,
            "phones": [self.phone_str],
            "fullPath": f"http://kfxy.ruizhiedu.com/#/pages/space/orderBatch?openid={so_open_id}"
        }
        
        try:
            response = self.session.post(url, json=order_data)
            result = response.json()
            print(f"创建订单结果: {result}")
            return result
        except Exception as e:
            print(f"创建订单失败: {e}")
            return {"error": str(e)}
    
    def find_court_by_name_and_time(self, courts_data: Dict[str, Any], court_name: str, time_slot: str) -> Optional[str]:
        """
        根据场地名称和时间段查找对应的court_id
        """
        if "data" not in courts_data or "openSlice" not in courts_data["data"]:
            return None
            
        open_slice = courts_data["data"]["openSlice"]
        
        for court_id, court_info in open_slice.items():
            if (court_info.get("slice_name") == court_name and 
                court_info.get("slice_time") == time_slot and
                court_info.get("is_lock") == 0):
                return court_id
        
        return None
    
    def complete_booking_process(self, phone: str, sms_code: str, date: str,
                                court_name: str, time_slot: str) -> Dict[str, Any]:
        """
        完整的预约流程
        """
        # 步骤2: 登录
        print("\n步骤2: 登录")
        login_result = self.login_with_sms(phone, sms_code)
        if "error" in login_result or not self.token:
            return login_result

        # 步骤3: 获取用户认证信息
        print("\n步骤3: 获取用户认证信息")
        user_info_result = self.get_user_verified_info()
        if "error" in user_info_result or not self.phone_str:
            return user_info_result

        # 步骤4: 获取可预约场地
        print("\n步骤4: 获取可预约场地")
        courts_result = self.get_available_courts(date)
        if "error" in courts_result:
            return courts_result
        
        # 查找指定的场地ID
        court_id = self.find_court_by_name_and_time(courts_result, court_name, time_slot)
        if not court_id:
            return {"error": f"未找到场地：{court_name}，在时间段：{time_slot} 的预约信息"}
        
        print(f"\n找到场地ID: {court_id}")
        
        # 步骤5: 创建订单
        print("\n步骤5: 创建预约订单")
        order_result = self.create_order(court_id)
        if "error" in order_result:
            return order_result
        
        # 步骤6: 获取支付二维码URL
        if (order_result.get("actionState") == 1 and 
            "data" in order_result and 
            "codeUrl" in order_result["data"]):
            
            code_url = order_result["data"]["codeUrl"]
            print(f"\n步骤6: 获取支付二维码URL: {code_url}")
            
            return {
                "success": True,
                "message": "预约成功",
                "payment_url": code_url,
                "order_info": order_result["data"]
            }
        
        return order_result

# 使用示例
def main():
    # 创建预约实例
    booking = BadmintonBooking()
    
    # 配置参数
    phone = "18273475755"  # 手机号
    date = "2025-08-20"  # 预约日期
    court_name = "羽毛球5"  # 场地名称
    time_slot = "18:30--20:30"  # 时间段
    
    print("=== 开始湘湖小学羽毛球场地预约流程 ===")
    
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
        court_name=court_name,
        time_slot=time_slot
    )
    
    print("\n=== 预约结果 ===")
    print(json.dumps(result, indent=2, ensure_ascii=False))
    
    if result.get("success"):
        print(f"\n预约成功！请使用以下链接进行支付：")
        print(result["payment_url"])
    else:
        print("\n预约失败,请重新预约")

if __name__ == "__main__":
    main()