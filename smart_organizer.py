# ---------------------------- Imports ----------------------------
from tkinter import simpledialog
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from tkinterdnd2 import DND_FILES, TkinterDnD
import os
import shutil
from datetime import datetime
import json
import threading
import time
# ---------------------------- Notifications ----------------------------
try:
    from win10toast import ToastNotifier
    toaster = ToastNotifier()
    def notify(title, message):
        def thread_func():
            toaster.show_toast(title, message, duration=5)
            while toaster.notification_active(): 
                time.sleep(0.1)
        threading.Thread(target=thread_func).start()
except ImportError:
    from plyer import notification
    def notify(title, message):
        notification.notify(title=title, message=message, app_name="Smart Organizer", timeout=5)

LIGHT_THEME = {"bg": "#f5f5f5", "fg": "#000000", "button_bg": "#e0e0e0", "progress": "#4caf50"}
DARK_THEME = {"bg": "#1e1e1e", "fg": "#ffffff", "button_bg": "#333333", "progress": "#00c853"}

# ---------------------------- Root Window ----------------------------
root = TkinterDnD.Tk()
root.title("Smart Organizer")
root.geometry("550x700")

settings_file = "settings.json"

# ---------------------------- File Counts ----------------------------
label_total = tk.Label(root, text="All files : 0", font=("Arial", 12), fg="blue")
label_total.pack(pady=5)
label_images = tk.Label(root, text="Images : 0", font=("Arial", 12), fg="purple")
label_images.pack()
label_videos = tk.Label(root, text="Videos : 0", font=("Arial", 12), fg="red")
label_videos.pack()
label_docs = tk.Label(root, text="Documents : 0", font=("Arial", 12), fg="green")
label_docs.pack()
label_others = tk.Label(root, text="Others : 0", font=("Arial", 12), fg="gray")
label_others.pack()

# ---------------------------- Progress Bar ----------------------------
style = ttk.Style()
style.configure("custom.Horizontal.TProgressbar", troughcolor=LIGHT_THEME["bg"], background=LIGHT_THEME["progress"])
progress = ttk.Progressbar(root, orient="horizontal", length=400, mode="determinate", style="custom.Horizontal.TProgressbar")
progress.pack(pady=10)
progress_label = tk.Label(root, text="0%", font=("Arial", 12))
progress_label.pack()

# ---------------------------- Done Label ----------------------------
label_done = tk.Label(root, text="", fg="darkgreen", font=("Arial", 12))
label_done.pack(pady=10)

# ---------------------------- Checkbuttons ----------------------------
var_images = tk.BooleanVar(value=True)
var_videos = tk.BooleanVar(value=True)
var_docs = tk.BooleanVar(value=True)
var_others = tk.BooleanVar(value=True)

frame_cheks = tk.Frame(root)
frame_cheks.pack(pady=10)

style.configure("Custom.TCheckbutton", background=LIGHT_THEME["bg"], foreground=LIGHT_THEME["fg"])
ttk.Checkbutton(frame_cheks, text="Images", variable=var_images, style="Custom.TCheckbutton").pack(side="left", padx=5)
ttk.Checkbutton(frame_cheks, text="Videos", variable=var_videos, style="Custom.TCheckbutton").pack(side="left", padx=5)
ttk.Checkbutton(frame_cheks, text="Documents", variable=var_docs, style="Custom.TCheckbutton").pack(side="left", padx=5)
ttk.Checkbutton(frame_cheks, text="Others", variable=var_others, style="Custom.TCheckbutton").pack(side="left", padx=5)

# ---------------------------- Listbox & Placeholder ----------------------------
selected_folders = []
file_history = []
removed_folder_stack = []

listbox_paths = tk.Listbox(root, width=65, height=8,font=("Arial",10),justify="center")
listbox_paths.pack(pady=10)
placeholder = tk.Label(root, text="↯ Drop folders here", fg="gray", font=("Arial", 12, "bold"))
placeholder.place(in_=listbox_paths, relx=0.5, rely=0.5, anchor="center")

# ---------------------------- Custom Rules ----------------------------
custom_rules = {"Compressed": [".zip", ".rar"], "Python_Files": [".py"]}

undo_stack = []
report_file_path = None

