#!/usr/bin/env python3
import base64, hashlib, json, os, queue, socket, struct, threading, time, urllib.parse, urllib.request, uuid, webbrowser
import shutil, sys, subprocess, re, math, tempfile
from pathlib import Path
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, simpledialog
APP_NAME='K1 Nexus — Printer Command Center'; DEFAULT_IP='192.168.1.195'
BG='#101820'; PANEL='#17232e'; PANEL2='#1d2b37'; TEXT='#eef6f8'; ACCENT='#59d8e8'; GOOD='#62d8a1'; BAD='#e66a5f'
STATE_NAMES={0:'Idle',1:'Printing',2:'Completed',3:'Failed',4:'Aborted',5:'Paused'}

class SimpleWebSocket:
    def __init__(self,host,port,path='/',timeout=5): self.host=host; self.port=port; self.path=path; self.timeout=timeout; self.sock=None; self.lock=threading.Lock(); self._prebuffer=b''
    def connect(self):
        self.close(); s=socket.create_connection((self.host,self.port),timeout=self.timeout); s.settimeout(None)
        key=base64.b64encode(os.urandom(16)).decode()
        req=(f'GET {self.path} HTTP/1.1\r\nHost: {self.host}:{self.port}\r\nUpgrade: websocket\r\nConnection: Upgrade\r\nSec-WebSocket-Key: {key}\r\nSec-WebSocket-Version: 13\r\n\r\n')
        s.sendall(req.encode('ascii')); header=b''
        while b'\r\n\r\n' not in header:
            c=s.recv(4096)
            if not c: raise ConnectionError('WebSocket handshake closed')
            header+=c
            if len(header)>65536: raise ConnectionError('Handshake too large')
        head,rest=header.split(b'\r\n\r\n',1); first=head.split(b'\r\n',1)[0]
        if b' 101 ' not in first: raise ConnectionError(first.decode(errors='ignore'))
        expected=base64.b64encode(hashlib.sha1((key+'258EAFA5-E914-47DA-95CA-C5AB0DC85B11').encode()).digest()).decode(); headers={}
        for line in head.decode(errors='ignore').split('\r\n')[1:]:
            if ':' in line:
                k,v=line.split(':',1); headers[k.strip().lower()]=v.strip()
        if headers.get('sec-websocket-accept')!=expected: raise ConnectionError('Invalid WebSocket accept')
        self.sock=s; self._prebuffer=rest
    def close(self):
        if self.sock:
            try:self.sock.close()
            except:pass
        self.sock=None
    def _recv_exact(self,n):
        out=b''
        if self._prebuffer:
            t=self._prebuffer[:n]; out+=t; self._prebuffer=self._prebuffer[len(t):]
        while len(out)<n:
            c=self.sock.recv(n-len(out))
            if not c: raise ConnectionError('WebSocket closed')
            out+=c
        return out
    def recv_text(self):
        fragments=[]
        while True:
            h=self._recv_exact(2); b1,b2=h; fin=(b1>>7)&1; opcode=b1&15; masked=(b2>>7)&1; ln=b2&127
            if ln==126: ln=struct.unpack('!H',self._recv_exact(2))[0]
            elif ln==127: ln=struct.unpack('!Q',self._recv_exact(8))[0]
            mask=self._recv_exact(4) if masked else None; payload=self._recv_exact(ln) if ln else b''
            if masked: payload=bytes(b^mask[i%4] for i,b in enumerate(payload))
            if opcode==8: raise ConnectionError('Closed by printer')
            if opcode==9: self._send_frame(payload,10); continue
            if opcode==10: continue
            if opcode in (1,2): fragments=[payload]
            elif opcode==0: fragments.append(payload)
            else: continue
            if fin: return b''.join(fragments).decode('utf-8','replace')
    def _send_frame(self,payload,opcode=1):
        if isinstance(payload,str): payload=payload.encode()
        with self.lock:
            if not self.sock: raise ConnectionError('Not connected')
            b1=0x80|opcode; ln=len(payload)
            if ln<126: head=bytes([b1,0x80|ln])
            elif ln<=65535: head=bytes([b1,0x80|126])+struct.pack('!H',ln)
            else: head=bytes([b1,0x80|127])+struct.pack('!Q',ln)
            mask=os.urandom(4); enc=bytes(b^mask[i%4] for i,b in enumerate(payload)); self.sock.sendall(head+mask+enc)
    def send_text(self,text): self._send_frame(text,1)

