import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from pynput import mouse, keyboard
import threading, time, json

root=tk.Tk()
root.title("Auto Click Pro Max | Windows")
root.geometry("650x590")
root.configure(bg="#121b2b")
running=threading.Event()
paused=threading.Event()
recording=threading.Event()
events=[]
controller=mouse.Controller()
kb=keyboard.Controller()
mode=tk.StringVar(value="Vị trí chuột hiện tại")
btn=tk.StringVar(value="Trái")
interval=tk.StringVar(value="0.5")
count=tk.StringVar(value="0")
x=tk.StringVar(value="500")
y=tk.StringVar(value="300")
status=tk.StringVar(value="Sẵn sàng")
style=ttk.Style()
style.theme_use("clam")
style.configure("TFrame",background="#121b2b")
style.configure("TLabel",background="#121b2b",foreground="#e9f0ff",font=("Segoe UI",10))
style.configure("TButton",padding=7,font=("Segoe UI",10))
f=ttk.Frame(root,padding=18)
f.pack(fill="both",expand=True)
ttk.Label(f,text="AUTO CLICK PRO MAX",font=("Segoe UI",20,"bold")).pack(anchor="w",pady=8)
ttk.Label(f,text="Chế độ").pack(anchor="w")
ttk.Combobox(f,textvariable=mode,state="readonly",values=["Vị trí chuột hiện tại","Tọa độ cố định","Phát Macro"]).pack(fill="x",pady=5)
r=ttk.Frame(f);r.pack(fill="x",pady=5)
for label,var in [("Nút chuột",btn),("Khoảng cách (giây)",interval),("Số lần (0 = liên tục)",count)]:
    c=ttk.Frame(r);c.pack(side="left",fill="x",expand=True,padx=3)
    ttk.Label(c,text=label).pack(anchor="w")
    if var is btn:
        ttk.Combobox(c,textvariable=var,state="readonly",values=["Trái","Phải","Đúp trái"],width=12).pack(fill="x")
    else: ttk.Entry(c,textvariable=var,width=12).pack(fill="x")
r=ttk.Frame(f);r.pack(fill="x",pady=6)
ttk.Label(r,text="X").pack(side="left")
ttk.Entry(r,textvariable=x,width=8).pack(side="left",padx=5)
ttk.Label(r,text="Y").pack(side="left")
ttk.Entry(r,textvariable=y,width=8).pack(side="left",padx=5)
def capture():
    p=controller.position;x.set(str(p[0]));y.set(str(p[1]))
ttk.Button(r,text="Lấy vị trí chuột",command=capture).pack(side="left",padx=5)
ttk.Label(f,text="Các thao tác Macro").pack(anchor="w",pady=5)
listbox=tk.Listbox(f,height=10,bg="#202d43",fg="white",selectbackground="#365e9e",border=0)
listbox.pack(fill="both",expand=True)
def refresh():
    listbox.delete(0,"end")
    for e in events:listbox.insert("end",str(e))
def on_click(px,py,button,pressed):
    if recording.is_set() and pressed:
        events.append({"t":round(time.monotonic()-record_start,3),"type":"click","x":px,"y":py,"button":str(button)})
        root.after(0,refresh)
def on_press(key):
    if key==keyboard.Key.f8:
        running.clear();paused.clear();root.after(0,lambda:status.set("Đã dừng"))
    elif key==keyboard.Key.f7:
        if paused.is_set():paused.clear()
        else:paused.set()
    elif key==keyboard.Key.f6:root.after(0,start)
    elif recording.is_set() and key not in (keyboard.Key.f6,keyboard.Key.f7,keyboard.Key.f8):
        try:k=key.char
        except AttributeError:k=str(key)
        events.append({"t":round(time.monotonic()-record_start,3),"type":"key","key":k})
        root.after(0,refresh)