# ---------------------------- Functions ----------------------------
def update_listbox_placeholder():
    listbox_paths.delete(0, tk.END)
    if not selected_folders:
        placeholder.lift()
    else:
        placeholder.lower()
        for path in selected_folders:
            listbox_paths.insert(tk.END, path)

def load_settings():
    global current_theme
    if os.path.exists(settings_file):
        try:
            with open(settings_file, "r") as f:
                data = json.load(f)
                current_theme = DARK_THEME if data.get("theme") == "dark" else LIGHT_THEME
        except:
            current_theme = LIGHT_THEME
    else:
        current_theme = LIGHT_THEME

def save_settings():
    data = {"theme": "dark" if current_theme == DARK_THEME else "light"}
    try:
        with open(settings_file, "w") as f:
            json.dump(data, f)
    except:
        pass

def apply_theme(theme):
    root.configure(bg=theme["bg"])
    widgets = [label_total, label_images, label_videos, label_docs, label_others, label_done, progress_label]
    for w in widgets:
        w.config(bg=theme["bg"], fg=theme["fg"])
    listbox_paths.config(bg=theme["bg"], fg=theme["fg"], highlightbackground=theme["fg"])
    frame_cheks.config(bg=theme["bg"])
    frame_buttons.config(bg=theme["bg"])
    button_frame_left.config(bg=theme["bg"])
    button_frame_right.config(bg=theme["bg"])
    placeholder.config(bg=theme["bg"], fg="gray" if theme==LIGHT_THEME else "lightgray")
    style.configure("Custom.TCheckbutton", background=theme["bg"], foreground=theme["fg"])
    buttons = [button_select, button_sort, button_undo, button_remove, button_custom_rule, button_theme]
    for b in buttons:
        b.config(bg=theme["button_bg"], fg=theme["fg"])
    style.configure("custom.Horizontal.TProgressbar", troughcolor=theme["bg"], background=theme["progress"])
    save_settings()

current_theme = LIGHT_THEME
def toggle_theme():
    global current_theme
    current_theme = DARK_THEME if current_theme == LIGHT_THEME else LIGHT_THEME
    apply_theme(current_theme)

def reset_progress(total):
    progress["maximum"] = total
    progress["value"] = 0
    progress_label.config(text="0%")

def drop_event(event):
    paths = root.tk.splitlist(event.data)
    for path in paths:
        if not os.path.exists(path):
            messagebox.showinfo("Drop Error", "Dropped path does not exist.")
            continue
        if path in selected_folders:
            messagebox.showwarning("Warning", "This path has already been chosen")
            continue
        selected_folders.append(path)
    update_listbox_placeholder()

listbox_paths.drop_target_register(DND_FILES)
listbox_paths.dnd_bind("<<Drop>>", drop_event)

def select_folders():
    path = filedialog.askdirectory(title="Choose path")
    if path:
        if path in selected_folders:
            messagebox.showwarning("Warning", "This path has already been chosen.")
            return
        selected_folders.append(path)
        update_listbox_placeholder()
        label_done.config(text=f"{len(selected_folders)} path(s) selected")

def remove_selected_folder():
    selected_indices = listbox_paths.curselection()
    if not selected_indices:
        messagebox.showinfo("Warning", "No path selected for deletion.")
        return
    for index in reversed(selected_indices):
        selected_folders.pop(index)
    update_listbox_placeholder()
    label_done.config(text=f"{len(selected_folders)} Remaining path(s)")

def remove_empty_folder(path):
    for root_dir, dirs, files in os.walk(path, topdown=False):
        for d in dirs:
            full_dir = os.path.join(root_dir, d)
            if os.path.exists(full_dir) and not os.listdir(full_dir):
                os.rmdir(full_dir)

