import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import threading
from datetime import datetime, timedelta
from badminton_booking import BadmintonBooking
import sys
import io

class BadmintonGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("羽毛球预约系统")
        self.root.geometry("600x700")
        
        # 创建预约实例
        self.booking = BadmintonBooking()
        
        # 创建界面
        self.create_widgets()
        
        # 重定向输出到GUI
        self.redirect_output()
        
    def create_widgets(self):
        # 主框架
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # 登录区域
        login_frame = ttk.LabelFrame(main_frame, text="登录设置", padding="10")
        login_frame.grid(row=0, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        
        # 手机号输入
        ttk.Label(login_frame, text="手机号:").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.phone_var = tk.StringVar(value="18273475755")
        self.phone_entry = ttk.Entry(login_frame, textvariable=self.phone_var, width=20)
        self.phone_entry.grid(row=0, column=1, sticky=(tk.W, tk.E), padx=(10, 0), pady=5)
        
        # 发送验证码按钮
        self.send_code_btn = ttk.Button(login_frame, text="发送验证码", command=self.send_verification_code)
        self.send_code_btn.grid(row=0, column=2, padx=(10, 0), pady=5)
        
        # 验证码输入
        ttk.Label(login_frame, text="验证码:").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.code_var = tk.StringVar()
        self.code_entry = ttk.Entry(login_frame, textvariable=self.code_var, width=20)
        self.code_entry.grid(row=1, column=1, sticky=(tk.W, tk.E), padx=(10, 0), pady=5)
        
        # 登录按钮
        self.login_btn = ttk.Button(login_frame, text="登录", command=self.login)
        self.login_btn.grid(row=1, column=2, padx=(10, 0), pady=5)
        
        # 预约区域
        booking_frame = ttk.LabelFrame(main_frame, text="预约设置", padding="10")
        booking_frame.grid(row=1, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        
        # 时间段输入
        ttk.Label(booking_frame, text="预约时间段:").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.time_slot_var = tk.StringVar(value="18:30--20:30")
        self.time_slot_entry = ttk.Entry(booking_frame, textvariable=self.time_slot_var, width=20)
        self.time_slot_entry.grid(row=0, column=1, sticky=(tk.W, tk.E), padx=(10, 0), pady=5)
        
        # 开始预约按钮
        self.start_booking_btn = ttk.Button(booking_frame, text="开始预约", command=self.start_booking, state="disabled")
        self.start_booking_btn.grid(row=0, column=2, padx=(10, 0), pady=5)
        
        # 状态显示
        status_frame = ttk.LabelFrame(main_frame, text="状态信息", padding="10")
        status_frame.grid(row=2, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        
        self.status_var = tk.StringVar(value="未登录")
        self.status_label = ttk.Label(status_frame, textvariable=self.status_var, foreground="red")
        self.status_label.grid(row=0, column=0, sticky=tk.W)
        
        # 日志区域
        log_frame = ttk.LabelFrame(main_frame, text="控制台日志", padding="10")
        log_frame.grid(row=3, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 10))
        
        # 日志文本框
        self.log_text = scrolledtext.ScrolledText(log_frame, width=70, height=20, wrap=tk.WORD)
        self.log_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # 清空日志按钮
        clear_btn = ttk.Button(log_frame, text="清空日志", command=self.clear_log)
        clear_btn.grid(row=1, column=0, pady=(10, 0))
        
        # 配置网格权重
        main_frame.columnconfigure(1, weight=1)
        main_frame.rowconfigure(3, weight=1)
        login_frame.columnconfigure(1, weight=1)
        booking_frame.columnconfigure(1, weight=1)
        log_frame.columnconfigure(0, weight=1)
        log_frame.rowconfigure(0, weight=1)
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        
    def redirect_output(self):
        """重定向print输出到GUI日志"""
        class TextRedirector:
            def __init__(self, widget):
                self.widget = widget
                
            def write(self, string):
                self.widget.insert(tk.END, string)
                self.widget.see(tk.END)
                self.widget.update()
                
            def flush(self):
                pass
                
        sys.stdout = TextRedirector(self.log_text)
        
    def log_message(self, message):
        """添加日志消息"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        log_entry = f"[{timestamp}] {message}\n"
        self.log_text.insert(tk.END, log_entry)
        self.log_text.see(tk.END)
        
    def clear_log(self):
        """清空日志"""
        self.log_text.delete(1.0, tk.END)
        
    def send_verification_code(self):
        """发送验证码"""
        phone = self.phone_var.get().strip()
        if not phone:
            messagebox.showerror("错误", "请输入手机号")
            return
            
        def send_code_thread():
            self.send_code_btn.config(state="disabled", text="发送中...")
            try:
                self.log_message(f"步骤1：在向 {phone} 发送验证码...")
                result = self.booking.send_sms_code(phone)
                
                if "error" in result:
                    self.log_message(f"发送验证码失败: {result['error']}")
                    messagebox.showerror("错误", f"发送验证码失败: {result['error']}")
                else:
                    self.log_message("验证码发送成功，请查收短信")
                    messagebox.showinfo("成功", "验证码发送成功，请查收短信")
                    
            except Exception as e:
                self.log_message(f"发送验证码异常: {str(e)}")
                messagebox.showerror("错误", f"发送验证码异常: {str(e)}")
            finally:
                self.send_code_btn.config(state="normal", text="发送验证码")
                
        threading.Thread(target=send_code_thread, daemon=True).start()
        
    def login(self):
        """登录"""
        phone = self.phone_var.get().strip()
        code = self.code_var.get().strip()
        
        if not phone or not code:
            messagebox.showerror("错误", "请输入手机号和验证码")
            return
            
        def login_thread():
            self.login_btn.config(state="disabled", text="登录中...")
            try:
                self.log_message(f"步骤2： 正在使用手机号 {phone} 登录...")
                result = self.booking.login_with_sms(phone, code)
                
                if "error" in result:
                    self.log_message(f"登录失败: {result['error']}")
                    messagebox.showerror("错误", f"登录失败: {result['error']}")
                    self.status_var.set("登录失败")
                    self.status_label.config(foreground="red")
                else:
                    self.log_message("登录成功！")
                    messagebox.showinfo("成功", "登录成功！")
                    self.status_var.set("已登录")
                    self.status_label.config(foreground="green")
                    self.start_booking_btn.config(state="normal")
                    
            except Exception as e:
                self.log_message(f"登录异常: {str(e)}")
                messagebox.showerror("错误", f"登录异常: {str(e)}")
                self.status_var.set("登录失败")
                self.status_label.config(foreground="red")
            finally:
                self.login_btn.config(state="normal", text="登录")
                
        threading.Thread(target=login_thread, daemon=True).start()
        
    def start_booking(self):
        """开始预约"""
        phone = self.phone_var.get().strip()
        code = self.code_var.get().strip()
        time_slot = self.time_slot_var.get().strip()
        
        if not time_slot:
            messagebox.showerror("错误", "请输入预约时间段")
            return
            
        # 计算明天的日期
        tomorrow = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
        
        def booking_thread():
            self.start_booking_btn.config(state="disabled", text="预约中...")
            try:
                self.log_message(f"开始预约 {tomorrow} {time_slot} 的场地...")
                result = self.booking.complete_booking_process(phone, code, tomorrow, time_slot)
                
                if "error" in result:
                    self.log_message(f"预约失败: {result['error']}")
                    messagebox.showerror("错误", f"预约失败: {result['error']}")
                else:
                    self.log_message("预约流程完成！")
                    if "payment_url" in result:
                        self.log_message(f"支付链接: {result['payment_url']}")
                        # 生成二维码
                        try:
                            qr_path = self.booking.generate_qr_code(result['payment_url'])
                            self.log_message(f"支付二维码已生成: {qr_path}")
                        except Exception as e:
                            self.log_message(f"生成二维码失败: {str(e)}")
                    messagebox.showinfo("成功", "预约完成，请查看日志获取支付信息")
                    
            except Exception as e:
                self.log_message(f"预约异常: {str(e)}")
                messagebox.showerror("错误", f"预约异常: {str(e)}")
            finally:
                self.start_booking_btn.config(state="normal", text="开始预约")
                
        threading.Thread(target=booking_thread, daemon=True).start()

def main():
    root = tk.Tk()
    app = BadmintonGUI(root)
    root.mainloop()

if __name__ == "__main__":
    main()