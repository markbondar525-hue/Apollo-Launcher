import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import pathlib, os, sys, json, shutil, subprocess, uuid, webbrowser, threading
import minecraft_launcher_lib as mc
from PIL import Image, ImageTk
P=pathlib.Path
home=P.home(); config=home/'.apollo44'; config.mkdir(exist_ok=True)
settings=config/'settings.json'
try: data=json.loads(settings.read_text())
except (OSError,ValueError): data={}
def save():
    settings.write_text(json.dumps(data,indent=2))
root=tk.Tk(); root.title('Apollo Launcher 4.4'); root.geometry('900x650'); root.minsize(650,540); root.configure(bg='#111827')
style=ttk.Style(); style.theme_use('clam'); style.configure('.',font=('Arial',12)); style.configure('TButton',padding=9)
base= data.get('directory',mc.utils.get_minecraft_directory()); directory=tk.StringVar(value=base); version=tk.StringVar(); nick=tk.StringVar(value=data.get('nick','Player')); ram=tk.StringVar(value=data.get('ram','4')); status=tk.StringVar(value='Ready'); java=tk.StringVar(value=data.get('java',''))
header=tk.Label(root,text='APOLLO  /  4.4',font=('Arial',26,'bold'),bg='#111827',fg='#8ed5ff'); header.pack(pady=12)
bg=tk.Label(root,bg='#111827'); bg.place(x=0,y=0,relwidth=1,relheight=1); bg.lower()
def background():
    try:
        im=Image.open(data['background']); im.thumbnail((1000,750)); bg.image=ImageTk.PhotoImage(im); bg.configure(image=bg.image)
    except (KeyError,OSError): pass
background()
body=ttk.Notebook(root); body.pack(fill='both',expand=True,padx=24,pady=8)
def tab(name):
    f=ttk.Frame(body,padding=16); body.add(f,text=name); return f
j=tab('Java'); mods=tab('Mods'); s=tab('Settings')
def refresh():
    versions=sorted((v['id'] for v in mc.utils.get_installed_versions(directory.get())),reverse=True); combo['values']=versions
    if version.get() not in versions: version.set(versions[0] if versions else '')
    update_mods()
def launch():
    try:
        v=version.get(); folder=directory.get(); name=nick.get().strip(); memory=int(ram.get())
        if not v or not name or not 1<=memory<=32: raise ValueError('Select an installed version, nickname and 1–32 GB RAM.')
        opts={'username':name,'uuid':uuid.uuid3(uuid.NAMESPACE_DNS,'OfflinePlayer:'+name).hex,'token':'','jvmArguments':[f'-Xmx{memory}G']}
        if java.get(): opts['executablePath']=java.get()
        cmd=mc.command.get_minecraft_command(v,folder,opts)
        log=config/'game.log'
        with log.open('w') as out: proc=subprocess.Popen(cmd,cwd=folder,stdout=out,stderr=subprocess.STDOUT)
        status.set('Minecraft started — log: '+str(log))
        def poll():
            if proc.poll() is None: root.after(1000,poll)
            else: status.set('Minecraft exited: '+str(proc.returncode)+' — see game.log')
        root.after(1000,poll)
    except Exception as e: messagebox.showerror('Launch error',str(e))
ttk.Label(j,text='MINECRAFT JAVA',font=('Arial',24,'bold'),foreground='#23843c').pack(pady=12)
ttk.Label(j,text='Installed versions • local single-player profile').pack(); combo=ttk.Combobox(j,textvariable=version,state='readonly'); combo.pack(fill='x',pady=10)
ttk.Button(j,text='Refresh versions',command=refresh).pack(); ttk.Button(j,text='START JAVA',command=launch).pack(pady=15)
ttk.Button(j,text='Microsoft / official account',command=lambda:webbrowser.open('https://www.minecraft.net/login')).pack()
def update_mods():
    items.delete(0,'end'); p=P(directory.get())/'mods'
    if p.is_dir():
        for f in sorted(p.glob('*.jar')): items.insert('end',f.name)
def add_mod():
    paths=filedialog.askopenfilenames(filetypes=[('Java mods','*.jar')]); p=P(directory.get())/'mods'; p.mkdir(parents=True,exist_ok=True)
    for f in paths:
        dest=p/P(f).name
        if dest.exists() and not messagebox.askyesno('Replace?',dest.name): continue
        if P(f).resolve()!=dest.resolve(): shutil.copy2(f,dest)
    update_mods()
items=tk.Listbox(mods); items.pack(fill='both',expand=True); ttk.Button(mods,text='Add .jar mods',command=add_mod).pack(pady=5)
for name,url in [('Modrinth','https://modrinth.com/mods'),('CurseForge','https://www.curseforge.com/minecraft')]: ttk.Button(mods,text=name,command=lambda u=url:webbrowser.open(u)).pack()
for name,var in [('Minecraft folder',directory),('Local nickname',nick),('RAM (GB)',ram),('Java executable (optional)',java)]:
    ttk.Label(s,text=name).pack(anchor='w'); ttk.Entry(s,textvariable=var).pack(fill='x',pady=3)
def choose_dir():
    p=filedialog.askdirectory();
    if p: directory.set(p); refresh()
def choose_bg():
    p=filedialog.askopenfilename(filetypes=[('Images','*.png *.jpg *.jpeg *.webp')]);
    if p:
        try:
            dest=config/'background.png'; Image.open(p).convert('RGB').save(dest); data['background']=str(dest); save(); background()
        except Exception as e: messagebox.showerror('Background',str(e))
def persist():
    data.update(directory=directory.get(),nick=nick.get(),ram=ram.get(),java=java.get()); save(); refresh(); status.set('Settings saved')
ttk.Button(s,text='Choose Minecraft folder',command=choose_dir).pack(); ttk.Button(s,text='Choose background',command=choose_bg).pack(); ttk.Button(s,text='Save settings',command=persist).pack()
for name,color in [('Bedrock','#23843c'),('Dungeons II','#2786b9'),('Dungeons','#c13b32'),('Legends','#2786b9')]:
    f=tab(name); ttk.Label(f,text=name.upper(),font=('Arial',24,'bold'),foreground=color).pack(pady=20); ttk.Label(f,text='Direct launch is not implemented for this game.').pack(); ttk.Button(f,text='Official Minecraft website',command=lambda:webbrowser.open('https://www.minecraft.net/')).pack(pady=12)
ttk.Label(root,textvariable=status,wraplength=800).pack(pady=8); refresh(); root.mainloop()