# ---------------------------- Sorting ----------------------------
def sort_single_path(path, selected_types, counts, total_files):
    for file in os.listdir(path):
        file_path = os.path.join(path, file)
        if os.path.isdir(file_path):
            continue
        ext = file.lower()
        folder = None
        if ext.endswith((".png", ".jpeg", ".jpg", ".gif")) and selected_types["Images"]:
            folder = "Images"; counts['images'] +=1
        elif ext.endswith((".mkv", ".mp4", ".mpeg", ".avi")) and selected_types["Videos"]:
            folder = "Videos"; counts['videos'] +=1
        elif ext.endswith((".pdf", ".docs", ".txt")) and selected_types["Documents"]:
            folder = "Documents"; counts['docs'] +=1
        elif not ext.endswith((".png", ".jpeg", ".jpg", ".gif", ".mkv", ".mp4", ".mpeg", ".avi",
                               ".pdf", ".docs", ".txt")) and selected_types["Others"]:
            folder = "Others"; counts['others'] +=1
        for rule_name, ext_list in custom_rules.items():
            if any(ext.endswith(e) for e in ext_list):
                folder = rule_name
                counts[rule_name] = counts.get(rule_name,0)+1
                break
        if folder is None:
            continue
        folder_path = os.path.join(path, folder)
        if not os.path.exists(folder_path):
            os.mkdir(folder_path)
        moved_path = os.path.join(folder_path, file)
        counter = 1
        base, ext_name = os.path.splitext(file)
        while os.path.exists(moved_path):
            moved_path = os.path.join(folder_path, f"{base}-{counter}{ext_name}")
            counter +=1
        shutil.move(file_path, moved_path)
        file_history.append((file_path, moved_path))
        counts['total'] +=1
        progress["value"] = counts['total']
        percent = int((counts['total']/total_files)*100)
        progress_label.config(text=f"{percent}%")
        label_total.config(text=f"All files : {counts['total']}")
        label_images.config(text=f"Images : {counts['images']}")
        label_videos.config(text=f"Videos : {counts['videos']}")
        label_docs.config(text=f"Documents : {counts['docs']}")
        label_others.config(text=f"Others : {counts['others']}")
        root.update_idletasks()

def sort_selected_folder():
    if not selected_folders:
        label_done.config(text="No path selected.")
        return
    selected_types = {"Images":var_images.get(),"Videos":var_videos.get(),"Documents":var_docs.get(),"Others":var_others.get()}
    total_files = sum(
        1 for p in selected_folders
        for f in os.listdir(p)
        if os.path.isfile(os.path.join(p,f)) and (
            (f.lower().endswith((".jpg",".png",".gif",".jpeg")) and selected_types["Images"]) or
            (f.lower().endswith((".mp4",".mkv",".avi")) and selected_types["Videos"]) or
            (f.lower().endswith((".pdf",".txt",".docs")) and selected_types["Documents"]) or
            (not f.lower().endswith((".jpg",".png",".gif",".jpeg",".mp4",".mkv",".avi",".pdf",".txt",".docs")) and selected_types["Others"]) or
            any(f.lower().endswith(e) for ext_list in custom_rules.values() for e in ext_list)
        )
    )
    if total_files==0:
        label_done.config(text="There are no files to sort")
        return
    reset_progress(total_files)
    counts = {'total':0,'images':0,'videos':0,'docs':0,'others':0}
    for rule_name in custom_rules:
        counts[rule_name]=0
    for path in selected_folders:
        sort_single_path(path, selected_types, counts, total_files)
    
    label_done.config(text="Sorting done")
    notify("Sorting Completed", f"{counts['total']} files sorted successfully")
    
    # ---------------------------- Ask to Create Report ----------------------------
    answer = messagebox.askyesno("Create Report", "Do you want to create a TXT report of this sorting?")
    if answer:
        create_report_txt(file_history, counts)
    
    selected_folders.clear()
    update_listbox_placeholder()

# ---------------------------- Undo ----------------------------
def undo_files():
    if not file_history:
        label_done.config(text="There are no files to restore.")
        return
    for original_path, moved_path in reversed(file_history):
        if os.path.exists(moved_path):
            try:
                shutil.move(moved_path, original_path)
            except:
                continue
    folders_to_check = list({os.path.dirname(orig) for orig,_ in file_history})
    for folder in folders_to_check:
        remove_empty_folder(folder)
    progress["value"]=0
    progress_label.config(text="0%")
    label_total.config(text="All files : 0")
    label_images.config(text="Images : 0")
    label_videos.config(text="Videos : 0")
    label_docs.config(text="Documents : 0")
    label_others.config(text="Others : 0")
    listbox_paths.delete(0,tk.END)
    listbox_paths.insert(tk.END,"↯ Drop folders here")
    listbox_paths.itemconfig(tk.END, fg="gray")
    selected_folders.clear()
    
    global report_file_path
    if report_file_path and os.path.exists(report_file_path):
        answer=messagebox.askyesno("Remove Report","Restore completed.\nDo you want to delete the report file?")
        if answer:
            try:
                os.remove(report_file_path)
                messagebox.showinfo("Report Removed","Report file deleted successfully")
            except Exception as e:
                messagebox.showerror("Error",f"Failed to delete report:\n{e}")
        report_file_path=None
    
    update_listbox_placeholder()
    label_done.config(text="All files restored.")
    notify("Restore Completed","All files have been restored successfully")

