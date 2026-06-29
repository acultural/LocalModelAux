import sys
from typing import Tuple
# print(sys.version)
# import platform
# print([platform.system(),platform.release()])

# ollama backend access
from ollama import chat

# database
from tinydb import TinyDB, Query # TODO: switch to sqlite maybe
import sqlite3
# import json

# clipboard access (tkinter has one too)
import pyperclip

# gui
import tkinter as tk
from tkinter.scrolledtext import ScrolledText
# from ctk_markdown import CTkMarkdown
from external.ctk_markdown import CTkMarkdown
import customtkinter as ctk

# tasking
import threading
import time

# resources linking
import pathlib
SRC_DIR = pathlib.Path(__file__).parent.resolve()

# config management
import tomlkit


class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        # config loading
        self._load_config()

        # frontend basics
        self._setup_window()
        self._font_customization()
        # TODO: window scaling is a bit weird; ctk makes a bunch of internal adjustments
        self.ui_scale = self.config["ui"]["scale"]
        ctk.set_widget_scaling(1)
        ctk.set_window_scaling(1)

        # status and state init
        self.is_running = True
        self._has_custom_msg = False
        self.is_listening_to_clipboard = True
        self.clipboard_text = pyperclip.paste() # TODO: below
        # above: after idling, this (not here) can sometimes throw an error;
        # try to catch and handle it.
        self.messages = []

        # model_selection
        self._setup_model()

        # history query
        self._setup_db()
        # frontend setup
        self._setup_layout()

        # connect to backend and start the backend functional loop
        self.thread = threading.Thread(target=self.run_in_thread, daemon=True)
        self.run()
        # TODO: add the ability to reset the session
        # TODO: add the ability to save setting changes the model setup
        # TODO: remember to add the config file when building, and save the build script

    def _setup_model(self):
        self.model_name = self.config["backend"]["model_name"]
        self.initializing_message = {'role': 'user', 'content': self.config["backend"]["init_msg"]}
        self.initializing_response = {'role': 'assistant', 'content': self.config["backend"]["init_res"]}
        self.use_canned_init_response = False

        if (self.use_canned_init_response) :
            self.messages = [self.initializing_message,self.initializing_response]
        else :
            self.messages = [self.initializing_message]
        # print(messages)

    def _setup_db(self):
        # self.cache_path = 'cache.json'
        self.cache_path = self.config["paths"]["cache"]
        self.db = TinyDB(self.cache_path) # TODO: replace with sqlite
        # the first displayed result is not in fact recorded, so we use next_id here
        # NOTE: with TinyDB, assume that the indices are consecutive (unbroken chain), and starts with 1
        self.curr_convo_idx = len(self.db)+1

    def _update_config(self):
        """writes config from ui into state"""
        self.config["backend"]["model_name"] = self.entry_model.get()
        self.config["paths"]["cache"] = self.entry_cache.get()
        self.config["backend"]["init_msg"] = self.box_init_msg.get("1.0","end")
        self.config["backend"]["init_res"] = self.box_init_res.get("1.0","end")

    def _update_config_and_reset(self):
        self.config["backend"]["model_name"] = self.entry_model.get()
        self.config["paths"]["cache"] = self.entry_cache.get()
        self.config["backend"]["init_msg"] = self.box_init_msg.get("1.0","end")
        self.config["backend"]["init_res"] = self.box_init_res.get("1.0","end")
        self.is_running = False
        self.thread.join()
        self._setup_model()
        self._setup_db()
        self.is_running = True
        self.run()
        # TODO: acknowledgement

    def _save_config(self):
        self._update_config()
        with open(SRC_DIR/"config.toml","w") as f:
            tomlkit.dump(self.config,f)
        # TODO: acknowledgement

    def _revert_config(self):
        self._load_config()
        self._render_settings()

    def _load_config(self):
        with open(SRC_DIR/"config.toml","r") as f:
            self.config = tomlkit.load(f)

    def _render_settings(self):
        self.entry_model.delete("0","end")
        self.entry_model.insert('end',self.config["backend"]["model_name"])
        self.entry_cache.delete("0","end")
        self.entry_cache.insert('end',self.config["paths"]["cache"])
        self.box_init_msg.delete("1.0","end")
        self.box_init_msg.insert('end',self.config["backend"]["init_msg"])
        self.box_init_res.delete("1.0","end")
        self.box_init_res.insert('end',self.config["backend"]["init_res"])
        

    def _setup_window(self):
        # default size
        window_width = 800
        window_height = 360
        # set the position of the window to the center of the screen
        screen_scaling = self._get_window_scaling()
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        center_x = int((screen_width - window_width)*(screen_scaling/2))
        center_y = int((screen_height - window_height)*(screen_scaling/2))
        self.geometry(f'{window_width}x{window_height}+{center_x}+{center_y}')
        # window attributs
        self.resizable(True, True)
        self.attributes('-alpha', self.config["ui"]["alpha"])
        self.attributes('-topmost', 1)
        # title bar
        self.title('Clip Translator')
        self.iconbitmap(SRC_DIR/'assets'/'icon.ico')
        self._title_bar_customization()

    def _title_bar_customization(self):
        # title bar customizaton
        # only works for win 11
        # https://github.com/TomSchimansky/CustomTkinter/discussions/1011
        try:
            from ctypes import windll, byref, sizeof, c_int
            HWND = windll.user32.GetParent(self.winfo_id()) # the window we want to change
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

    def _font_customization(self):
        # custom font setup
        # only works on windows
        # https://github.com/orgs/pyinstaller/discussions/6266
        try:
            import ctypes.wintypes
            wingdi = ctypes.CDLL("gdi32")
            wingdi.AddFontResourceExW.argtypes = [ctypes.c_wchar_p, ctypes.wintypes.DWORD, ctypes.c_void_p]
            res = wingdi.AddFontResourceExW(str(SRC_DIR/"MonofurNerdFontMono-Regular.ttf"), 0x10, 0)
            if (res !=0 ) :
                # print(f"trying to set custom font but failed, with error code: {res}. This is okay.")
                pass
        except Exception as e:
            # print(f"trying to set custom font but failed, That's okay.")
            pass

    def _setup_layout(self):
        # layout init
        # TODO: make frames into classes

        # TODO: +, -
        self.bind("<Control-]>",self.scale_up)
        self.bind("<Control-[>",self.scale_down)

        # response display
        frame_response = ctk.CTkFrame(self, fg_color="transparent", height=10)
        frame_response.grid_columnconfigure(0, weight=1)
        frame_response.grid_rowconfigure(0, weight=1)
        frame_response.pack(fill="both", expand=True, padx=0, pady=0)
        renderer = CTkMarkdown(frame_response, 
            font=(self.config["ui"]["font"], 16), fonts=self.config["ui"]["font"], 
            type_scale = {        
                'h1': 2,
                'h2': 1.5,
                'h3': 1.25,
                'h4': 1,
                'h5': 0.875,
                'h6': 0.85,
                'code_inline': 0.85,
                'code_block': 0.85,
                'code_ui': 9/15, # lang_label & copy_btn
                'blockquote': 1,
                'list_number': 1, 
                'table_header': 1,
                'table_cell': 1,
            },
            height=10)
        renderer.grid(row=0, column=0, padx=10, pady=(10,0), sticky="nsew")
        renderer.set_markdown("""*awaiting response*...""")

        # status bar
        frame_status = ctk.CTkFrame(self, fg_color="transparent", height=10)
        frame_status.grid_columnconfigure(0, weight=1)
        frame_status.grid_rowconfigure(0, weight=1)
        frame_status.pack(fill="both", expand=False, padx=0, pady=0)
        status_line = ctk.CTkFrame(frame_status, fg_color="transparent", height=10)
        status_line.grid(row=0, column=0, padx=10, pady=(3,3), sticky="nsew")

        ## status displays
        armed_icon_label = ctk.CTkLabel(status_line, text="󰤁", height=8, font=(self.config["ui"]["font"], 14, "bold"), text_color="#878787")
        armed_icon_label.place(relx=0.0, x=15, rely=0.5, anchor="e")
        armed_hint_label = ctk.CTkLabel(status_line, text="", height=8, font=(self.config["ui"]["font"], 30), text_color="#FA8C55")
        armed_hint_label.place(relx=0.0, x=35, rely=0.5, anchor="e")

        readiness_icon_label = ctk.CTkLabel(status_line, text="", height=8, font=(self.config["ui"]["font"], 14, "bold"), text_color="#878787")
        readiness_icon_label.place(relx=0.0, x=55, rely=0.5, anchor="e")
        readiness_hint_label = ctk.CTkLabel(status_line, text="", height=8, font=(self.config["ui"]["font"], 30), text_color="#FA8C55")
        readiness_hint_label.place(relx=0.0, x=75, rely=0.5, anchor="e")

        busyness_icon_label = ctk.CTkLabel(status_line, text="", height=8, font=(self.config["ui"]["font"], 14, "bold"), text_color="#878787")
        busyness_icon_label.place(relx=0.0, x=95, rely=0.5, anchor="e")
        busyness_hint_label = ctk.CTkLabel(status_line, text="", height=8, font=(self.config["ui"]["font"], 30), text_color="#55FAE7")
        busyness_hint_label.place(relx=0.0, x=115, rely=0.5, anchor="e")

        ## status toggle
        button_toggle_arm = ctk.CTkButton(status_line, text="󰤁", command=self.toggle_arm,
                                        width=30, height=10, font=(self.config["ui"]["font"], 12), 
                                        fg_color="#444444", hover_color="#FA7163")
        button_toggle_arm.place(relx=0.0, x=160, rely=0.5, anchor="e")
        button_toggle_settings = ctk.CTkButton(status_line, text="", command=self.toggle_settings,
                                        width=30, height=10, font=(self.config["ui"]["font"], 12), 
                                        fg_color="#444444", hover_color="#FA7163")
        button_toggle_settings.place(relx=0.0, x=200, rely=0.5, anchor="e")

        ## message history navigation
        button_prev_msg = ctk.CTkButton(status_line, text="", command=self.get_prev_message, 
                                        width=30, height=10, font=(self.config["ui"]["font"], 12), 
                                        fg_color="#444444", hover_color="#FA7163")
        button_prev_msg.place(relx=0.0, x=260, rely=0.5, anchor="e")
        button_next_msg = ctk.CTkButton(status_line, text="", command=self.get_next_message, 
                                        width=30, height=10, font=(self.config["ui"]["font"], 12), 
                                        fg_color="#444444", hover_color="#FA7163")
        button_next_msg.place(relx=0.0, x=300, rely=0.5, anchor="e")
        slider_msg = ctk.CTkSlider(status_line, from_=1, to=len(self.db), command=lambda x: self.get_idx_message(int(x)), 
                                button_color="#444444", button_hover_color="#FA7163")
        slider_msg.set(len(self.db))
        slider_msg.configure(number_of_steps=len(self.db)-1)
        slider_msg.place(relx=0.0, x=505, rely=0.5, anchor="e")

        ## message input hint
        message_hint_label = ctk.CTkLabel(status_line, text="󰘶 󰌑", height=8, font=(self.config["ui"]["font"], 20), text_color="#878787")
        message_hint_label.place(relx=1.0, x=-10, rely=0.5, anchor="e")

        # TODO: make into class
        frame_settings = ctk.CTkFrame(self, fg_color="transparent")
        frame_settings.grid_columnconfigure(0, weight=1)
        frame_settings.grid_rowconfigure(0, weight=1)
        frame_settings.pack(fill="both", expand=False, padx=0, pady=0)
        frame_settings_inner = ctk.CTkFrame(frame_settings, fg_color="#353535")
        frame_settings_inner.grid_columnconfigure(0, weight=1)
        frame_settings_inner.grid_rowconfigure(0, weight=1)
        frame_settings_inner.grid(row=0, column=0, padx=10, pady=(5,0), sticky="nsew",)
        
        setting_main_label = ctk.CTkLabel(frame_settings_inner, text="SETTINGS", font=(self.config["ui"]["font"], 14), text_color="#BDBDBD")
        setting_main_label.grid(row=0, column=0, padx=10, pady=(0,0), sticky="ew")

        frame_settings_entries = ctk.CTkFrame(frame_settings_inner, fg_color="transparent")
        frame_settings_entries.grid_columnconfigure(1, weight=1)
        frame_settings_entries.grid_rowconfigure(0, weight=1)
        frame_settings_entries.grid(row=1, column=0, padx=10, pady=(0, 0), sticky="nsew")
        setting_model_label = ctk.CTkLabel(frame_settings_entries, text="Model", height=8, font=(self.config["ui"]["font"], 13), text_color="#BDBDBD")
        setting_model_label.grid(row=0, column=0, padx=10, pady=(0,0), sticky="w")
        entry_model = ctk.CTkEntry(frame_settings_entries, font=(self.config["ui"]["font"], 14), 
                                   border_width=0, height=23, fg_color='#232323')
        
        entry_model.grid(row=0, column=1, padx=10, pady=(0,0), sticky="ew")
        setting_cache_label = ctk.CTkLabel(frame_settings_entries, text="Cache", font=(self.config["ui"]["font"], 13), text_color="#BDBDBD")
        setting_cache_label.grid(row=1, column=0, padx=10, pady=(0,0), sticky="w")
        entry_cache = ctk.CTkEntry(frame_settings_entries, font=(self.config["ui"]["font"], 14), 
                                   border_width=0, height=23, fg_color='#232323')
        entry_cache.grid(row=1, column=1, padx=10, pady=(0,0), sticky="ew")

        frame_settings_boxes = ctk.CTkFrame(frame_settings_inner, fg_color="transparent")
        frame_settings_boxes.grid_columnconfigure((0,1), weight=1)
        frame_settings_boxes.grid_rowconfigure(0, weight=1)
        frame_settings_boxes.grid(row=2, column=0, padx=10, pady=(0,10), sticky="nsew")
        setting_input_label = ctk.CTkLabel(frame_settings_boxes, text="Init Input", font=(self.config["ui"]["font"], 13), text_color="#BDBDBD")
        setting_input_label.grid(row=0, column=0, padx=(0,3), pady=(0,0), sticky="ew")
        box_init_msg = ctk.CTkTextbox(frame_settings_boxes,
                                      font=(self.config["ui"]["font"], 14), 
                                      #  border_color="#F5F5F5", border_width=2,
                                      wrap='char',
                                      fg_color="#232323",
                                      height=100
                                      )
        box_init_msg.insert('end',self.initializing_message['content'])
        box_init_msg.grid(row=1, column=0, padx=(0,3), pady=(0,0), sticky="ew")
        setting_output_label = ctk.CTkLabel(frame_settings_boxes, text="Init Response", font=(self.config["ui"]["font"], 13), text_color="#BDBDBD")
        setting_output_label.grid(row=0, column=1, padx=(3,0), pady=(0,0), sticky="we")
        box_init_res = ctk.CTkTextbox(frame_settings_boxes,
                                      font=(self.config["ui"]["font"], 14), 
                                      #  border_color="#F5F5F5", border_width=2,
                                      wrap='char',
                                      fg_color="#232323",
                                      height=100
                                      )
        box_init_res.grid(row=1, column=1, padx=(3,0), pady=(0,0), sticky="ew")


        # TODO: setting related actions & init file
        frame_settings_buttons = ctk.CTkFrame(frame_settings_inner, fg_color="transparent")
        frame_settings_buttons.grid_columnconfigure((0,1,2), weight=1)
        frame_settings_buttons.grid_rowconfigure(0, weight=1)
        frame_settings_buttons.grid(row=3, column=0, padx=10, pady=(0,10), sticky="nsew")
        button_revert_settings = ctk.CTkButton(frame_settings_buttons, text="Revert Settings", command=self._revert_config,
                                        height=12, font=(self.config["ui"]["font"], 12), 
                                        fg_color="#444444", hover_color="#FA7163")
        button_revert_settings.grid(row=0, column=0, padx=(0,3), pady=(0,0), sticky="ew")
        button_save_settings = ctk.CTkButton(frame_settings_buttons, text="Save New Settings", command=self._save_config,
                                        height=12, font=(self.config["ui"]["font"], 12), 
                                        fg_color="#444444", hover_color="#FA7163")
        button_save_settings.grid(row=0, column=1, padx=(3,3), pady=(0,0), sticky="ew")
        button_reload = ctk.CTkButton(frame_settings_buttons, text="Reload With Settings", command=self._update_config_and_reset,
                                        height=12, font=(self.config["ui"]["font"], 12), 
                                        fg_color="#444444", hover_color="#FA7163")
        button_reload.grid(row=0, column=2, padx=(3,0), pady=(0,0), sticky="ew")


        # input area
        frame_message = ctk.CTkFrame(self, fg_color="transparent", height=10)
        frame_message.grid_columnconfigure(0, weight=1)
        frame_message.grid_rowconfigure(0, weight=1)
        frame_message.pack(fill="both", expand=False, padx=0, pady=0)
        message = ctk.CTkTextbox(frame_message, font=(self.config["ui"]["font"], 16), 
                                #  border_color="#F5F5F5", border_width=2,
                                wrap='char',
                                fg_color="#353535",
                                )
        message.tag_config("status", foreground="#FA8C55") # #55C3FA
        message.tag_config("history", foreground="#878787") # #55C3FA
        message.tag_config("input")
        message.insert("end","BOOTING UP...","status")
        message.grid(row=0, column=0, padx=10, pady=(0,10), sticky="ew")
        message.bind("<Shift-Return>",self.send_custom_message)


        # layout finalize
        self.message = message
        self.renderer = renderer
        self.slider_msg = slider_msg
        self.busyness_hint_label = busyness_hint_label
        self.readiness_hint_label = readiness_hint_label
        self.armed_hint_label = armed_hint_label
        self.frame_message = frame_message
        self.frame_status = frame_status
        self.frame_settings = frame_settings
        # TODO: put into frame_settings when it's a class
        self.entry_model = entry_model
        self.entry_cache = entry_cache
        self.box_init_msg = box_init_msg
        self.box_init_res = box_init_res
        self._render_settings()
        frame_settings.pack_forget()
        
        self.adjust_input_height(1)
        message.bind("<KeyRelease>",self.adjust_input_height_event) 
        # size calculation always lags by one event ... sigh 
        # -> Press will create a scroll bar every new line, and won't update until the next event
        #    where as Release will create a new line as soon as the user lets go of the key.
        #    When only one event can be used (to save computation), Release feels more responsive

        

    def toggle_arm(self):
        self.is_listening_to_clipboard = not self.is_listening_to_clipboard
        # refresh to avoid reading the content before arming
        self.clipboard_text = pyperclip.paste()

    def toggle_settings(self):
        if (self.frame_settings.winfo_viewable()):
            self.frame_settings.pack_forget()
        else:
            self.frame_settings.pack(before=self.frame_status, fill="both", expand=False, padx=0, pady=0)

    def adjust_input_height(self,new_height=0):
        if (new_height <= 0):
            lines = self.message.tk.call((self.message._textbox, "count", "-update", "-lines", "1.0", "end"))
            lines_disp = self.message.tk.call((self.message._textbox, "count", "-update", "-displaylines", "1.0", "end"))
            line_count = lines_disp
            new_height = min(max(line_count, 1), 10)
        self.message.configure(height=new_height*(16+0.8)+14.2+1/3)

    def adjust_input_height_event(self,event):
        self.adjust_input_height()

    def get_message_history_at_curr_idx(self):
        history_message = self.db.get(doc_id=self.curr_convo_idx)
        if (history_message):
            # print(history_message)
            if (isinstance(history_message,list)):
                history_message = history_message[0]
            self.renderer.set_markdown(history_message['res']['content'])
            self.message.delete("1.0","end")
            self.message.insert("end",history_message['usr']['content'],"history")

    def get_idx_message(self,idx:int):
        self.curr_convo_idx = idx
        self.get_message_history_at_curr_idx()


    def get_prev_message(self):
        if (self.curr_convo_idx > 1):
            self.curr_convo_idx -= 1
            # self.renderer._setup_tags()
            try:
                self.slider_msg.set(self.curr_convo_idx)
            except:
                pass
            self.get_message_history_at_curr_idx()
        
    def get_next_message(self):
        if (self.curr_convo_idx < len(self.db)):
            self.curr_convo_idx += 1
            # self.renderer._setup_tags()
            try:
                self.slider_msg.set(self.curr_convo_idx)
            except:
                pass
            self.get_message_history_at_curr_idx()

    # @staticmethod
    def scale_up(self,event):
        new_scale = min(self.ui_scale + 0.1,10) # max scale of 10
        # despite ui_scale not changing, set scaling can still do something
        # likely due to rounding errors. so only call them when the scale changes
        if (new_scale is not self.ui_scale): # max scale of 10
            self.ui_scale = new_scale
            ctk.set_widget_scaling(self.ui_scale)
            ctk.set_window_scaling(self.ui_scale)
        return "break"
    
    # @staticmethod
    def scale_down(self,event):
        new_scale = max(self.ui_scale - 0.1,0.1) # min scale of 0.1
        # despite ui_scale not changing, set scaling can still do something
        # likely due to rounding errors. so only call them when the scale changes
        if (new_scale is not self.ui_scale):
            self.ui_scale = new_scale
            ctk.set_widget_scaling(self.ui_scale)
            ctk.set_window_scaling(self.ui_scale)
        return "break"

    # def on_closing():  
    #     # closing
    #     with open('cache.txt', 'w') as file:
    #         for msg in messages:
    #             file.write(json.dumps(msg) + '\n')
    #     self.destroy()
    # self.protocol("WM_DELETE_WINDOW", on_closing)

    def send_request(self,msg):
        global messages
        new_input = {'role': 'user', 'content': msg}
        self.busyness_hint_label.configure(text_color="#FA8C55")

        response = chat(
            model=self.model_name,
            messages=[*self.messages, new_input],
            think=False,
            stream=False,
        )
        self.busyness_hint_label.configure(text_color="#55FAE7")

        if (response.message.content):
            new_response = {'role': 'assistant', 'content': response.message.content}
            self.messages += [
                new_input,
                new_response,
            ]

            self.renderer.set_markdown(response.message.content)

            self.db.insert({"usr":new_input,"res":new_response})
            self.curr_convo_idx = len(self.db)
            self.slider_msg.set(len(self.db))
            self.slider_msg.configure(number_of_steps=len(self.db)-1)
        else:
            self.renderer.set_markdown("... got no response ... ")

    def run_in_thread(self):

        # session initialization
        self.busyness_hint_label.configure(text_color="#FA8C55")
        response = chat(
            model=self.model_name,
            messages=self.messages,
            think=False,
            stream=False,
        )
        # if (response.done):
        self.message.delete("1.0","end")
        self.message.insert("end","SYSTEM READY!","status")
        self.readiness_hint_label.configure(text_color="#55FAE7")
        if (self.use_canned_init_response) :
            self.renderer.set_markdown("""*I'm ready when you are*...""")
            # renderer.set_markdown(response.message.content)
        else :
            if (response.message.content):
                self.messages += [{'role': 'assistant', 'content': response.message.content}]
                self.renderer.set_markdown(response.message.content)
        self.busyness_hint_label.configure(text_color="#55FAE7")
  
        # perpetural
        while self.is_running:
            if (self.is_listening_to_clipboard):
                self.armed_hint_label.configure(text_color="#55FAE7")
            else:
                self.armed_hint_label.configure(text_color="#FA8C55")
                continue

            if self._has_custom_msg:
                self.send_request(self.message.get("1.0", "end-1c"))
            else:
                new_text = pyperclip.paste()
                if (self.clipboard_text != new_text) :
                    self.clipboard_text = new_text
                    self.message.delete("1.0","end")
                    self.message.insert("end",self.clipboard_text,"input")
                    self.adjust_input_height()
                    self.send_request(self.clipboard_text)

            time.sleep(0.01)

    # send custom message
    def send_custom_message(self,event):
        # print("messaging")
        # print(message.get("1.0", "end-1c"))
        # print(event)
        self._has_custom_msg = True
        # self.send_request(self.message.get("1.0", "end-1c")) # let thread handle it so ui does not block
        return "break" # this prevents further bound functions from being invoked. (tkinter inline doc)

    def run(self):
        self.thread = threading.Thread(target=self.run_in_thread, daemon=True)
        self.thread.start()


app = App()
app.mainloop()




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
