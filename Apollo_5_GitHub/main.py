import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from pathlib import Path
import json, subprocess, threading, queue, shutil, uuid, os, re
import minecraft_launcher_lib as mc
from PIL import Image, ImageTk
HOME=Path.home()/'.apollo5'; HOME.mkdir(exist_ok=True)
LOG=HOME/'game.log'; CFG=HOME/'settings.json'
try: cfg=json.loads(CFG.read_text())
except (OSError,ValueError): cfg={}
root=tk.Tk(); root.title('Apollo Launcher 5.0'); root.geometry('1000x720'); root.minsize(720,560)
style=ttk.Style(); style.theme_use('clam'); style.configure('.',font=('Arial',12)); style.configure('TButton',padding=8)
root.configure(bg='#141b2d'); tk.Label(root,text='APOLLO  /  5.0',bg='#141b2d',fg='#91d8ff',font=('Arial',26,'bold')).pack(pady=12)
status=tk.StringVar(value='Ready'); folder=tk.StringVar(value=cfg.get('folder',mc.utils.get_minecraft_directory())); java=tk.StringVar(value=cfg.get('java','')); nick=tk.StringVar(value=cfg.get('nick','Player')); version=tk.StringVar(); remote=tk.StringVar(); kind=tk.StringVar(value='release'); ram=tk.StringVar(value=cfg.get('ram','4')); fps=tk.StringVar(value=cfg.get('fps','60')); distance=tk.StringVar(value=cfg.get('distance','8'))
q=queue.Queue(); busy=False; proc=None; catalog=[]; editor_path=None
book=ttk.Notebook(root); book.pack(fill='both',expand=True,padx=15,pady=8)
def tab(name):
 f=ttk.Frame(book,padding=12); book.add(f,text=name); return f
play=tab('Play'); versions=tab('Versions'); mods=tab('Mods'); editor=tab('Code editor'); settings=tab('Settings'); logs=tab('Logs')
def task(fn,done=lambda x:None):
 global busy
 if busy: return messagebox.showinfo('Apollo','Another task is running')
 busy=True; status.set('Working…')
 def worker():
  try:q.put((done,fn(),None))
  except Exception as e:q.put((done,None,str(e)))
 threading.Thread(target=worker,daemon=True).start()
def pump():
 global busy
 try:
  while True:
   done,result,error=q.get_nowait(); busy=False
   if error: status.set('Error'); messagebox.showerror('Apollo',error)
   else:
    status.set('Ready')
    try:done(result)
    except Exception as e:messagebox.showerror('Apollo',str(e))
 except queue.Empty:pass
 root.after(150,pump)
def entry(parent,label,var):
 ttk.Label(parent,text=label).pack(anchor='w'); ttk.Entry(parent,textvariable=var).pack(fill='x',pady=4)
def refresh():
 try: ids=[x['id'] for x in mc.utils.get_installed_versions(folder.get())]
 except OSError:ids=[]
 installed['values']=ids
 if version.get() not in ids:version.set(ids[0] if ids else '')
 modlist.delete(0,'end')
 for p in sorted((Path(folder.get())/'mods').glob('*.jar*')):modlist.insert('end',p.name)
def filter_versions(*args):
 ids=[x['id'] for x in catalog if kind.get()=='all' or x['type']==kind.get()]; available['values']=ids; remote.set(ids[0] if ids else '')
def received(items):
 global catalog
 catalog=items; filter_versions()
def download_list():task(mc.utils.get_version_list,received)
def install(v):
 if not v:return messagebox.showerror('Apollo','Choose a version')
 if proc and proc.poll() is None:return messagebox.showerror('Apollo','Close Minecraft first')
 dest=folder.get(); task(lambda:mc.install.install_minecraft_version(v,dest),lambda _:refresh())
def repair():
 v=version.get(); dest=folder.get()
 if not v:return
 if proc and proc.poll() is None:return messagebox.showerror('Apollo','Close Minecraft first')
 task(lambda:mc.install.install_minecraft_version(v,dest),lambda _:refresh())
def profile():
 cfg.update({k:v.get() for k,v in [('folder',folder),('java',java),('nick',nick),('ram',ram),('fps',fps),('distance',distance)]}); CFG.write_text(json.dumps(cfg,indent=2)); status.set('Settings saved')
def performance(dest,a,b):
 p=Path(dest)/'options.txt'; old=p.read_text(errors='replace') if p.exists() else ''; vals={'maxFps':str(a),'renderDistance':str(b),'simulationDistance':str(min(b,6)),'enableVsync':'true'}
 if p.exists():shutil.copy2(p,p.with_suffix('.apollo-backup'))
 lines=[l for l in old.splitlines() if l.split(':',1)[0] not in vals]; p.write_text('\n'.join(lines+[k+':'+v for k,v in vals.items()])+'\n')
def launch():
 global proc
 if busy or (proc and proc.poll() is None):return messagebox.showinfo('Apollo','Please wait or close Minecraft')
 try:
  v=version.get(); dest=folder.get(); name=nick.get(); mem=int(ram.get()); a=int(fps.get()); b=int(distance.get())
  if not v or not re.fullmatch(r'[A-Za-z0-9_]{1,16}',name) or not 1<=mem<=16 or not 15<=a<=240 or not 2<=b<=32:raise ValueError('Check version, nickname, RAM, FPS and distance')
  meta=json.loads((Path(dest)/'versions'/v/(v+'.json')).read_text()); parent=meta.get('inheritsFrom',v); jarid=meta.get('jar',parent); jar=Path(dest)/'versions'/jarid/(jarid+'.jar')
  if not jar.is_file():raise ValueError('Missing game JAR: '+str(jar)+'\nInstall the base version first.')
  opts={'username':name,'uuid':uuid.uuid3(uuid.NAMESPACE_DNS,'OfflinePlayer:'+name).hex,'token':'','jvmArguments':['-Xmx%dG'%mem,'-Xms512M']}
  if java.get():opts['executablePath']=java.get()
  cmd=mc.command.get_minecraft_command(v,dest,opts)
  if '-cp' in cmd:
   cp=cmd[cmd.index('-cp')+1]; missing=[x for x in cp.split(os.pathsep) if x and not Path(x).is_file() and not Path(x).is_dir()]
   if missing:raise ValueError('Missing libraries: '+ '\n'.join(missing[:5])+'\nUse Versions to install or repair.')
  performance(dest,a,b); profile()
  with LOG.open('w') as out:proc=subprocess.Popen(cmd,cwd=dest,stdout=out,stderr=subprocess.STDOUT,stdin=subprocess.DEVNULL)
  status.set('Minecraft running'); poll()
 except Exception as e:messagebox.showerror('Launch error',str(e))