# ---------------------------- Custom Rules ----------------------------
def add_custom_rule():
    folder_name = simpledialog.askstring("Custom Folder","Enter folder name for custom rule:")
    if not folder_name:
        return
    extensions = simpledialog.askstring("File Extensions","Enter file extensions separated by comma (e.g., .zip,.rar):")
    if not extensions:
        return
    ext_list = [ext.strip() for ext in extensions.split(",") if ext.strip()]
    if ext_list:
        custom_rules[folder_name]=ext_list
        messagebox.showinfo("Rule Added",f"Rule added : {folder_name} -> {', '.join(ext_list)}")

# ---------------------------- Report ----------------------------
def create_report_txt(sorted_paths, counts):
    save_path = filedialog.asksaveasfilename(defaultextension=".txt", filetypes=[("Text files", "*.txt")], title="Save report as ....")
    if not save_path:
        messagebox.showinfo("Report", "Report not created")
        return
    try:
        with open(save_path, "w", encoding="utf-8") as f:
            f.write(f"Sorting Report - {datetime.now().strftime('%y-%m-%d %H.%M.%S')}\n")
            f.write("="*50 + "\n")
            f.write(f"Total files sorted : {counts['total']}\n")
            f.write(f"Images : {counts['images']}\n")
            f.write(f"Videos : {counts['videos']}\n")
            f.write(f"Documents : {counts['docs']}\n")
            f.write(f"Others : {counts['others']}\n")
            for rule_name in custom_rules:
                f.write(f"{rule_name} : {counts.get(rule_name,0)}\n")
            f.write("\nFiles moved :\n")
            for original, moved in file_history:
                f.write(f"{original} ---> {moved}\n")
        messagebox.showinfo("Report Created", f"Report saved as {save_path}")
        notify("Report Created","TXT report was created successfully")
    except Exception as e:
        messagebox.showerror("Error", f"Failed to save report:\n{e}")
    global report_file_path
    report_file_path = save_path

# ---------------------------- Buttons ----------------------------
frame_buttons = tk.Frame(root, bg=current_theme["bg"])
frame_buttons.pack(pady=10)
button_frame_left = tk.Frame(root, bg=current_theme["bg"])
button_frame_left.pack(side="left", padx=48, pady=10)
button_frame_right = tk.Frame(root, bg=current_theme["bg"])
button_frame_right.pack(side="right", padx=48, pady=10)

button_select = tk.Button(button_frame_left, text="Choose Paths", command=select_folders, bg="lightblue", width=20)
button_select.pack(side="top", pady=5)
button_sort = tk.Button(button_frame_right, text="Sort Selected Path", command=sort_selected_folder, bg="blue", fg="white", width=20)
button_sort.pack(side="top", pady=10)
button_undo = tk.Button(button_frame_right, text="Restore File", command=undo_files, bg="lightgreen", width=20)
button_undo.pack(pady=10)
button_remove = tk.Button(button_frame_left, text="Delete Selected Path", command=remove_selected_folder, bg="#ffcccc", width=20)
button_remove.pack(pady=10)
button_custom_rule = tk.Button(button_frame_left, text="Custom Rule", command=add_custom_rule, bg="#ffa500", width=20)
button_custom_rule.pack(pady=10)
button_theme = tk.Button(button_frame_right, text="Toggle Theme", command=toggle_theme, width=20)
button_theme.pack(pady=10)

# ---------------------------- Initial Theme ----------------------------
load_settings()
apply_theme(current_theme)
# ---------------------------- Mainloop ----------------------------
root.iconbitmap("D:\DOWNLOAD\icon.ico")
root.mainloop()