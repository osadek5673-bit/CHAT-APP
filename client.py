import socket
import threading
import tkinter as tk
from tkinter import scrolledtext, filedialog
from PIL import Image, ImageTk  # أضفنا ImageTk هنا
import os
import tempfile

HOST = '127.0.0.1' 
PORT = 7000

os.makedirs("received_files", exist_ok=True)

client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client.connect((HOST, PORT))

# لستة للحفاظ على مراجع الصور في الذاكرة عشان متختفيش من الشات
chat_images = []

def update_chat(message, tag):
    chat_area.config(state=tk.NORMAL)
    chat_area.insert(tk.END, message + "\n", tag)
    chat_area.config(state=tk.DISABLED)
    chat_area.yview(tk.END)

# دالة جديدة لعرض الصور داخل الشات مباشرة
def display_image_in_chat(image_path, tag):
    try:
        chat_area.config(state=tk.NORMAL)
        
        # فتح الصورة وتصغير حجمها عشان متملايش الشاشة بالكامل
        img = Image.open(image_path)
        img.thumbnail((150, 150))  # تغيير الحجم الأقصى للصورة داخل الشات
        
        photo = ImageTk.PhotoImage(img)
        chat_images.append(photo)  # حفظ المرجع في الذاكرة
        
        # تحديد جهة المحاذاة (يمين للمرسل، شمال للمستقبل)
        alignment = "right" if tag == "you" else "left"
        
        # إضافة سطر جديد قبل الصورة ومحاذاتها
        chat_area.insert(tk.END, "\n", tag)
        chat_area.image_create(tk.END, image=photo)
        chat_area.insert(tk.END, "\n\n", tag)
        
        chat_area.config(state=tk.DISABLED)
        chat_area.yview(tk.END)
    except Exception as e:
        print(f"Error displaying image: {e}")

def compress_image(image_path):
    img = Image.open(image_path)
    if img.mode != "RGB":
        img = img.convert("RGB")
    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".jpg")
    img.save(temp_file.name, format="JPEG", quality=25)
    return temp_file.name

def send_message():
    message = message_entry.get()
    if message:
        full_msg = f"TEXT:{message}"
        client.send(full_msg.encode())
        update_chat(f"You: {message}", "you")
        message_entry.delete(0, tk.END)

def send_media():
    file_path = filedialog.askopenfilename()
    if not file_path: return

    is_image = file_path.lower().endswith(('.png', '.jpg', '.jpeg'))
    if is_image and not hd_var.get():
        send_path = compress_image(file_path)
    else:
        send_path = file_path

    filename = os.path.basename(send_path)
    
    client.send(f"FILE_START:{filename}<END_NAME>".encode())
    
    with open(send_path, "rb") as f:
        while chunk := f.read(4096):
            client.sendall(chunk)
    
    client.send(b"<END_OF_FILE_MARKER>")
    
    # إذا كانت الملف صورة، اعرضها في شات المرسل فوراً
    if is_image:
        update_chat("You sent an image:", "you")
        display_image_in_chat(send_path, "you")
    else:
        update_chat(f"You sent: {filename}", "you")

def receive_thread():
    while True:
        try:
            data = client.recv(4096)
            if not data: break

            if data.startswith(b"TEXT:"):
                msg = data.decode()[5:]
                update_chat(f"Friend: {msg}", "friend")
            
            elif data.startswith(b"FILE_START:"):
                header, chunk = data.split(b"<END_NAME>", 1)
                filename = header.decode().split(":")[1]
                
                file_data = chunk
                while b"<END_OF_FILE_MARKER>" not in file_data:
                    packet = client.recv(4096)
                    file_data += packet
                
                final_content = file_data.replace(b"<END_OF_FILE_MARKER>", b"")
                save_path = os.path.join("received_files", filename)
                with open(save_path, "wb") as f:
                    f.write(final_content)
                
                # هنا بنفحص لو الملف المستلم صورة عشان نعرضها للـ Friend
                is_image = filename.lower().endswith(('.png', '.jpg', '.jpeg'))
                if is_image:
                    update_chat("Friend sent an image:", "friend")
                    display_image_in_chat(save_path, "friend")
                else:
                    update_chat(f"Friend sent: {filename}", "friend")
        except Exception as e:
            print(e)
            break

window = tk.Tk()
window.title("SafeChat - Client")
window.geometry("450x550")

chat_area = scrolledtext.ScrolledText(window, wrap=tk.WORD, state=tk.DISABLED, font=("Arial", 11))
chat_area.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)

chat_area.tag_config("you", foreground="blue", justify="right")
chat_area.tag_config("friend", foreground="green", justify="left")

bottom_frame = tk.Frame(window)
bottom_frame.pack(fill=tk.X, padx=10, pady=5)

message_entry = tk.Entry(bottom_frame, font=("Arial", 12))
message_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))
message_entry.bind("<Return>", lambda e: send_message())

hd_var = tk.BooleanVar()
tk.Checkbutton(bottom_frame, text="HD", variable=hd_var).pack(side=tk.LEFT)

tk.Button(bottom_frame, text="File/Img", command=send_media, bg="lightgray").pack(side=tk.RIGHT, padx=2)
tk.Button(bottom_frame, text="Send", command=send_message, bg="lightblue").pack(side=tk.RIGHT)

threading.Thread(target=receive_thread, daemon=True).start()
window.mainloop()