def poll():
 if proc.poll() is None:root.after(2000,poll)
 else:status.set('Minecraft exited: '+str(proc.returncode)); show_log()
ttk.Label(play,text='MINECRAFT JAVA',font=('Arial',24,'bold')).pack(pady=12); installed=ttk.Combobox(play,textvariable=version,state='readonly'); installed.pack(fill='x'); ttk.Button(play,text='Refresh installed versions',command=refresh).pack(pady=8); ttk.Button(play,text='PLAY',command=launch).pack(pady=10); ttk.Label(play,text='Local single-player profile • use a legally acquired game').pack()
ttk.Button(versions,text='Load version catalog',command=download_list).pack(pady=8); filt=ttk.Combobox(versions,textvariable=kind,values=['release','snapshot','all'],state='readonly'); filt.pack(fill='x'); filt.bind('<<ComboboxSelected>>',filter_versions); available=ttk.Combobox(versions,textvariable=remote,state='readonly'); available.pack(fill='x',pady=8); ttk.Button(versions,text='Install selected vanilla version',command=lambda:install(remote.get())).pack(); ttk.Button(versions,text='Repair selected installed vanilla version',command=repair).pack(pady=8)
modlist=tk.Listbox(mods); modlist.pack(fill='both',expand=True)
def addmods():
 p=Path(folder.get())/'mods';p.mkdir(parents=True,exist_ok=True)
 for f in filedialog.askopenfilenames(filetypes=[('JAR','*.jar')]):
  d=p/Path(f).name
  if Path(f).resolve()!=d.resolve() and (not d.exists() or messagebox.askyesno('Replace',d.name)):shutil.copy2(f,d)
 refresh()
def toggle():
 if not modlist.curselection():return
 p=Path(folder.get())/'mods'/modlist.get(modlist.curselection()[0]); d=p.with_suffix('') if p.suffix=='.disabled' else Path(str(p)+'.disabled')
 if not d.exists():p.rename(d)
 refresh()
ttk.Button(mods,text='Add mods',command=addmods).pack();ttk.Button(mods,text='Enable / disable selected',command=toggle).pack()
bar=ttk.Frame(editor);bar.pack(fill='x'); code=tk.Text(editor,undo=True,wrap='none',bg='#192235',fg='#e5e7eb',insertbackground='white',font=('Menlo' if os.sys.platform=='darwin' else 'Courier',12)); code.pack(fill='both',expand=True)
def open_code():
 global editor_path
 if code.edit_modified() and not messagebox.askyesno('Editor','Discard unsaved edits?'):return
 f=filedialog.askopenfilename()
 if not f:return
 try:
  p=Path(f)
  if p.stat().st_size>2_000_000:raise ValueError('File exceeds 2 MB')
  txt=p.read_text(encoding='utf-8');code.delete('1.0','end');code.insert('1.0',txt);code.edit_modified(False);editor_path=p;status.set(str(p))
 except Exception as e:messagebox.showerror('Editor',str(e))
def save_code(as_new=False):
 global editor_path
 p=filedialog.asksaveasfilename() if as_new or not editor_path else editor_path
 if not p:return
 try:editor_path=Path(p);editor_path.write_text(code.get('1.0','end-1c'),encoding='utf-8');code.edit_modified(False);status.set('Saved '+str(p))
 except Exception as e:messagebox.showerror('Editor',str(e))
for label,fn in [('Open',open_code),('Save',save_code),('Save as',lambda:save_code(True)),('Undo',lambda:code.event_generate('<<Undo>>')),('Redo',lambda:code.event_generate('<<Redo>>'))]:ttk.Button(bar,text=label,command=fn).pack(side='left')
for label,var in [('Minecraft folder',folder),('Java executable (optional)',java),('Nickname',nick),('RAM GB',ram),('FPS limit',fps),('Render distance',distance)]:entry(settings,label,var)
def pick_folder():
 p=filedialog.askdirectory()
 if p:folder.set(p);refresh()
def pick_java():
 p=filedialog.askopenfilename()
 if p:java.set(p)
def eco():ram.set('4');fps.set('60');distance.set('8')
for label,fn in [('Choose folder',pick_folder),('Choose Java',pick_java),('Eco preset',eco),('Save settings',profile)]:ttk.Button(settings,text=label,command=fn).pack(side='left',padx=3)
logtext=tk.Text(logs,wrap='word');logtext.pack(fill='both',expand=True)
def show_log():
 logtext.delete('1.0','end')
 if LOG.exists():
  with LOG.open('rb') as f:f.seek(max(0,LOG.stat().st_size-200000));logtext.insert('1.0',f.read().decode(errors='replace'))
ttk.Button(logs,text='Refresh log',command=show_log).pack();ttk.Label(root,textvariable=status,wraplength=900).pack(pady=6)
refresh();pump();root.mainloop()
