import sys
# print(sys.version)
# import platform
# print([platform.system(),platform.release()])

# ollama backend access
from ollama import chat

# database
from tinydb import TinyDB, Query
db = TinyDB('cache.json')
# import json

# clipboard access (tkinter has one too)
import pyperclip

# gui
import tkinter as tk
from tkinter.scrolledtext import ScrolledText
from ctk_markdown import CTkMarkdown
import customtkinter as ctk

# tasking
import threading
import time

# resources linking
import pathlib
src_dir = pathlib.Path(__file__).parent.resolve()


# window setup
root = ctk.CTk()
root.title('Clip Translator')
window_width = 800
window_height = 300
## get the screen dimension
screen_width = root.winfo_screenwidth()
screen_height = root.winfo_screenheight()
## find the center point
center_x = int(screen_width/2 - window_width / 2)
center_y = int(screen_height/2 - window_height / 2)
## set the position of the window to the center of the screen
root.geometry(f'{window_width}x{window_height}+{center_x}+{center_y}')
root.resizable(True, True)
root.attributes('-alpha', 0.8)
root.attributes('-topmost', 1)
root.iconbitmap(src_dir/'assets'/'icon.ico')

# title bar customizaton
try:
    # https://github.com/TomSchimansky/CustomTkinter/discussions/1011
    from ctypes import windll, byref, sizeof, c_int

    HWND = windll.user32.GetParent(root.winfo_id()) # the window we want to change

    """
    DWMWA_ATTRIBUTES (for windows 11 title bar) 
    CAPTION COLOR (HEADER) = 35
    BORDER COLOR = 34
    TITLE COLOR = 36
    """

    DWMWA_ATTRIBUTE = 35

    COLOR = 0x00222222 # color should be in hex order: 0x00bbggrr

    res = windll.dwmapi.DwmSetWindowAttribute(HWND, DWMWA_ATTRIBUTE, byref(c_int(COLOR)), sizeof(c_int))
    if (res !=0 ) :
        # print(f"trying to set title bar color but failed, with error code: {res}. This is okay.")
        pass
except Exception as e:
    # print(f"trying to set title bar color but failed, That's okay.")
    pass



# # status message?
# message = tk.Label(frame_message, text="BOOTING UP...", font=("Monofur Nerd Font Mono", 16), justify="left")


# status and state init
is_running = True
is_listening_to_clipboard = False
clipboard_text = pyperclip.paste()
messages = []

def toggle_arm():
    global is_listening_to_clipboard
    global clipboard_text
    is_listening_to_clipboard = not is_listening_to_clipboard
    # refresh to avoid reading the content before arming
    clipboard_text = pyperclip.paste()



# layout init

frame_response = ctk.CTkFrame(root, height=10)
frame_response.grid_columnconfigure(0, weight=1)
frame_response.grid_rowconfigure(0, weight=1)
frame_response.pack(fill="both", expand=True, padx=0, pady=0)
renderer = CTkMarkdown(frame_response, font=("Monofur Nerd Font Mono", 16), height=10)
renderer.grid(row=0, column=0, padx=10, pady=(10,0), sticky="nsew")
renderer.set_markdown("""*awaiting response*...""")


frame_status = ctk.CTkFrame(root, fg_color="transparent", height=10)
frame_status.grid_columnconfigure(0, weight=1)
frame_status.grid_rowconfigure(0, weight=1)
frame_status.pack(fill="both", expand=False, padx=0, pady=0)
status_line = ctk.CTkFrame(frame_status, fg_color="transparent", height=10)
status_line.grid(row=0, column=0, padx=10, pady=(3,3), sticky="nsew")

armed_icon_label = ctk.CTkLabel(status_line, text="󰤁", height=8, font=("Monofur Nerd Font Mono", 14, "bold"), text_color="#878787")
armed_icon_label.place(relx=0.0, x=15, rely=0.5, anchor="e")
armed_hint_label = ctk.CTkLabel(status_line, text="", height=8, font=("Monofur Nerd Font Mono", 30), text_color="#FA8C55")
armed_hint_label.place(relx=0.0, x=35, rely=0.5, anchor="e")

readiness_icon_label = ctk.CTkLabel(status_line, text="", height=8, font=("Monofur Nerd Font Mono", 14, "bold"), text_color="#878787")
readiness_icon_label.place(relx=0.0, x=55, rely=0.5, anchor="e")
readiness_hint_label = ctk.CTkLabel(status_line, text="", height=8, font=("Monofur Nerd Font Mono", 30), text_color="#FA8C55")
readiness_hint_label.place(relx=0.0, x=75, rely=0.5, anchor="e")

busyness_icon_label = ctk.CTkLabel(status_line, text="", height=8, font=("Monofur Nerd Font Mono", 14, "bold"), text_color="#878787")
busyness_icon_label.place(relx=0.0, x=95, rely=0.5, anchor="e")
busyness_hint_label = ctk.CTkLabel(status_line, text="", height=8, font=("Monofur Nerd Font Mono", 30), text_color="#55FAE7")
busyness_hint_label.place(relx=0.0, x=115, rely=0.5, anchor="e")