mouse_listener=mouse.Listener(on_click=on_click)
key_listener=keyboard.Listener(on_press=on_press)
mouse_listener.start();key_listener.start()
def toggle_record():
    global record_start
    if recording.is_set():
        recording.clear();status.set("Đã dừng ghi")
    else:
        running.clear();events.clear();refresh()
        record_start=time.monotonic();recording.set();status.set("Đang ghi Macro")
def save():
    path=filedialog.asksaveasfilename(defaultextension=".json",filetypes=[("Macro JSON","*.json")])
    if path:
        with open(path,"w",encoding="utf-8") as out:json.dump(events,out,ensure_ascii=False,indent=2)
def load():
    global events
    path=filedialog.askopenfilename(filetypes=[("Macro JSON","*.json")])
    if path:
        try:
            with open(path,encoding="utf-8") as src:events=json.load(src)
            refresh()
        except Exception as exc:messagebox.showerror("Lỗi",str(exc))
def click_once():
    b=mouse.Button.right if btn.get()=="Phải" else mouse.Button.left
    controller.click(b,2 if btn.get()=="Đúp trái" else 1)
def wait(seconds):
    end=time.monotonic()+seconds
    while running.is_set() and time.monotonic()<end:
        while paused.is_set() and running.is_set():time.sleep(.05)
        time.sleep(min(.03,max(0,end-time.monotonic())))
def worker(delay,total,px,py,chosen,actions):
    try:
        n=0
        while running.is_set() and (total==0 or n<total):
            while paused.is_set() and running.is_set():time.sleep(.05)
            if not running.is_set():break
            if chosen=="Phát Macro":
                prev=0
                for a in actions:
                    if not running.is_set():break
                    wait(max(0,float(a["t"])-prev));prev=float(a["t"])
                    if not running.is_set():break
                    if a["type"]=="click":
                        controller.position=(a["x"],a["y"])
                        controller.click(mouse.Button.right if "right" in a["button"] else mouse.Button.left)
                    elif a["type"]=="key":
                        key=a["key"]
                        try:kb.press(key);kb.release(key)
                        except Exception:pass
            else:
                if chosen=="Tọa độ cố định":controller.position=(px,py)
                click_once();wait(delay)
            n+=1
    finally:
        running.clear();root.after(0,lambda:status.set("Đã hoàn thành / dừng"))
def start():
    if running.is_set():return
    recording.clear()
    try:
        delay=float(interval.get());total=int(count.get());px=int(x.get());py=int(y.get())
        if delay<0.01 or total<0:raise ValueError()
        if mode.get()=="Phát Macro" and not events:
            messagebox.showwarning("Macro","Chưa có thao tác nào");return
    except ValueError:
        messagebox.showerror("Dữ liệu sai","Khoảng cách tối thiểu 0.01 giây; số lần không âm.");return
    running.set();paused.clear();status.set("Đang chạy (F8 để dừng)")
    threading.Thread(target=worker,args=(delay,total,px,py,mode.get(),list(events)),daemon=True).start()
def pause():
    if paused.is_set():paused.clear();status.set("Tiếp tục")
    else:paused.set();status.set("Tạm dừng")
def stop():
    running.clear();paused.clear();recording.clear();status.set("Đã dừng")
r=ttk.Frame(f);r.pack(fill="x",pady=8)
for label,fn in [("Ghi / Dừng ghi",toggle_record),("Xóa",lambda:(events.clear(),refresh())),("Lưu Macro",save),("Mở Macro",load)]:
    ttk.Button(r,text=label,command=fn).pack(side="left",padx=3)
r=ttk.Frame(f);r.pack(fill="x",pady=6)
for label,fn in [("Bắt đầu F6",start),("Tạm dừng F7",pause),("Dừng F8",stop)]:
    ttk.Button(r,text=label,command=fn).pack(side="left",padx=4)
ttk.Label(f,textvariable=status).pack(anchor="w",pady=6)
root.protocol("WM_DELETE_WINDOW",lambda:(stop(),mouse_listener.stop(),key_listener.stop(),root.destroy()))
root.mainloop()
