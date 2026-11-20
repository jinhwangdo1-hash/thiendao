import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import threading, json
import pyautogui
from pynput import keyboard

pyautogui.FAILSAFE = True
pyautogui.PAUSE = 0

class Target:
    def __init__(self, app, x, y, number):
        self.app = app
        self.win = tk.Toplevel(app.root)
        self.win.overrideredirect(True)
        self.win.attributes("-topmost", True)
        self.win.geometry(f"64x64+{x-32}+{y-32}")
        self.canvas = tk.Canvas(self.win, width=64, height=64, bg="#17253a", highlightthickness=0)
        self.canvas.pack()
        self.canvas.create_oval(4,4,60,60,outline="#20e3c1",width=4)
        self.canvas.create_text(32,32,text=str(number),fill="white",font=("Arial",16,"bold"))
        self.canvas.bind("<ButtonPress-1>",lambda e: setattr(self,"offset",(e.x,e.y)))
        self.canvas.bind("<B1-Motion>",self.move)
        self.offset=(0,0)
    def move(self,e):
        self.win.geometry(f"+{e.x_root-self.offset[0]}+{e.y_root-self.offset[1]}")
    def pos(self):
        return (self.win.winfo_x()+32,self.win.winfo_y()+32)

class App:
    def __init__(self):
        self.root=tk.Tk()
        self.root.title("Auto Click Pro Max")
        self.root.geometry("440x510")
        self.root.configure(bg="#101827")
        self.targets=[]
        self.running=threading.Event()
        self.delay=tk.StringVar(value="500")
        self.mouse=tk.StringVar(value="left")
        self.status=tk.StringVar(value="Đã dừng")
        self.make_ui()
        self.listener=keyboard.Listener(on_press=self.hotkey)
        self.listener.start()
        self.root.protocol("WM_DELETE_WINDOW",self.close)
        self.add()
    def make_ui(self):
        frame=tk.Frame(self.root,bg="#101827",padx=18,pady=18)
        frame.pack(fill="both",expand=True)
        def label(s):
            tk.Label(frame,text=s,bg="#101827",fg="white",font=("Segoe UI",11)).pack(anchor="w",pady=5)
        tk.Label(frame,text="AUTO CLICK PRO MAX",bg="#101827",fg="#20e3c1",font=("Segoe UI",20,"bold")).pack(pady=10)
        label("Kéo các vòng tròn tới nơi cần click")
        tk.Button(frame,text="+ Thêm vòng click",command=self.add).pack(fill="x",pady=4)
        tk.Button(frame,text="- Xóa vòng cuối",command=self.remove).pack(fill="x",pady=4)
        label("Khoảng cách giữa các lần click (ms)")
        tk.Entry(frame,textvariable=self.delay).pack(fill="x")
        label("Nút chuột")
        ttk.Combobox(frame,textvariable=self.mouse,values=["left","right","middle"],state="readonly").pack(fill="x")
        tk.Button(frame,text="▶ BẮT ĐẦU (F6)",command=self.start,bg="#20c9a5").pack(fill="x",pady=(16,4))
        tk.Button(frame,text="■ DỪNG (F6)",command=self.stop).pack(fill="x",pady=4)
        tk.Button(frame,text="Lưu cấu hình",command=self.save).pack(fill="x",pady=4)
        tk.Button(frame,text="Tải cấu hình",command=self.load).pack(fill="x",pady=4)
        tk.Label(frame,textvariable=self.status,bg="#101827",fg="#20e3c1").pack(pady=10)
        label("F6: bật/tắt • Kéo chuột lên góc trái để dừng an toàn")
    def add(self,x=None,y=None):
        if self.running.is_set() or len(self.targets)>=30:return
        n=len(self.targets)+1
        self.targets.append(Target(self,x if x is not None else 180+n*35,y if y is not None else 180+n*35,n))
    def remove(self):
        if self.running.is_set() or not self.targets:return
        self.targets.pop().win.destroy()
    def hotkey(self,key):
        if key==keyboard.Key.f6:
            try:self.root.after(0,self.stop if self.running.is_set() else self.start)
            except RuntimeError:pass
    def start(self):
        if self.running.is_set() or not self.targets:return
        try:
            delay=int(self.delay.get())
            if delay<10 or delay>3600000:raise ValueError()
        except ValueError:
            messagebox.showerror("Lỗi","Nhập thời gian từ 10 đến 3600000 ms")
            return
        points=[t.pos() for t in self.targets]
        button=self.mouse.get()
        self.running.set()
        for t in self.targets:t.win.withdraw()
        self.status.set("Đang click - F6 để dừng")
        threading.Thread(target=self.work,args=(points,button,delay/1000),daemon=True).start()
    def work(self,points,button,delay):
        try:
            while self.running.is_set():
                for x,y in points:
                    if not self.running.is_set():break
                    pyautogui.click(x,y,button=button)
                    if self.running.wait(0):break
                    import time
                    time.sleep(delay)
        except Exception:
            pass
        finally:
            try:self.root.after(0,self.stop)
            except RuntimeError:pass
    def stop(self):
        self.running.clear()
        for t in self.targets:
            try:t.win.deiconify()
            except tk.TclError:pass
        self.status.set("Đã dừng")
    def save(self):
        p=filedialog.asksaveasfilename(defaultextension=".json",filetypes=[("JSON","*.json")])
        if p:
            with open(p,"w",encoding="utf-8") as f:json.dump({"points":[t.pos() for t in self.targets],"delay":self.delay.get(),"mouse":self.mouse.get()},f)
    def load(self):
        if self.running.is_set():return
        p=filedialog.askopenfilename(filetypes=[("JSON","*.json")])
        if not p:return
        try:
            with open(p,encoding="utf-8") as f:data=json.load(f)
            pts=data["points"]
            if len(pts)>30:raise ValueError()
            for t in self.targets:t.win.destroy()
            self.targets=[]
            for x,y in pts:self.add(int(x),int(y))
            self.delay.set(str(data.get("delay","500")))
            self.mouse.set(data.get("mouse","left"))
        except Exception:messagebox.showerror("Lỗi","Không đọc được cấu hình")
    def close(self):
        self.running.clear()
        self.listener.stop()
        self.root.destroy()

if __name__=="__main__":
    App().root.mainloop()
