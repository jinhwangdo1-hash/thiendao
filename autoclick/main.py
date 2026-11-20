import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import threading, json
import pyautogui
from pynput import keyboard

pyautogui.FAILSAFE = True
pyautogui.PAUSE = 0

class Target:
    def __init__(self, app, x, y, number, size=32):
        self.app = app
        self.number = number
        self.size = max(16, min(100, int(size)))
        self.win = tk.Toplevel(app.root)
        self.win.overrideredirect(True)
        self.win.attributes("-topmost", True)
        self.canvas = tk.Canvas(self.win, bg="#17253a", highlightthickness=0)
        self.canvas.pack()
        self.offset = (0, 0)
        self.canvas.bind("<ButtonPress-1>", self.begin_move)
        self.canvas.bind("<B1-Motion>", self.move)
        self.canvas.bind("<MouseWheel>", self.wheel)
        self.canvas.bind("<Button-4>", lambda e: self.resize(self.size + 4))
        self.canvas.bind("<Button-5>", lambda e: self.resize(self.size - 4))
        self.set_geometry(x, y)
    def set_geometry(self, x, y):
        size = self.size
        self.win.geometry(f"{size}x{size}+{int(x-size/2)}+{int(y-size/2)}")
        self.canvas.config(width=size, height=size)
        self.canvas.delete("all")
        self.canvas.create_oval(2, 2, size-2, size-2, outline="#20e3c1", width=2)
        self.canvas.create_text(size/2, size/2, text=str(self.number),
                                fill="white", font=("Arial", max(8, int(size*.35)), "bold"))
    def begin_move(self, event):
        self.offset = (event.x, event.y)
    def move(self, event):
        self.win.geometry(f"+{event.x_root-self.offset[0]}+{event.y_root-self.offset[1]}")
    def wheel(self, event):
        self.resize(self.size + (4 if event.delta > 0 else -4))
    def resize(self, new_size):
        if self.app.running.is_set():
            return
        x, y = self.pos()
        self.size = max(16, min(100, int(new_size)))
        self.set_geometry(x, y)
    def pos(self):
        return (self.win.winfo_x()+self.size//2, self.win.winfo_y()+self.size//2)

class App:
    def __init__(self):
        self.root=tk.Tk()
        self.root.title("Auto Click Pro Max")
        self.root.geometry("460x620")
        self.root.configure(bg="#101827")
        self.targets=[]
        self.running=threading.Event()
        self.delay=tk.StringVar(value="500")
        self.mouse=tk.StringVar(value="left")
        self.circle_size=tk.IntVar(value=32)
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
        label("Kích thước vòng tròn (16–100 px)")
        tk.Scale(frame, from_=16, to=100, orient="horizontal", variable=self.circle_size,
                 command=self.resize_all, bg="#101827", fg="white", highlightthickness=0).pack(fill="x")
        label("Cuộn chuột trên từng vòng để thu/phóng riêng")
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
        self.targets.append(Target(self,x if x is not None else 180+n*35,y if y is not None else 180+n*35,n,self.circle_size.get()))
    def resize_all(self, value):
        if not self.running.is_set():
            for target in self.targets:
                target.resize(int(float(value)))
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
            with open(p,"w",encoding="utf-8") as f:json.dump({"points":[{"x":t.pos()[0],"y":t.pos()[1],"size":t.size} for t in self.targets],"circle_size":self.circle_size.get(),"delay":self.delay.get(),"mouse":self.mouse.get()},f)
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
            self.circle_size.set(max(16,min(100,int(data.get("circle_size",32)))))
            for item in pts:
                if isinstance(item, dict):
                    self.add(int(item["x"]),int(item["y"]))
                    self.targets[-1].resize(item.get("size",self.circle_size.get()))
                else:
                    x,y=item
                    self.add(int(x),int(y))
            self.delay.set(str(data.get("delay","500")))
            self.mouse.set(data.get("mouse","left"))
        except Exception:messagebox.showerror("Lỗi","Không đọc được cấu hình")
    def close(self):
        self.running.clear()
        self.listener.stop()
        self.root.destroy()

if __name__=="__main__":
    App().root.mainloop()
