import customtkinter as ctk
from tkinter import colorchooser
import threading
import time
import keyboard
import mss
import numpy as np
import win32api
import win32con

def move_mouse(x, y):
    win32api.mouse_event(win32con.MOUSEEVENTF_MOVE, int(x), int(y), 0, 0)

class FovOverlay(ctk.CTkToplevel):
    def __init__(self, master):
        super().__init__(master)
        self.title("FoV Overlay")
        self.overrideredirect(True)
        self.wm_attributes("-topmost", True)
        self.wm_attributes("-disabled", True)
        self.wm_attributes("-transparentcolor", "black")
        self.config(bg='black')

        self.canvas = ctk.CTkCanvas(self, bg="black", highlightthickness=0)
        self.canvas.pack(fill="both", expand=True)

        self.withdraw()

    def update_geometry(self, x, y, size):
        self.geometry(f"{size}x{size}+{x}+{y}")
        self.canvas.delete("all")
        self.canvas.create_rectangle(1, 1, size-1, size-1, outline='red', width=2)

    def show(self):
        self.deiconify()

    def hide(self):
        self.withdraw()


class App(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("Colorblox Basic")
        self.geometry("400x480")
        self.resizable(False, False)
        ctk.set_appearance_mode("Dark")
        ctk.set_default_color_theme("blue")

        self.is_running = False
        self.is_aiming = False
        self.target_color = (255, 0, 255)
        self.fov_size = ctk.IntVar(value=150)
        self.smoothness = ctk.DoubleVar(value=5.0)
        self.aim_key = ctk.StringVar(value="shift")
        self.show_fov = ctk.BooleanVar(value=False)

        self.tabview = ctk.CTkTabview(self, width=360)
        self.tabview.pack(pady=20, padx=20, fill="both", expand=True)
        self.tabview.add("Main Settings")
        self.tabview.add("Color Settings")
        
        tab_main = self.tabview.tab("Main Settings")

        self.toggle_button = ctk.CTkButton(tab_main, text="Start", command=self.toggle_script, height=40, font=("Arial", 16, "bold"))
        self.toggle_button.pack(pady=15, padx=10, fill="x")

        self.fov_label = ctk.CTkLabel(tab_main, text=f"FoV Size: {self.fov_size.get()}x{self.fov_size.get()}")
        self.fov_label.pack(pady=(10, 0))
        self.fov_slider = ctk.CTkSlider(tab_main, from_=50, to=500, variable=self.fov_size, command=self.update_fov_label)
        self.fov_slider.pack(pady=5, padx=10, fill="x")

        self.smooth_label = ctk.CTkLabel(tab_main, text=f"Smoothness: {self.smoothness.get():.1f}")
        self.smooth_label.pack(pady=(10, 0))
        self.smooth_slider = ctk.CTkSlider(tab_main, from_=1.0, to=20.0, variable=self.smoothness, command=self.update_smooth_label)
        self.smooth_slider.pack(pady=5, padx=10, fill="x")

        self.keybind_frame = ctk.CTkFrame(tab_main)
        self.keybind_frame.pack(pady=15, padx=10, fill="x")
        self.keybind_button = ctk.CTkButton(self.keybind_frame, text="Set Aim Key", command=self.set_keybind)
        self.keybind_button.pack(side="left", padx=(0, 10))
        self.keybind_label = ctk.CTkLabel(self.keybind_frame, text=f"Active Key: {self.aim_key.get().upper()}", font=("Arial", 12))
        self.keybind_label.pack(side="left")

        self.fov_checkbox = ctk.CTkCheckBox(tab_main, text="Show FoV", variable=self.show_fov, onvalue=True, offvalue=False, command=self.toggle_fov_visibility)
        self.fov_checkbox.pack(pady=10, padx=10)
        
        tab_color = self.tabview.tab("Color Settings")
        
        color_tab_frame = ctk.CTkFrame(tab_color)
        color_tab_frame.pack(pady=10, padx=10, fill="both", expand=True)

        self.color_preview = ctk.CTkFrame(color_tab_frame, fg_color=f"#{self.target_color[0]:02x}{self.target_color[1]:02x}{self.target_color[2]:02x}", border_width=2)
        self.color_preview.pack(pady=20, padx=20, fill="both", expand=True)

        self.rgb_label = ctk.CTkLabel(color_tab_frame, text=f"RGB: {self.target_color}", font=("Arial", 16))
        self.rgb_label.pack(pady=(0, 15))

        self.color_button = ctk.CTkButton(color_tab_frame, text="Select Target Color", command=self.pick_color, height=35)
        self.color_button.pack(side="bottom", pady=10, padx=10, fill="x")

        self.screen_width = self.winfo_screenwidth()
        self.screen_height = self.winfo_screenheight()
        self.fov_overlay = FovOverlay(self)
        self.toggle_fov_visibility()

        self.aimbot_thread = threading.Thread(target=self.aimbot_loop, daemon=True)
        self.aimbot_thread.start()

        self.key_listener_thread = threading.Thread(target=self.key_listener, daemon=True)
        self.key_listener_thread.start()

    def toggle_script(self):
        self.is_running = not self.is_running
        if self.is_running:
            self.toggle_button.configure(text="Stop", fg_color="red")
            print("Aimbot Active.")
        else:
            self.toggle_button.configure(text="Start", fg_color=ctk.ThemeManager.theme["CTkButton"]["fg_color"])
            self.is_aiming = False
            print("Aimbot Inactive.")
        self.toggle_fov_visibility()

    def pick_color(self):
        color_code = colorchooser.askcolor(title="Select Target Color")
        if color_code[0]:
            self.target_color = tuple(int(c) for c in color_code[0])
            hex_color = color_code[1]
            self.color_preview.configure(fg_color=hex_color)
            self.rgb_label.configure(text=f"RGB: {self.target_color}")
            print(f"New target color: {self.target_color}")

    def update_fov_label(self, value):
        self.fov_label.configure(text=f"FoV Size: {int(value)}x{int(value)}")

    def update_smooth_label(self, value):
        self.smooth_label.configure(text=f"Smoothness: {value:.1f}")

    def set_keybind(self):
        self.keybind_button.configure(text="Press a key...", state="disabled")
        
        def get_key():
            key = keyboard.read_key()
            self.aim_key.set(key)
            self.keybind_label.configure(text=f"Active Key: {key.upper()}")
            self.keybind_button.configure(text="Set Aim Key", state="normal")
            print(f"New aim key: {key}")

        threading.Thread(target=get_key, daemon=True).start()
        
    def toggle_fov_visibility(self):
        if self.is_running and self.show_fov.get():
            self.fov_overlay.show()
        else:
            self.fov_overlay.hide()

    def key_listener(self):
        while True:
            try:
                if self.is_running:
                    if keyboard.is_pressed(self.aim_key.get()):
                        self.is_aiming = True
                    else:
                        self.is_aiming = False
                else:
                    self.is_aiming = False
                time.sleep(0.01)
            except Exception:
                self.is_aiming = False
                time.sleep(0.1)

    def aimbot_loop(self):
        with mss.mss() as sct:
            while True:
                if self.is_running and self.is_aiming:
                    fov = self.fov_size.get()
                    monitor = {
                        "top": (self.screen_height - fov) // 2,
                        "left": (self.screen_width - fov) // 2,
                        "width": fov,
                        "height": fov,
                    }

                    if self.show_fov.get():
                        self.fov_overlay.update_geometry(monitor["left"], monitor["top"], fov)

                    img = sct.grab(monitor)
                    img_np = np.array(img)
                    
                    target_bgr = (self.target_color[2], self.target_color[1], self.target_color[0])
                    indices = np.where(np.all(img_np[:, :, :3] == target_bgr, axis=2))
                    
                    if indices[0].size > 0:
                        center_fov = fov // 2
                        min_dist = float('inf')
                        target_x, target_y = -1, -1

                        check_limit = min(50, indices[0].size)
                        
                        for i in range(check_limit):
                            y, x = indices[0][i], indices[1][i]
                            dist = (x - center_fov)**2 + (y - center_fov)**2
                            if dist < min_dist:
                                min_dist = dist
                                target_x, target_y = x, y

                        if target_x != -1:
                            move_x = (target_x - center_fov) / self.smoothness.get()
                            move_y = (target_y - center_fov) / self.smoothness.get()
                            move_mouse(move_x, move_y)

                time.sleep(0.001)


if __name__ == "__main__":
    app = App()
    app.mainloop()