class K1Socket:
    def __init__(self,ip,enqueue): self.ip=ip; self.enqueue=enqueue; self.ws=None; self.stop_evt=threading.Event(); self.send_lock=threading.Lock()
    def start(self): self.stop(); self.stop_evt.clear(); threading.Thread(target=self._loop,daemon=True).start()
    def stop(self): self.stop_evt.set(); self.ws.close() if self.ws else None; self.ws=None
    def _loop(self):
        while not self.stop_evt.is_set():
            try:
                self.enqueue(('state',(False,'Connecting…'))); ws=SimpleWebSocket(self.ip,9999); ws.connect(); self.ws=ws
                self.enqueue(('state',(True,'Connected'))); self.enqueue(('log','Direct Python WebSocket connected'))
                threading.Thread(target=self._heartbeat,daemon=True).start(); self.get(ReqPrinterPara=1); self.get(reqGcodeFile=1)
                while not self.stop_evt.is_set():
                    raw=ws.recv_text(); self.enqueue(('log','RX '+raw[:1800]))
                    try:self.enqueue(('data',json.loads(raw)))
                    except:pass
            except Exception as e: self.enqueue(('log',f'WS error: {e}'))
            finally:
                if self.ws: self.ws.close()
                self.ws=None; self.enqueue(('state',(False,'Disconnected')))
            if self.stop_evt.wait(2): break
    def _heartbeat(self):
        while not self.stop_evt.wait(5):
            if self.ws: self.send({'ModeCode':'heart_beat','msg':time.strftime('%Y-%m-%dT%H:%M:%S')})
            else: return
    def send(self,obj):
        raw=json.dumps(obj,separators=(',',':'))
        try:
            with self.send_lock:
                if not self.ws:return False
                self.ws.send_text(raw)
            self.enqueue(('log','TX '+raw)); return True
        except Exception as e: self.enqueue(('log',f'TX error: {e}')); return False
    def set(self,**params): return self.send({'method':'set','params':params})
    def get(self,**params): return self.send({'method':'get','params':params})