button_toggle_arm = ctk.CTkButton(status_line, text="󰤁", command=toggle_arm,
                                  width=30, height=10, font=("Monofur Nerd Font Mono", 12), 
                                  fg_color="#444444", hover_color="#FA7163")
button_toggle_arm.place(relx=0.0, x=160, rely=0.5, anchor="e")

message_hint_label = ctk.CTkLabel(status_line, text="󰘶 󰌑", height=8, font=("Monofur Nerd Font Mono", 20), text_color="#878787")
message_hint_label.place(relx=1.0, x=-10, rely=0.5, anchor="e")


frame_message = ctk.CTkFrame(root, fg_color="transparent", height=10)
frame_message.grid_columnconfigure(0, weight=1)
frame_message.grid_rowconfigure(0, weight=1)
frame_message.pack(fill="both", expand=False, padx=0, pady=0)
message = ctk.CTkTextbox(frame_message, font=("Monofur Nerd Font Mono", 16), 
                        #  border_color="#F5F5F5", border_width=2,
                        wrap='char',
                        fg_color="#353535",
                         )
message.tag_config("status", foreground="#FA8C55") # #55C3FA
message.tag_config("input")
message.insert("end","BOOTING UP...","status")
message.grid(row=0, column=0, padx=10, pady=(0,10), sticky="ew")

# layout helpers

def adjust_input_height(new_height=0):
    if (new_height <= 0):
        lines = message.tk.call((message._textbox, "count", "-update", "-lines", "1.0", "end"))
        lines_disp = message.tk.call((message._textbox, "count", "-update", "-displaylines", "1.0", "end"))
        line_count = lines_disp
        new_height = min(max(line_count, 1), 10)
    message.configure(height=new_height*(16+0.8)+14.2+1/3)
def adjust_input_height_event(event):
    adjust_input_height()

# layout finalize
adjust_input_height(1)
message.bind("<KeyRelease>",adjust_input_height_event) # size calculation always lags by one event ... sigh 
# -> Press will create a scroll bar every new line, and won't update until the next event
#    where as Release will create a new line as soon as the user lets go of the key.
#    When only one event can be used (to save computation), Release feels more responsive


# # closing
# def on_closing():  
#     with open('cache.txt', 'w') as file:
#         for msg in messages:
#             file.write(json.dumps(msg) + '\n')
#     root.destroy()
# root.protocol("WM_DELETE_WINDOW", on_closing)


# history query
curr_convo_idx = len(db)

def get_message_history_at_curr_idx():
    global curr_convo_idx
    history_message = db.get(doc_id=curr_convo_idx)
    if (history_message):
        # print(history_message)
        if (isinstance(history_message,list)):
            history_message = history_message[0]
        renderer.set_markdown(history_message['res']['content'])

def get_idx_message(idx:int):
    global curr_convo_idx
    curr_convo_idx = idx
    get_message_history_at_curr_idx()

slider_msg = ctk.CTkSlider(status_line, from_=1, to=len(db), command=lambda x: get_idx_message(int(x)), 
                           button_color="#444444", button_hover_color="#FA7163")
slider_msg.set(len(db))
slider_msg.configure(number_of_steps=len(db)-1)
slider_msg.place(relx=0.0, x=485, rely=0.5, anchor="e")

def get_prev_message():
    global curr_convo_idx
    if (curr_convo_idx > 1):
        curr_convo_idx -= 1
        try:
            slider_msg.set(curr_convo_idx)
        except:
            pass
        get_message_history_at_curr_idx()
    
def get_next_message():
    global curr_convo_idx
    if (curr_convo_idx < len(db)):
        curr_convo_idx += 1
        try:
            slider_msg.set(curr_convo_idx)
        except:
            pass
        get_message_history_at_curr_idx()

button_prev_msg = ctk.CTkButton(status_line, text="", command=get_prev_message, 
                                width=30, height=10, font=("Monofur Nerd Font Mono", 12), 
                                fg_color="#444444", hover_color="#FA7163")
button_prev_msg.place(relx=0.0, x=240, rely=0.5, anchor="e")
button_next_msg = ctk.CTkButton(status_line, text="", command=get_next_message, 
                                width=30, height=10, font=("Monofur Nerd Font Mono", 12), 
                                fg_color="#444444", hover_color="#FA7163")
button_next_msg.place(relx=0.0, x=280, rely=0.5, anchor="e")



# execution prep

def send_request(msg):
    global messages
    new_input = {'role': 'user', 'content': msg}
    busyness_hint_label.configure(text_color="#FA8C55")

    response = chat(
        model='gemma4',
        messages=[*messages, new_input],
        think=False,
        stream=False,
    )
    busyness_hint_label.configure(text_color="#55FAE7")

    if (response.message.content):
        new_response = {'role': 'assistant', 'content': response.message.content}
        messages += [
            new_input,
            new_response,
        ]

        renderer.set_markdown(response.message.content)

        db.insert({"usr":new_input,"res":new_response})
        curr_convo_idx = len(db)
        slider_msg.set(len(db))
        slider_msg.configure(number_of_steps=len(db)-1)
    else:
        renderer.set_markdown("... got no response ... ")

