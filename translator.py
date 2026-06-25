import sys
print(sys.version)

from ollama import chat

import pyperclip

import tkinter as tk
from tkinter.scrolledtext import ScrolledText
import threading
import time
from ctk_markdown import CTkMarkdown
import customtkinter as ctk


# root = tk.Tk()

root = ctk.CTk()

# window setup
root.title('Clip Translator')

window_width = 800
window_height = 300

# get the screen dimension
screen_width = root.winfo_screenwidth()
screen_height = root.winfo_screenheight()

# find the center point
center_x = int(screen_width/2 - window_width / 2)
center_y = int(screen_height/2 - window_height / 2)

# set the position of the window to the center of the screen
root.geometry(f'{window_width}x{window_height}+{center_x}+{center_y}')

root.resizable(True, True)
root.attributes('-alpha', 0.8)
root.attributes('-topmost', 1)
# Ensure icon is in the assets folder relative to your script.
root.iconbitmap('./assets/icon.ico')
# root.iconphoto(False, tk.PhotoImage(file='./assets/icon.png'))

# # Remove the menubar
# root.config(menu="")

# root.grid_columnconfigure(0, weight=1)
# root.grid_rowconfigure(0, weight=1)


# place a label on the root window
# message = tk.Label(frame_message, text="BOOTING UP...", font=("Monofur Nerd Font Mono", 16), justify="left")


# message.grid(row=0, column=0, padx=20, pady=10, sticky="ew")

# message.pack(pady=16)
# message.pack(fill="both", expand=False, padx=16, pady=6)

# text = ScrolledText(root, width=80,  height=8)
# text.pack(padx = 10, pady=10,  fill=tk.BOTH, side=tk.LEFT, expand=True)


# label = tk.Label(root, text="", font=("Helvetica", 14))
# label.pack(pady=20)




from tinydb import TinyDB, Query
db = TinyDB('cache.json')
# import json


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
    # # Get the number of lines in the Text widget
    # line_count = int(message.index("end-1c").split('.')[0])
    # # Set height dynamically, with a minimum of 2 and maximum of 10 lines
    # new_height = min(max(line_count, 2), 10)
    # message.configure(height=new_height)
    if (new_height <= 0):
        lines = message.tk.call((message._textbox, "count", "-update", "-lines", "1.0", "end"))
        lines_disp = message.tk.call((message._textbox, "count", "-update", "-displaylines", "1.0", "end"))
        line_count = lines_disp
        new_height = min(max(line_count, 1), 10)
        # print(lines,lines_disp)
    # print(message._get_widget_scaling())
    # print(message.winfo_height())
    # print(new_height)
    message.configure(height=new_height*(16+0.8)+14.2+1/3)
    # print(message.winfo_height(), message._current_height)
def adjust_input_height_event(event):
    adjust_input_height()

# layout finalize
adjust_input_height(1)
message.bind("<KeyRelease>",adjust_input_height_event) # size calculation always lags by one event ... sigh 
# -> Press will create a scroll bar every new line, and won't update until the next event
#    where as Release will create a new line as soon as the user lets go of the key.
#    When only one event can be used (to save computation), Release feels more responsive

# TODO: send custom message
# message.bind("<KeyRelease>",adjust_input_height_event)


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

            new_input = {'role': 'user', 'content': clipboard_text}
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


        time.sleep(0.01)



thread = threading.Thread(target=run_in_thread, daemon=True)
thread.start()


# keep the window displaying
# try:
#     from ctypes import windll
#     windll.shcore.SetProcessDpiAwareness(1)
# finally:

root.mainloop()




# Below are some reference materials
# Simple SVG visual editor
# https://www.svgviewer.dev/
# Color picler
# https://htmlcolorcodes.com/color-picker/
# About SVG gradient
# https://developer.mozilla.org/en-US/docs/Web/SVG/Tutorials/SVG_from_scratch/Gradients
# The SVG path guide I always use
# https://www.joshwcomeau.com/svg/interactive-guide-to-paths/
# The logo's SVG code
# <svg xmlns="http://www.w3.org/2000/svg" width="512" height="512" viewBox="0 0 512 512" fill="none">
# <defs>
#     <linearGradient id="GradBG" x1="0" x2="0" y1="0" y2="1">
#     <stop offset="0%" stop-color="#FA5571" stop-opacity="1" />
#     <stop offset="50%" stop-color="#FA8D55" stop-opacity="1" />
#     <stop offset="100%" stop-color="#FADF55" stop-opacity="1" />
#     </linearGradient>
#     <linearGradient id="GradMain" x1="0" x2="0" y1="0" y2="1">
#     <stop offset="0%" stop-color="#55FADE" stop-opacity="1" />
#     <stop offset="50%" stop-color="#55C3FA" stop-opacity="1" />
#     <stop offset="100%" stop-color="#5571FA" stop-opacity="1" />
#     </linearGradient>
# </defs>
# <style>
#     #rect1 {
#     fill: url("#GradBG");
#     }
#     #rect2 {
#     fill: url("#GradMain");
#     }
# </style>

# <rect id="rect1" width="512" height="512" rx="64"/>

# <path d="
#     M100 256 h312 
#     a28 28 0 0 1 15 50    
#     L310 400
#     a100 120 0 0 1 -108 0
#     L85 306
#     a28 28 0 0 1 15 -50
#     " 
#     transform="translate(-51,-48) scale(1.2)" id="rect2"/>
# <rect opacity="1" x="220" y="180" width="80" height="80" rx="20" 
#     transform="rotate(-30 220 180) scale(1.15)" id="rect2"/>
# <rect x="170" y="35" width="120" height="120" rx="20" 
#     transform="rotate(30 170 35) scale(1.15)"  id="rect2"/>

# <path d="
#     M100 256 h312 
#     a28 28 0 0 1 15 50    
#     L310 400
#     a100 120 0 0 1 -108 0
#     L85 306
#     a28 28 0 0 1 15 -50
#     " 
#     transform="translate(0,30)" fill="white"/>
# <rect opacity="1" x="260" y="200" width="80" height="80" rx="20" 
#     transform="rotate(-30 260 200)" fill="white"/>
# <rect x="210" y="80" width="120" height="120" rx="20" 
#     transform="rotate(30 210 80)" fill="white"/>

    
# <!-- <path d="M19.375 36.7818V100.625C19.375 102.834 21.1659 104.625 23.375 104.625H87.2181C90.7818 104.625 92.5664 100.316 90.0466 97.7966L26.2034 33.9534C23.6836 31.4336 19.375 33.2182 19.375 36.7818Z" fill="white"/>
# <circle cx="63.2109" cy="37.5391" r="18.1641" fill="black"/>
# <rect opacity="0.4" x="81.1328" y="80.7198" width="17.5687" height="17.3876" rx="4" transform="rotate(-45 81.1328 80.7198)" fill="#FDBA74"/> -->
# </svg>


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
