import tkinter as tk
from tkinter import ttk, messagebox
import threading, time, json, os
from pathlib import Path
import pyautogui as pg
import numpy as np
import cv2
ROOT=Path(__file__).resolve().parent
CFG=ROOT/'auto_config.json'
TEMPLATES=ROOT/'templates'
DEFAULT={'window':'Cờ Lau Loạn Thế','attack':[965,560],'heal':[0,0],'quest':[0,0],'hp':[75,35,140,14],'board':[350,135,400,400],'interval':1.0,'threshold':0.4,'dry':True}
def readcfg():
    try:return {**DEFAULT,**json.loads(CFG.read_text(encoding='utf-8'))}
    except:return DEFAULT.copy()
def window(title):
    matches=[w for w in pg.getWindowsWithTitle(title) if w.width>200 and w.height>200]
    return matches[0] if matches else None
def find(img,name,confidence=.78):
    p=TEMPLATES/(name+'.png')
    if not p.exists():return None
    template=cv2.imread(str(p))
    if template is None or template.shape[0]>img.shape[0] or template.shape[1]>img.shape[1]:return None
    _,score,_,loc=cv2.minMaxLoc(cv2.matchTemplate(img,template,cv2.TM_CCOEFF_NORMED))
    return (loc[0]+template.shape[1]//2,loc[1]+template.shape[0]//2) if score>=confidence else None
def best_swap(img,region):
    x,y,w,h=region
    if min(w,h)<=0 or x<0 or y<0 or x+w>img.shape[1] or y+h>img.shape[0]:return None
    cells=[]
    for r in range(8):
        row=[]
        for c in range(8):
            tile=img[y+int((r+.28)*h/8):y+int((r+.72)*h/8),x+int((c+.28)*w/8):x+int((c+.72)*w/8)]
            row.append(cv2.cvtColor(tile,cv2.COLOR_BGR2HSV).reshape(-1,3).mean(axis=0) if tile.size else np.zeros(3))
        cells.append(row)
    colors=np.array(cells)
    def score(arr):
        total=0
        for line in list(arr)+list(arr.transpose(1,0,2)):
            count=1
            for i in range(1,8):
                if np.linalg.norm((line[i]-line[i-1])*[.5,1,.8])<18:count+=1
                else:
                    if count>=3:total+=count*count
                    count=1
            if count>=3:total+=count*count
        return total
    base=score(colors); best=None; high=base
    for r in range(8):
        for c in range(8):
            for dr,dc in [(0,1),(1,0)]:
                rr,cc=r+dr,c+dc
                if rr>=8 or cc>=8:continue
                colors[r,c],colors[rr,cc]=colors[rr,cc].copy(),colors[r,c].copy()
                s=score(colors)
                colors[r,c],colors[rr,cc]=colors[rr,cc].copy(),colors[r,c].copy()
                if s>high:high=s;best=((x+(c+.5)*w/8,y+(r+.5)*h/8),(x+(cc+.5)*w/8,y+(rr+.5)*h/8))
    return best
class App:
    def __init__(self):
        self.root=tk.Tk();self.root.title('THIÊN ĐẠO | AUTO CỜ LAU PC');self.root.geometry('650x650')
        self.root.configure(bg='#101827');self.stop=threading.Event();self.cfg=readcfg()
        tk.Label(self.root,text='⚔ THIÊN ĐẠO AUTO',font=('Segoe UI',22,'bold'),fg='#f6d58c',bg='#101827').pack(pady=16)
        tk.Label(self.root,text='CỜ LAU LOẠN THẾ PC • BẢN THỬ NGHIỆM',fg='#8ca3c7',bg='#101827').pack()
        f=tk.Frame(self.root,bg='#101827');f.pack(fill='x',padx=24,pady=14)
        self.vars={}
        for label,key in [('Tên cửa sổ','window'),('Nút đánh x,y','attack'),('Hồi máu x,y','heal'),('Nhiệm vụ x,y','quest'),('Thanh HP x,y,w,h','hp'),('Bàn cờ x,y,w,h','board'),('Chu kỳ (giây)','interval')]:
            tk.Label(f,text=label,fg='white',bg='#101827',anchor='w',width=19).pack(anchor='w')
            v=tk.StringVar(value=','.join(map(str,self.cfg[key])) if isinstance(self.cfg[key],list) else str(self.cfg[key]))
            tk.Entry(f,textvariable=v,bg='#26364d',fg='white',insertbackground='white',relief='flat').pack(fill='x',pady=(2,7));self.vars[key]=v
        options=tk.Frame(self.root,bg='#101827');options.pack()
        self.flags={}
        for label,key in [('Tìm quái','monster'),('Di chuyển','move'),('Ghép biểu tượng','boardauto'),('Hồi HP','healauto'),('Nhiệm vụ','questauto'),('Tấn công','attackauto'),('Chế độ thử (không click)','dry')]:
            v=tk.BooleanVar(value=key=='dry' or key in ['monster','boardauto','attackauto'])
            tk.Checkbutton(options,text=label,variable=v,fg='#e4edf8',bg='#101827',selectcolor='#26364d',activebackground='#101827').pack(side='left' if key!='dry' else 'top')
            self.flags[key]=v
        b=tk.Frame(self.root,bg='#101827');b.pack(pady=10)
        tk.Button(b,text='▶ BẮT ĐẦU',command=self.start,bg='#20a47c',fg='white',width=16).pack(side='left',padx=8)
        tk.Button(b,text='■ DỪNG',command=self.halt,bg='#b94455',fg='white',width=16).pack(side='left',padx=8)
        self.status=tk.StringVar(value='Sẵn sàng • hãy hiệu chỉnh tọa độ theo cửa sổ game')
        tk.Label(self.root,textvariable=self.status,fg='#f6d58c',bg='#101827',wraplength=600).pack(pady=10)
        self.root.protocol('WM_DELETE_WINDOW',self.close)
    def save(self):
        try:
            for key,v in self.vars.items():
                s=v.get().strip()
                self.cfg[key]=[int(z.strip()) for z in s.split(',')] if key in ['attack','heal','quest','hp','board'] else float(s) if key=='interval' else s
            CFG.write_text(json.dumps(self.cfg,ensure_ascii=False,indent=2),encoding='utf-8')
            return True
        except Exception as e:messagebox.showerror('Cấu hình',str(e));return False
    def log(self,msg):self.root.after(0,lambda:self.status.set(msg))
    def click(self,w,p):
        if p and not self.flags['dry'].get():pg.click(w.left+int(p[0]),w.top+int(p[1]))
    def loop(self):
        tick=0
        while not self.stop.is_set():
            try:
                w=window(self.cfg['window'])
                if not w:self.log('Không thấy cửa sổ game: '+self.cfg['window']);self.stop.wait(2);continue
                img=np.array(pg.screenshot(region=(w.left,w.top,w.width,w.height)).convert('RGB'))[:,:,::-1]
                board=find(img,'battle')
                if self.flags['boardauto'].get() and board:
                    move=best_swap(img,self.cfg['board'])
                    if move:
                        self.log('Đã phát hiện nước ghép'+(' • chế độ thử' if self.flags['dry'].get() else ''))
                        if not self.flags['dry'].get():
                            pg.moveTo(w.left+move[0][0],w.top+move[0][1]);pg.dragTo(w.left+move[1][0],w.top+move[1][1],duration=.3)
                else:
                    monster=find(img,'monster') if self.flags['monster'].get() else None
                    if monster:self.click(w,monster);self.log('Đã nhận diện quái')
                    if self.flags['attackauto'].get():self.click(w,self.cfg['attack'])
                    if self.flags['healauto'].get():
                        x,y,ww,hh=self.cfg['hp'];roi=img[y:y+hh,x:x+ww]
                        if roi.size:
                            hsv=cv2.cvtColor(roi,cv2.COLOR_BGR2HSV)
                            red=((hsv[:,:,0]<12)|(hsv[:,:,0]>170))&(hsv[:,:,1]>90)
                            if red.mean()<self.cfg['threshold']:self.click(w,self.cfg['heal'])
                    if self.flags['questauto'].get() and tick%10==0:self.click(w,self.cfg['quest'])
                    if self.flags['move'].get() and tick%8==0 and not self.flags['dry'].get():
                        pg.keyDown('right');time.sleep(.4);pg.keyUp('right')
                tick+=1;self.stop.wait(max(.2,self.cfg['interval']))
            except Exception as e:self.log('Lỗi: '+str(e));self.stop.wait(2)
        self.log('Đã dừng')
    def start(self):
        if not self.save():return
        if not self.stop.is_set() and getattr(self,'worker',None) and self.worker.is_alive():return
        self.stop.clear();self.worker=threading.Thread(target=self.loop,daemon=True);self.worker.start()
    def halt(self):self.stop.set()
    def close(self):self.halt();self.root.destroy()
if __name__=='__main__':App().root.mainloop()