def run_in_thread():
    global is_running
    global is_listening_to_clipboard
    global clipboard_text
    global messages
    global curr_convo_idx



    initializing_message = {'role': 'user', 'content': 
        r"Hi! I'm playing a text heavy game in Japanese, its original language. \
        Would you be able to help with translating some dialogues and instructions \
        into English for me? \
        The text will be extracted via OCR, so ask me to verify \
        if you find potential errors. \
        Otherwise, for now, please limit your response contents to \
        the following 3 sections: \
        a few English translation options, a romanji representation, \
        and a glossary for 2 or fewer vocabs of your choosing \
        (select by real life usefullness) in bullet point form. \
        I'd like to learn a few words at a time. \
        (Please also explain the word form if it differs from the dictionaty form.) \
        Do not include any other additional note. \
        Thank you!"
    }

    initializing_response = {'role': 'assistant', 'content': 
        r"That sounds like a fascinating challenge! \
        I would be happy to help you translate and understand the Japanese text from your game. \
        Dealing with OCR can be tricky, \
        so I will definitely ask you to verify anything that looks questionable.\n\
        \n\
        I understand your preferred format perfectly:\
        1. A few English translation options.\n\
        2. Romanji representation.\n\
        3. A concise glossary (max 2 words), \
        focusing on real-life usefulness, \
        including grammatical notes if the form is different from the dictionary entry.\n\
        \n\
        Please go ahead and paste or provide the first piece of Japanese text you need help with! \
        I'm ready when you are."
    }

    use_canned_init_response = False

    if (use_canned_init_response) :
        messages = [initializing_message,initializing_response]
    else :
        messages = [initializing_message]

    # print(messages)

    response = chat(
        model='gemma4',
        messages=messages,
        think=False,
        stream=False,
    )

    # root.after(0, lambda: message.config(text="SYSTEM READY"))
    # if (response.done):
    message.delete("1.0","end")
    message.insert("end","SYSTEM READY!","status")
    readiness_hint_label.configure(text_color="#55FAE7")
    if (use_canned_init_response) :
        renderer.set_markdown("""*I'm ready when you are*...""")
        # renderer.set_markdown(response.message.content)
    else :
        if (response.message.content):
            messages += [{'role': 'assistant', 'content': response.message.content}]
            renderer.set_markdown(response.message.content)
            

    # renderer.set_markdown(response.message.content)






    while is_running:
        if (is_listening_to_clipboard):
            armed_hint_label.configure(text_color="#55FAE7")
        else:
            armed_hint_label.configure(text_color="#FA8C55")
            continue

        new_text = pyperclip.paste()
        if (clipboard_text != new_text) :
            clipboard_text = new_text
            # root.after(0, lambda: message.config(text=clipboard_text))
            message.delete("1.0","end")
            message.insert("end",clipboard_text,"input")
            adjust_input_height()
            # renderer.set_markdown(clipboard_text)

            send_request(clipboard_text)


        time.sleep(0.01)

# send custom message
def send_custom_message(event):
    # print("messaging")
    # print(message.get("1.0", "end-1c"))
    # print(event)
    send_request(message.get("1.0", "end-1c"))
    return "break" # this prevents further bound functions from being invoked. (tkinter inline doc)
message.bind("<Shift-Return>",send_custom_message)


thread = threading.Thread(target=run_in_thread, daemon=True)
thread.start()


# keep the window displaying
# try:
#     from ctypes import windll
#     windll.shcore.SetProcessDpiAwareness(1)
# finally:

root.mainloop()




# Below are some reference code snippets


# Response streaming
# stream = chat(
#     model='gemma4',
#     messages=[{'role': 'user', 'content': r"Hi! I'm playing a text heavy game in Japanese, its original language. Would you be able to help with translating some dialogues and instructions into english for me? The text will be extracted via OCR, so ask me to verify if you find potential errors. Otherwise, for now, please limit your response contents to a few translation options, a romanji representation, and a glossary for 2 or fewer vocabs of your choosing (select by real life usefullness) in your response? I'd like to learn a few words at a time. (Please also explain the word form if it differs from the dictionaty form.) Thank you!"
#                }],
#     think=False,
#     stream=True,
# )

# root.after(0, lambda: message.config(text="SYSTEM READY"))

# for chunk in stream:
#     if chunk.message.thinking and not in_thinking:
#         in_thinking = True
#         print('Thinking:\n', end='')

#     if chunk.message.thinking:
#         print(chunk.message.thinking, end='')
#     elif chunk.message.content:
#         if in_thinking:
#             print('\n\nAnswer:\n', end='')
#             in_thinking = False
#             print(chunk.message.content, end='')