class App(tk.Tk):
    def __init__(self):
        super().__init__(); self.title(APP_NAME); self.geometry('1320x840'); self.minsize(1080,700); self.configure(bg=BG); self.protocol('WM_DELETE_WINDOW',self.close)
        self.q=queue.Queue(); self.t={}; self.sock=None; self.file_records={}; self.selected_file_id=None
        self.ip=tk.StringVar(value=DEFAULT_IP); self.conn=tk.StringVar(value='Disconnected'); self.nozzle=tk.StringVar(value='--'); self.ntarget=tk.StringVar(value='--'); self.bed=tk.StringVar(value='--'); self.btarget=tk.StringVar(value='--'); self.chamber=tk.StringVar(value='--'); self.pos=tk.StringVar(value='X -- Y -- Z --'); self.status=tk.StringVar(value='Idle'); self.file=tk.StringVar(value='—'); self.progress=tk.DoubleVar(value=0); self.progress_txt=tk.StringVar(value='0%'); self.layer=tk.StringVar(value='0 / 0'); self.fil_phase=tk.StringVar(value='Ready'); self.usb_status=tk.StringVar(value='USB: not detected / not exposed')
        self.print_total_time=tk.StringVar(value='Total: --'); self.print_left_time=tk.StringVar(value='Remaining: --')
        self._style(); self._ui(); self.after(80,self._pump); self.connect()
    def _style(self):
        """Apply the K1 Nexus dark navy / cyan theme."""
        st=ttk.Style(self)
        try: st.theme_use('clam')
        except: pass

        border='#324858'
        muted='#91a5b5'

        st.configure('TFrame',background=BG)
        st.configure('Panel.TFrame',background=PANEL)
        st.configure('TLabel',background=BG,foreground=TEXT,font=('Arial',11))
        st.configure('Panel.TLabel',background=PANEL,foreground=TEXT,font=('Arial',11))
        st.configure('Title.TLabel',background=BG,foreground=ACCENT,font=('Arial',22,'bold'))
        st.configure('Big.TLabel',background=PANEL,foreground=TEXT,font=('Arial',28,'bold'))

        st.configure(
            'TButton',font=('Arial',10,'bold'),padding=8,
            background=PANEL2,foreground=TEXT,
            bordercolor=border,lightcolor=border,darkcolor=border
        )
        st.map(
            'TButton',
            background=[('active','#253847'),('pressed','#14212a')],
            foreground=[('active',ACCENT)],
            bordercolor=[('active',ACCENT)]
        )

        st.configure(
            'Accent.TButton',font=('Arial',12,'bold'),padding=11,
            background='#1f5663',foreground='#eafcff',
            bordercolor=ACCENT,lightcolor=ACCENT,darkcolor=ACCENT
        )
        st.map(
            'Accent.TButton',
            background=[('active','#287083'),('pressed','#184754')],
            foreground=[('active','white')]
        )

        st.configure(
            'TEntry',
            fieldbackground=PANEL2,foreground=TEXT,insertcolor=TEXT,
            bordercolor=border,lightcolor=border,darkcolor=border,padding=6
        )
        st.configure(
            'TCombobox',
            fieldbackground=PANEL2,foreground=TEXT,background=PANEL2,
            arrowcolor=ACCENT,bordercolor=border
        )

        st.configure('TNotebook',background=BG,borderwidth=0)
        st.configure(
            'TNotebook.Tab',
            background=PANEL2,foreground=muted,
            padding=(17,10),font=('Arial',10,'bold'),
            bordercolor=border,lightcolor=border,darkcolor=border
        )
        st.map(
            'TNotebook.Tab',
            background=[('selected',PANEL)],
            foreground=[('selected',ACCENT),('active',TEXT)],
            bordercolor=[('selected',ACCENT)]
        )

        st.configure(
            'Horizontal.TProgressbar',
            troughcolor='#243746',background=ACCENT,
            bordercolor=PANEL2,lightcolor=ACCENT,darkcolor=ACCENT
        )

        st.configure(
            'Treeview',
            background=PANEL2,fieldbackground=PANEL2,foreground=TEXT,
            rowheight=27,bordercolor=border,font=('Menlo',9)
        )
        st.configure(
            'Treeview.Heading',
            background=PANEL,foreground=muted,
            font=('Arial',9,'bold'),bordercolor=border
        )
        st.map(
            'Treeview',
            background=[('selected','#245667')],
            foreground=[('selected','#ffffff')]
        )

        st.configure('TCheckbutton',background=PANEL,foreground=TEXT)
        st.map(
            'TCheckbutton',
            background=[('active',PANEL)],
            foreground=[('active',ACCENT)]
        )
    def card(self,p,title):
        f=ttk.Frame(p,style='Panel.TFrame',padding=15); ttk.Label(f,text=title,style='Panel.TLabel',font=('Arial',14,'bold')).pack(anchor='w',pady=(0,10)); return f
    def _ui(self):
        top=ttk.Frame(self,padding=(16,12)); top.pack(fill='x'); ttk.Label(top,text='K1 NEXUS',style='Title.TLabel').pack(side='left'); ttk.Label(top,text='  Printer Command Center').pack(side='left'); r=ttk.Frame(top); r.pack(side='right'); ttk.Entry(r,textvariable=self.ip,width=16).pack(side='left',padx=4); ttk.Button(r,text='Reconnect',command=self.connect).pack(side='left',padx=4); self.conn_lbl=ttk.Label(r,textvariable=self.conn); self.conn_lbl.pack(side='left',padx=8)
        self.nb=ttk.Notebook(self); self.nb.pack(fill='both',expand=True,padx=12,pady=(0,12)); tabs=[]
        for name in ('Home','Control','Filament','Files','Self Check','Settings','Diagnostics'):
            f=ttk.Frame(self.nb,padding=12); self.nb.add(f,text=name); tabs.append(f)
        self.home,self.control,self.filament,self.files_tab,self.selfcheck,self.settings,self.diag=tabs; self._home(); self._control(); self._filament(); self._files(); self._selfcheck(); self._settings(); self._diag()
    def _home(self):
        row=ttk.Frame(self.home); row.pack(fill='x')
        for title,var,target in (('Nozzle',self.nozzle,self.ntarget),('Bed',self.bed,self.btarget),('Chamber',self.chamber,None)):
            c=self.card(row,title); c.pack(side='left',fill='x',expand=True,padx=5); ttk.Label(c,textvariable=var,style='Big.TLabel').pack(); ttk.Label(c,textvariable=target,style='Panel.TLabel').pack() if target else None
        c=self.card(self.home,'Printer'); c.pack(fill='x',padx=5,pady=10); rr=ttk.Frame(c,style='Panel.TFrame'); rr.pack(fill='x'); ttk.Label(rr,textvariable=self.status,style='Panel.TLabel',font=('Arial',15,'bold')).pack(side='left'); ttk.Label(rr,textvariable=self.pos,style='Panel.TLabel').pack(side='right'); ttk.Label(c,textvariable=self.file,style='Panel.TLabel').pack(anchor='w',pady=(10,4)); ttk.Progressbar(c,variable=self.progress,maximum=100).pack(fill='x'); rr=ttk.Frame(c,style='Panel.TFrame'); rr.pack(fill='x'); ttk.Label(rr,textvariable=self.progress_txt,style='Panel.TLabel').pack(side='left'); ttk.Label(rr,textvariable=self.layer,style='Panel.TLabel').pack(side='right')
        tr=ttk.Frame(c,style='Panel.TFrame'); tr.pack(fill='x',pady=(5,0)); ttk.Label(tr,textvariable=self.print_total_time,style='Panel.TLabel').pack(side='left'); ttk.Label(tr,textvariable=self.print_left_time,style='Panel.TLabel').pack(side='right')
        c2=self.card(self.home,'Print'); c2.pack(fill='x',padx=5,pady=5); ttk.Button(c2,text='Pause',command=lambda:self.sock.set(pause=1)).pack(side='left',padx=5); ttk.Button(c2,text='Resume',command=lambda:self.sock.set(pause=0)).pack(side='left',padx=5); ttk.Button(c2,text='Stop',command=self.stop_print).pack(side='left',padx=5); ttk.Button(c2,text='LED ON',command=lambda:self.sock.set(lightSw=1)).pack(side='right',padx=5); ttk.Button(c2,text='LED OFF',command=lambda:self.sock.set(lightSw=0)).pack(side='right',padx=5)
    def _control(self):
        l=ttk.Frame(self.control); l.pack(side='left',fill='both',expand=True,padx=5); r=ttk.Frame(self.control); r.pack(side='left',fill='both',expand=True,padx=5); c=self.card(l,'Movement'); c.pack(fill='both',expand=True); self.step=tk.StringVar(value='10'); rr=ttk.Frame(c,style='Panel.TFrame'); rr.pack(); ttk.Label(rr,text='Step (mm)',style='Panel.TLabel').pack(side='left'); ttk.Combobox(rr,textvariable=self.step,values=('0.1','1','10','50','100'),state='readonly',width=8).pack(side='left',padx=7); g=ttk.Frame(c,style='Panel.TFrame'); g.pack(pady=18)
        for text,row,col,cmd in [('Y +',0,1,lambda:self.jog('Y',1)),('X -',1,0,lambda:self.jog('X',-1)),('HOME XY',1,1,lambda:self.home_axes('X Y')),('X +',1,2,lambda:self.jog('X',1)),('Y -',2,1,lambda:self.jog('Y',-1)),('Z +',3,0,lambda:self.jog('Z',1)),('HOME ALL',3,1,lambda:self.home_axes('X Y Z')),('Z -',3,2,lambda:self.jog('Z',-1))]: ttk.Button(g,text=text,command=cmd).grid(row=row,column=col,padx=4,pady=4)
        c=self.card(r,'Temperature'); c.pack(fill='x'); self.nset=tk.IntVar(value=220); self.bset=tk.IntVar(value=60); self.slider_row(c,'Nozzle',self.nset,300,lambda:self.sock.set(nozzleTempControl=int(self.nset.get())),lambda:self.sock.set(nozzleTempControl=0)); self.slider_row(c,'Bed',self.bset,100,lambda:self.sock.set(bedTempControl={'num':0,'val':int(self.bset.get())}),lambda:self.sock.set(bedTempControl={'num':0,'val':0}))
        c=self.card(r,'Fans 0–100%'); c.pack(fill='x',pady=8); self.f0=tk.IntVar(value=0); self.f1=tk.IntVar(value=0); self.f2=tk.IntVar(value=0); self.fan_row(c,'Part / Model Fan (P0)',self.f0,0); self.fan_row(c,'Case / Chamber Fan (P1)',self.f1,1); self.fan_row(c,'Auxiliary Fan (P2)',self.f2,2)
        c=self.card(r,'Speed / Flow'); c.pack(fill='x',pady=8); self.speed=tk.IntVar(value=100); self.flow=tk.IntVar(value=100); self.simple(c,'Speed %',self.speed,lambda:self.sock.set(setFeedratePct=int(self.speed.get()))); self.simple(c,'Flow %',self.flow,lambda:self.sock.set(setFlowratePct=int(self.flow.get())))
    def slider_row(self,p,name,var,maxv,setcmd,offcmd):
        rr=ttk.Frame(p,style='Panel.TFrame'); rr.pack(fill='x',pady=4); ttk.Label(rr,text=name,style='Panel.TLabel',width=11).pack(side='left'); tk.Scale(rr,from_=0,to=maxv,orient='horizontal',variable=var,bg=PANEL,fg=TEXT,highlightthickness=0,troughcolor='#243746',length=245).pack(side='left',fill='x',expand=True); ttk.Button(rr,text='Set',command=setcmd).pack(side='left',padx=3); ttk.Button(rr,text='OFF',command=offcmd).pack(side='left',padx=3)
    def fan_row(self,p,name,var,pidx):
        rr=ttk.Frame(p,style='Panel.TFrame'); rr.pack(fill='x',pady=4); ttk.Label(rr,text=name,style='Panel.TLabel',width=22).pack(side='left'); tk.Scale(rr,from_=0,to=100,orient='horizontal',variable=var,bg=PANEL,fg=TEXT,highlightthickness=0,troughcolor='#243746',length=200).pack(side='left',fill='x',expand=True); ttk.Button(rr,text='Apply',command=lambda:self.set_fan(pidx,var.get())).pack(side='left',padx=4)
    def simple(self,p,name,var,cmd):
        rr=ttk.Frame(p,style='Panel.TFrame'); rr.pack(fill='x',pady=4); ttk.Label(rr,text=name,style='Panel.TLabel',width=12).pack(side='left'); ttk.Entry(rr,textvariable=var,width=8).pack(side='left'); ttk.Button(rr,text='Apply',command=cmd).pack(side='left',padx=5)
    def _filament(self):
        c=self.card(self.filament,'Factory Filament Control'); c.pack(fill='both',expand=True,padx=55,pady=22); ttk.Label(c,textvariable=self.fil_phase,style='Panel.TLabel',font=('Arial',19,'bold')).pack(pady=5); ttk.Label(c,text='Factory LOAD / UNLOAD. All user fans are stopped before the new command.',style='Panel.TLabel').pack(pady=4); rr=ttk.Frame(c,style='Panel.TFrame'); rr.pack(pady=20); ttk.Button(rr,text='EXTRUDE / LOAD',style='Accent.TButton',command=self.factory_load).pack(side='left',padx=16,ipadx=15,ipady=8); ttk.Button(rr,text='RETRACT / UNLOAD',style='Accent.TButton',command=self.factory_unload).pack(side='left',padx=16,ipadx=15,ipady=8)
        m=self.card(c,'Manual extrude / retract'); m.pack(fill='x',pady=14); self.emm=tk.StringVar(value='20'); ttk.Label(m,text='Distance mm:',style='Panel.TLabel').pack(side='left',padx=4); ttk.Entry(m,textvariable=self.emm,width=10).pack(side='left',padx=4); ttk.Button(m,text='Extrude entered mm',command=lambda:self.manual_e(1)).pack(side='left',padx=4); ttk.Button(m,text='Retract entered mm',command=lambda:self.manual_e(-1)).pack(side='left',padx=4); ttk.Button(m,text='Emergency Heat OFF',command=lambda:self.gcode('TURN_OFF_HEATERS')).pack(side='right',padx=4)
    def _files(self):
        outer=ttk.Frame(self.files_tab); outer.pack(fill='both',expand=True)
        left=self.card(outer,'Printer / USB Files'); left.pack(side='left',fill='both',expand=True,padx=(0,6))
        right=self.card(outer,'File Details'); right.pack(side='left',fill='y',padx=(6,0))

        bar=ttk.Frame(left,style='Panel.TFrame'); bar.pack(fill='x')
        for text,cmd in [
            ('Refresh',self.refresh_files),
            ('Upload G-code…',self.upload),
            ('Download to Mac…',self.download_selected),
            ('Rename',self.rename_selected),
            ('Delete',self.delete_file),
            ('Print',self.start_file),
        ]:
            ttk.Button(bar,text=text,command=cmd).pack(side='left',padx=3)
        ttk.Label(bar,textvariable=self.usb_status,style='Panel.TLabel').pack(side='right',padx=4)

        cols=('source','name','size','material','nozzle','bed','time')
        self.tree=ttk.Treeview(left,columns=cols,show='headings',selectmode='browse')
        hd={'source':'Source','name':'Name','size':'Size','material':'Material','nozzle':'Nozzle','bed':'Bed','time':'Print time'}
        widths={'source':75,'name':330,'size':85,'material':90,'nozzle':75,'bed':65,'time':95}
        for col in cols:
            self.tree.heading(col,text=hd[col])
            self.tree.column(col,width=widths[col],anchor='w')
        self.tree.pack(fill='both',expand=True,pady=8)
        self.tree.bind('<<TreeviewSelect>>',self.on_file_select)

        self.detail_text=tk.Text(
            right,width=45,height=35,
            bg=PANEL2,fg=TEXT,insertbackground=TEXT,
            borderwidth=0,font=('Menlo',9)
        )
        self.detail_text.pack(fill='both',expand=True,pady=(0,8))

        pbar=ttk.Frame(right,style='Panel.TFrame'); pbar.pack(fill='x',pady=8)
        ttk.Button(pbar,text='Copy Internal → USB',command=self.copy_to_usb_attempt).pack(side='left',padx=3)

    def _selfcheck(self):
        c=self.card(self.selfcheck,'Factory Self Check / Calibration'); c.pack(fill='both',expand=True); g=ttk.Frame(c,style='Panel.TFrame'); g.pack(anchor='w',pady=10)
        for text,row,col,cmd in [('Auto Bed Leveling (G29)',0,0,lambda:self.confirm_run('Run full factory G29?','G29')),('Input Shaping (INPUTSHAPER)',0,1,lambda:self.confirm_run('Run factory INPUTSHAPER?','INPUTSHAPER')),('Bed PID (BEDPID)',0,2,lambda:self.confirm_run('Run BEDPID?','BEDPID')),('Request Bed Mesh',1,0,lambda:self.sock.get(reqProbedMatrix=1)),('Clear displayed mesh',1,1,lambda:self.sock.set(rmProbedMatrix=1)),('Home All',1,2,lambda:self.home_axes('X Y Z'))]: ttk.Button(g,text=text,command=cmd).grid(row=row,column=col,padx=5,pady=5)
    def _settings(self):
        c=self.card(self.settings,'Printer Features'); c.pack(fill='x'); self.mat=tk.IntVar(value=1); self.timelapse=tk.IntVar(value=0); self.snapshot=tk.IntVar(value=0)
        for text,var,key in (('Filament detection',self.mat,'materialDetect'),('Timelapse',self.timelapse,'videoElapse'),('Nozzle move snapshot',self.snapshot,'nozzleMoveSnapshot')):
            rr=ttk.Frame(c,style='Panel.TFrame'); rr.pack(fill='x',pady=4); ttk.Label(rr,text=text,style='Panel.TLabel').pack(side='left'); ttk.Checkbutton(rr,variable=var,command=lambda v=var,k=key:self.sock.set(**{k:int(v.get())})).pack(side='right')
        c2=self.card(self.settings,'System'); c2.pack(fill='x',pady=8); ttk.Button(c2,text='Restart Klipper',command=lambda:self.ask(lambda:self.sock.set(restartKlipper=1),'Restart Klipper?')).pack(side='left',padx=4); ttk.Button(c2,text='Restart Firmware',command=lambda:self.ask(lambda:self.sock.set(restartFirmware=1),'Restart firmware?')).pack(side='left',padx=4); ttk.Button(c2,text='Clear Error',command=lambda:self.sock.set(cleanErr=1)).pack(side='left',padx=4); ttk.Button(c2,text='Open stock LAN UI',command=lambda:webbrowser.open(f'http://{self.ip.get()}')).pack(side='left',padx=4); info=self.card(self.settings,'Device info'); info.pack(fill='both',expand=True,pady=8); self.info=tk.Text(info,bg=PANEL2,fg=TEXT,insertbackground=TEXT,borderwidth=0,font=('Menlo',10)); self.info.pack(fill='both',expand=True)
    def _diag(self):
        self.logbox=tk.Text(self.diag,bg='#0c141b',fg='#b9eaf0',insertbackground='white',font=('Menlo',10),borderwidth=0); self.logbox.pack(fill='both',expand=True); rr=ttk.Frame(self.diag); rr.pack(fill='x',pady=5); self.gentry=tk.StringVar(); ttk.Entry(rr,textvariable=self.gentry).pack(side='left',fill='x',expand=True); ttk.Button(rr,text='Send G-code',command=lambda:self.gcode(self.gentry.get())).pack(side='left',padx=4)
    def connect(self):
        if self.sock:self.sock.stop()
        self.sock=K1Socket(self.ip.get().strip(),self.q.put); self.sock.start()
    def close(self):
        if self.sock:self.sock.stop()
        self.destroy()
    def _pump(self):
        try:
            while True:
                kind,payload=self.q.get_nowait()
                if kind=='data':self.data(payload)
                elif kind=='state':
                    ok,msg=payload; self.conn.set(msg); self.conn_lbl.configure(foreground=GOOD if ok else BAD)
                elif kind=='log':self.log(payload)
        except queue.Empty:pass
        self.after(80,self._pump)
    def log(self,s): self.logbox.insert('end',time.strftime('%H:%M:%S ')+s+'\n'); self.logbox.see('end')
    def data(self,d):
        self.t.update(d)
        def temp(k):
            try:return f'{float(self.t.get(k)):.1f} °C'
            except:return '--'
        self.nozzle.set(temp('nozzleTemp')); self.ntarget.set('Target '+temp('targetNozzleTemp')); self.bed.set(temp('bedTemp0')); self.btarget.set('Target '+temp('targetBedTemp0')); self.chamber.set(temp('boxTemp')); cp=self.t.get('curPosition'); self.pos.set(cp) if isinstance(cp,str) else None
        try:self.status.set(STATE_NAMES.get(int(self.t.get('state',0)),f"State {self.t.get('state')}"))
        except:pass
        try:p=float(self.t.get('printProgress',self.t.get('dProgress',0)) or 0); self.progress.set(p); self.progress_txt.set(f'{p:.0f}%')
        except:pass
        self.layer.set(f"{self.t.get('layer',0)} / {self.t.get('TotalLayer',0)}"); self.file.set(str(self.t['printFileName'])) if self.t.get('printFileName') else None
        self.print_total_time.set("Total: "+self._format_duration_live(self.t.get('printJobTime')))
        self.print_left_time.set("Remaining: "+self._format_duration_live(self.t.get('printLeftTime')))
        for key,var in (('modelFanPct',self.f0),('caseFanPct',self.f1),('auxiliaryFanPct',self.f2)):
            if key in d:
                try:var.set(int(float(d[key])))
                except:pass
        for key,var in (('materialDetect',self.mat),('videoElapse',self.timelapse),('nozzleMoveSnapshot',self.snapshot)):
            if key in d:
                try:var.set(int(d[key]))
                except:pass
        self._extract_file_records(d); self.info.delete('1.0','end'); keys=('hostname','model','modelVersion','features','connect','deviceState','err','materialDetect','materialStatus','powerLoss','maxNozzleTemp','maxBedTemp','maxBoxTemp','velocityLimits','accelerationLimits','pressureAdvance','smoothTime','video','webrtcSupport','tfCard'); self.info.insert('1.0',json.dumps({k:self.t.get(k) for k in keys},indent=2,ensure_ascii=False))
    def gcode(self,cmd):
        cmd=cmd.strip(); self.sock.set(gcodeCmd=cmd) if cmd else None
    def set_fan(self,pidx,pct): pct=max(0,min(100,int(pct))); self.gcode(f'M106 P{pidx} S{round(pct*255/100)}')
    def stop_all_user_fans(self): self.gcode('M106 P0 S0\nM106 P1 S0\nM106 P2 S0'); self.f0.set(0); self.f1.set(0); self.f2.set(0)
    def home_axes(self,a): self.sock.set(autohome=a)
    def jog(self,a,sgn):
        try:s=float(self.step.get())
        except:s=10
        self.sock.set(setPosition=f"{a}{s*sgn:g} F{600 if a=='Z' else 3000}")
    def factory_load(self):
        if int(self.t.get('state',0) or 0) in (1,5): messagebox.showwarning('Printer busy','Finish/stop the print first.'); return
        if not messagebox.askokcancel('Extrude / Load','Insert filament until it stops and LOCK the extruder lever.\n\nThen press OK.'): return
        self.stop_all_user_fans(); self.fil_phase.set('Factory LOAD queued…'); self.gcode('LOAD_MATERIAL'); self.gcode('M104 S0'); self.gcode('WAIT_TEMP_START')
    def factory_unload(self):
        if int(self.t.get('state',0) or 0) in (1,5): messagebox.showwarning('Printer busy','Finish/stop the print first.'); return
        if not messagebox.askokcancel('Retract / Unload','Keep the extruder lever LOCKED.\n\nPress OK to run factory unload.'): return
        self.stop_all_user_fans(); self.fil_phase.set('Factory UNLOAD queued…'); self.gcode('QUIT_MATERIAL'); self.gcode('M104 S0'); self.gcode('WAIT_TEMP_START')
    def manual_e(self,direction):
        try:mm=float(self.emm.get().strip().replace(',','.'))
        except: messagebox.showerror('Manual extrusion','Enter a valid number, e.g. 20 or 30.'); return
        if mm<=0: messagebox.showerror('Manual extrusion','Distance must be greater than 0.'); return
        try:cur=float(self.t.get('nozzleTemp',0))
        except:cur=0
        if cur<170: messagebox.showwarning('Nozzle cold','Heat nozzle above 170°C first.'); return
        mm=abs(mm)*direction; self.gcode(f'M83\nG1 E{mm:g} F180')
    def refresh_files(self): self.sock.get(reqGcodeFile=1)
    def _classify_source(self,path):
        p=(path or '').lower()
        if '/usr/data/printer_data/gcodes/' in p:return 'Internal'
        if any(x in p for x in ('/media/','/mnt/','/udisk','/usb','/tmp/udisk','/run/media/')):return 'USB'
        return 'Other'
    def _extract_file_records(self,x):
        # retGcodeFileInfo2 is a full file-list snapshot. Replace the cache
        # instead of merging, otherwise deleted files remain visible forever.
        if isinstance(x,dict) and isinstance(x.get("retGcodeFileInfo2"),list):
            fresh={}
            for v in x["retGcodeFileInfo2"]:
                if not isinstance(v,dict):
                    continue
                name=v.get("name") or v.get("fileName") or v.get("filename")
                path=v.get("path") or v.get("filePath")
                if name and path and str(name).lower().endswith((".gcode",".gco")):
                    rec=dict(v)
                    rec["name"]=str(name)
                    rec["path"]=str(path)
                    rec["source"]=self._classify_source(rec["path"])
                    fresh[rec["path"]]=rec
            self.file_records=fresh
            self._render_files()
            return

        # Incremental/other responses: merge only genuine file records.
        updated=False
        def walk(v):
            nonlocal updated
            if isinstance(v,dict):
                name=v.get("name") or v.get("fileName") or v.get("filename")
                path=v.get("path") or v.get("filePath")
                if name and path and str(name).lower().endswith((".gcode",".gco")):
                    fid=str(path)
                    rec=dict(v)
                    rec["name"]=str(name)
                    rec["path"]=str(path)
                    rec["source"]=self._classify_source(rec["path"])
                    self.file_records[fid]=rec
                    updated=True
                for z in v.values():
                    walk(z)
            elif isinstance(v,list):
                for z in v:
                    walk(z)
        walk(x)
        if updated:
            self._render_files()

    def _format_duration_live(self,value):
        """Format live printer seconds as HH:MM:SS."""
        try:
            sec=max(0,int(float(value)))
            return f"{sec//3600:02d}:{(sec%3600)//60:02d}:{sec%60:02d}"
        except Exception:
            return "--"

    def _fmt_size(self,n):
        try:
            n=float(n)
            return f'{n/1024**2:.1f} MB' if n>=1024**2 else (f'{n/1024:.0f} KB' if n>=1024 else f'{int(n)} B')
        except:return '—'
    def _fmt_time(self,s):
        try:s=int(s); h=s//3600; m=(s%3600)//60; return f'{h}h {m:02d}m' if h else f'{m}m'
        except:return '—'
    def _render_files(self):
        selected=self.selected_file_id
        for iid in self.tree.get_children():self.tree.delete(iid)
        usb=0
        for fid,rec in sorted(self.file_records.items(),key=lambda kv:(kv[1].get('source',''),kv[1].get('name','').lower())):
            source=rec.get('source','Other'); usb+=1 if source=='USB' else 0
            def tv(k):
                try:v=float(rec.get(k)); return f'{v/100:.0f}°' if v>500 else f'{v:.0f}°'
                except:return '—'
            self.tree.insert('', 'end', iid=fid, values=(source,rec.get('name',''),self._fmt_size(rec.get('file_size')),rec.get('material','') or '—',tv('nozzleTemp'),tv('bedTemp'),self._fmt_time(rec.get('timeCost'))))
        self.usb_status.set(f'USB: {usb} file(s) exposed' if usb else 'USB: not detected / not exposed')
        if selected and self.tree.exists(selected):self.tree.selection_set(selected)
    def selected_record(self):
        sel=self.tree.selection()
        if not sel:return None
        self.selected_file_id=sel[0]; return self.file_records.get(sel[0])
    def on_file_select(self,event=None):
        rec=self.selected_record()
        if not rec:return
        self.detail_text.delete('1.0','end'); keys=('source','name','path','file_size','create_time','timeCost','material','nozzleTemp','bedTemp','filamentWeight','thumbnail','preview'); self.detail_text.insert('1.0',json.dumps({k:rec.get(k) for k in keys},indent=2,ensure_ascii=False)); threading.Thread(target=self._load_preview,args=(rec,),daemon=True).start()
    def _load_preview(self,rec):
        url=self._preview_url(rec)
        try:
            with urllib.request.urlopen(url,timeout=5) as r:data=r.read()
            self.q.put(('preview',(rec.get('path'),data,url)))
        except Exception as e:self.q.put(('log',f'Preview error: {e}'))
    def _gcode_download_candidates(self,rec):
        """Build known stock/rooted LAN routes for a printer G-code file."""
        ip=self.ip.get().strip(); name=rec.get("name",""); path=rec.get("path","")
        qn=urllib.parse.quote(name); qp=urllib.parse.quote(path,safe="")
        return [
            f"http://{ip}/downloads/{qn}",
            f"http://{ip}/download/{qn}",
            f"http://{ip}/download?path={qp}",
            f"http://{ip}/downloads?path={qp}",
            f"http://{ip}:4408/server/files/gcodes/{qn}",
            f"http://{ip}:4409/server/files/gcodes/{qn}",
            f"http://{ip}:7125/server/files/gcodes/{qn}",
        ]


    def upload(self):
        p=filedialog.askopenfilename(filetypes=[('G-code','*.gcode *.gco'),('All files','*.*')]); threading.Thread(target=self._upload_worker,args=(p,),daemon=True).start() if p else None
    def _upload_worker(self,path):
        try:
            name=Path(path).name; boundary='----K1'+uuid.uuid4().hex; raw=Path(path).read_bytes(); body=(f'--{boundary}\r\nContent-Disposition: form-data; name="file"; filename="{name}"\r\nContent-Type: application/octet-stream\r\n\r\n').encode()+raw+f'\r\n--{boundary}--\r\n'.encode(); ip=self.ip.get().strip(); url=f'http://{ip}/upload/{urllib.parse.quote(name)}'; req=urllib.request.Request(url,data=body,headers={'Content-Type':f'multipart/form-data; boundary={boundary}','Accept':'application/json, text/plain, */*','Origin':f'http://{ip}','Referer':f'http://{ip}/'},method='POST')
            with urllib.request.urlopen(req,timeout=180) as r:resp=r.read().decode(errors='ignore')
            self.q.put(('log',f'UPLOAD OK {name}: {resp[:500]}')); time.sleep(1); self.sock.get(reqGcodeFile=1)
        except Exception as e:self.q.put(('log',f'UPLOAD ERROR: {e}')); self.after(0,lambda:messagebox.showerror('Upload',str(e)))
    def rename_selected(self):
        rec=self.selected_record()
        if not rec:return
        new=simpledialog.askstring('Rename','New filename:',initialvalue=rec['name'],parent=self)
        if not new:return
        if not new.lower().endswith(('.gcode','.gco')):new+=Path(rec['name']).suffix or '.gcode'
        newpath=str(Path(rec['path']).parent/new); self.sock.set(opGcodeFile=f"renameprt:{rec['path']}:{newpath}"); self.after(1000,self.refresh_files)
    def delete_file(self):
        rec=self.selected_record()
        if not rec:
            return
        path=rec["path"]
        name=rec["name"]
        if not messagebox.askyesno("Delete",f"Delete from printer:\n{name}\n\n{path}?"):
            return

        # Stock K1 WebUI command is:
        # opGcodeFile = "deleteprt:" + <full path>
        ok=self.sock.set(opGcodeFile=f"deleteprt:{path}")
        if not ok:
            messagebox.showerror("Delete","Delete command could not be sent.")
            return

        self.log(f"DELETE requested: {path}")

        # Force authoritative re-list and verify the file actually disappeared.
        def verify():
            self.sock.get(reqGcodeFile=1)
            self.after(1400, lambda: self._verify_deleted(path,name))
        self.after(700, verify)

    def _verify_deleted(self,path,name):
        if path in self.file_records:
            self.log(f"DELETE VERIFY FAILED: still present: {path}")
            messagebox.showwarning(
                "Delete",
                f"The printer still reports this file after the delete command:\n{name}\n\n"
                "Nothing was removed from the local list artificially."
            )
        else:
            self.log(f"DELETE VERIFIED: {path}")
            messagebox.showinfo("Delete",f"Deleted successfully:\n{name}")

    def start_file(self):
        rec=self.selected_record()
        if rec and messagebox.askyesno('Start print',f"Print:\n{rec['name']}?"): self.sock.set(opGcodeFile=f"printprt:{rec['path']}")
    def download_selected(self):
        rec=self.selected_record()
        if not rec:return
        dest=filedialog.asksaveasfilename(initialfile=rec['name'],defaultextension='.gcode'); threading.Thread(target=self._download_worker,args=(rec,dest),daemon=True).start() if dest else None
    def _download_worker(self,rec,dest):
        urls=self._gcode_download_candidates(rec); errors=[]
        for url in urls:
            try:
                with urllib.request.urlopen(urllib.request.Request(url,headers={'Accept':'application/octet-stream,*/*'}),timeout=20) as r:data=r.read(); ctype=r.headers.get('Content-Type','')
                if not data or ('text/html' in ctype.lower() and b'<html' in data[:300].lower()):raise ValueError('not a file response')
                Path(dest).write_bytes(data); self.q.put(('log',f'DOWNLOAD OK {url} -> {dest}')); self.after(0,lambda:messagebox.showinfo('Download',f'Saved:\n{dest}')); return
            except Exception as e:errors.append(f'{url} -> {e}')
        self.q.put(('log','DOWNLOAD FAILED\n'+'\n'.join(errors))); self.after(0,lambda:messagebox.showerror('Download','This stock firmware did not expose a downloadable G-code endpoint through the tested LAN routes. See Diagnostics.'))
    def copy_to_usb_attempt(self):
        rec=self.selected_record()
        if not rec:return
        usb=[r for r in self.file_records.values() if r.get('source')=='USB']
        if not usb: messagebox.showinfo('USB','No USB filesystem is currently exposed by the stock LAN API.\n\nInsert USB, press Refresh, and try again.'); return
        messagebox.showinfo('USB','USB files are visible. The exact stock internal→USB copy command is not sent until identified for this firmware.')
    def stop_print(self):
        if messagebox.askyesno('Stop print','Stop current print?'):self.sock.set(stop=1)
    def ask(self,fn,text):
        if messagebox.askyesno(APP_NAME,text):fn()
    def confirm_run(self,text,cmd):
        if messagebox.askyesno('Calibration',text+'\n\nClear the bed and supervise the machine.'):self.gcode(cmd)

if __name__=='__main__': App().mainloop()
