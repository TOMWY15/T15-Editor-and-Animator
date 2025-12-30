import tkinter as tk
from tkinter import messagebox


class Stroke:
    def __init__(self, points, color, size):
        self.points = points
        self.color = color
        self.size = size


class FrameData:
    def __init__(self):
        self.strokes = []


class T15AnimatorEditor:
    def __init__(self, root):
        self.root = root
        self.root.title("T15 Animator and Editor")

        # Project state
        self.frames = []
        self.current_frame_index = 0
        self.is_playing = False
        self.fps = 6

        # Drawing state
        self.current_tool = "brush"
        self.brush_color = "black"
        self.brush_size = 3
        self.drawing = False
        self.current_points = []
        self.last_x, self.last_y = None, None

        # Selection state
        self.selection_start = None
        self.selection_rect_id = None
        self.is_moving_selection = False
        self.selected_strokes = []
        self.move_last_x = None
        self.move_last_y = None

        # Canvas size
        self.canvas_width = 640
        self.canvas_height = 360

        # Build UI
        self.create_toolbar()
        self.create_main_layout()
        self.create_timeline()
        self.create_bottom_menu_bar()

        # First frame
        self.add_new_frame()
        self.update_ui()

    # ---------------- TOP TOOLBAR ----------------
    def create_toolbar(self):
        toolbar = tk.Frame(self.root, bg="#202020", height=40)
        toolbar.pack(side=tk.TOP, fill=tk.X)

        title_label = tk.Label(
            toolbar,
            text="T15 Animator and Editor",
            fg="white",
            bg="#202020",
            font=("Arial", 12, "bold")
        )
        title_label.pack(side=tk.LEFT, padx=10)

        tk.Label(toolbar, text="  ", bg="#202020").pack(side=tk.LEFT)

        tk.Button(toolbar, text="New", command=self.new_project).pack(side=tk.LEFT, padx=5)
        tk.Button(toolbar, text="Save (WIP)", command=self.not_implemented).pack(side=tk.LEFT, padx=5)
        tk.Button(toolbar, text="Open (WIP)", command=self.not_implemented).pack(side=tk.LEFT, padx=5)

        tk.Label(toolbar, text="   ", bg="#202020").pack(side=tk.LEFT)

        tk.Button(toolbar, text="Play", command=self.play_animation).pack(side=tk.LEFT, padx=5)
        tk.Button(toolbar, text="Stop", command=self.stop_animation).pack(side=tk.LEFT, padx=5)

        tk.Label(toolbar, text="FPS:", fg="white", bg="#202020").pack(side=tk.LEFT, padx=(20, 2))
        self.fps_var = tk.IntVar(value=self.fps)
        tk.Entry(toolbar, textvariable=self.fps_var, width=3).pack(side=tk.LEFT)
        tk.Button(toolbar, text="Set", command=self.set_fps).pack(side=tk.LEFT, padx=2)

    # ---------------- MAIN LAYOUT ----------------
    def create_main_layout(self):
        main_frame = tk.Frame(self.root, bg="#303030")
        main_frame.pack(side=tk.TOP, fill=tk.BOTH, expand=True)

        # Left tools
        left_panel = tk.Frame(main_frame, width=80, bg="#252525")
        left_panel.pack(side=tk.LEFT, fill=tk.Y)

        tk.Label(left_panel, text="Tools", fg="white", bg="#252525").pack(pady=5)

        tk.Button(left_panel, text="Brush", command=lambda: self.set_tool("brush")).pack(fill=tk.X, padx=5, pady=2)
        tk.Button(left_panel, text="Eraser", command=lambda: self.set_tool("eraser")).pack(fill=tk.X, padx=5, pady=2)
        tk.Button(left_panel, text="Fill", command=lambda: self.set_tool("fill")).pack(fill=tk.X, padx=5, pady=2)
        tk.Button(left_panel, text="Select", command=lambda: self.set_tool("select")).pack(fill=tk.X, padx=5, pady=2)

        # Canvas
        center_frame = tk.Frame(main_frame, bg="#404040")
        center_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self.canvas = tk.Canvas(
            center_frame,
            width=self.canvas_width,
            height=self.canvas_height,
            bg="white",
            highlightthickness=0
        )
        self.canvas.pack(expand=True, pady=10)

        self.canvas.bind("<ButtonPress-1>", self.on_canvas_press)
        self.canvas.bind("<B1-Motion>", self.on_canvas_drag)
        self.canvas.bind("<ButtonRelease-1>", self.on_canvas_release)

        # Right properties
        right_panel = tk.Frame(main_frame, width=160, bg="#252525")
        right_panel.pack(side=tk.LEFT, fill=tk.Y)

        tk.Label(right_panel, text="Properties", fg="white", bg="#252525").pack(pady=5)

        tk.Label(right_panel, text="Tool:", fg="white", bg="#252525").pack()
        self.tool_label = tk.Label(right_panel, text="Brush", fg="yellow", bg="#252525")
        self.tool_label.pack()

        tk.Label(right_panel, text="Brush size:", fg="white", bg="#252525").pack(pady=(10, 0))
        self.brush_size_var = tk.IntVar(value=self.brush_size)
        tk.Scale(
            right_panel,
            from_=1,
            to=30,
            orient=tk.HORIZONTAL,
            variable=self.brush_size_var,
            command=self.update_brush_size
        ).pack(padx=5)

        tk.Label(right_panel, text="Onion skin:", fg="white", bg="#252525").pack(pady=(15, 0))
        self.onion_var = tk.BooleanVar(value=True)
        tk.Checkbutton(
            right_panel,
            text="Show previous frame",
            variable=self.onion_var,
            bg="#252525",
            fg="white",
            selectcolor="#404040",
            command=self.refresh_canvas
        ).pack()

    # ---------------- TIMELINE ----------------
    def create_timeline(self):
        timeline_frame = tk.Frame(self.root, bg="#202020", height=90)
        timeline_frame.pack(side=tk.BOTTOM, fill=tk.X)

        self.timeline_container = tk.Frame(timeline_frame, bg="#202020")
        self.timeline_container.pack(side=tk.TOP, fill=tk.X, pady=5)

        controls = tk.Frame(timeline_frame, bg="#202020")
        controls.pack(side=tk.TOP)

        tk.Button(controls, text="+ Frame", command=self.add_new_frame).pack(side=tk.LEFT, padx=5)
        tk.Button(controls, text="Duplicate", command=self.duplicate_frame).pack(side=tk.LEFT, padx=5)
        tk.Button(controls, text="Delete", command=self.delete_frame).pack(side=tk.LEFT, padx=5)

        self.timeline_buttons = []

    def rebuild_timeline_buttons(self):
        for b in self.timeline_buttons:
            b.destroy()
        self.timeline_buttons.clear()

        for i in range(len(self.frames)):
            btn = tk.Button(
                self.timeline_container,
                text=str(i + 1),
                width=3,
                command=lambda idx=i: self.set_current_frame(idx)
            )
            btn.pack(side=tk.LEFT, padx=2)
            self.timeline_buttons.append(btn)

        self.highlight_current_frame_button()

    def highlight_current_frame_button(self):
        for i, btn in enumerate(self.timeline_buttons):
            btn.config(bg="yellow" if i == self.current_frame_index else "SystemButtonFace")

    # ---------------- BOTTOM MENU BAR ----------------
    def create_bottom_menu_bar(self):
        bottom_bar = tk.Frame(self.root, bg="#181818", height=50)
        bottom_bar.pack(side=tk.BOTTOM, fill=tk.X)

        plus_btn = tk.Button(
            bottom_bar,
            text="+",
            font=("Arial", 20, "bold"),
            width=3,
            bg="#303030",
            fg="white",
            command=self.open_edit_menu
        )
        plus_btn.place(relx=0.5, rely=0.5, anchor=tk.CENTER)

    def open_edit_menu(self):
        menu = tk.Toplevel(self.root)
        menu.title("Edit Menu")
        menu.geometry("250x250")
        menu.resizable(False, False)

        tk.Label(menu, text="Edit Tools", font=("Arial", 12, "bold")).pack(pady=10)

        tk.Button(menu, text="Add Frame", width=20, command=self.add_new_frame).pack(pady=5)
        tk.Button(menu, text="Duplicate Frame", width=20, command=self.duplicate_frame).pack(pady=5)
        tk.Button(menu, text="Delete Frame", width=20, command=self.delete_frame).pack(pady=5)
        tk.Button(menu, text="Clear Selection", width=20, command=self.clear_selection).pack(pady=5)
        tk.Button(menu, text="Close", width=20, command=menu.destroy).pack(pady=10)

    # ---------------- FRAME MANAGEMENT ----------------
    def new_project(self):
        if not messagebox.askyesno("New Project", "Start a new project?"):
            return
        self.frames.clear()
        self.current_frame_index = 0
        self.add_new_frame()
        self.update_ui()

    def add_new_frame(self):
        self.frames.append(FrameData())
        self.current_frame_index = len(self.frames) - 1
        self.update_ui()

    def duplicate_frame(self):
        current = self.frames[self.current_frame_index]
        new_frame = FrameData()
        for s in current.strokes:
            new_frame.strokes.append(Stroke(list(s.points), s.color, s.size))
        self.frames.insert(self.current_frame_index + 1, new_frame)
        self.current_frame_index += 1
        self.update_ui()

    def delete_frame(self):
        if len(self.frames) <= 1:
            messagebox.showinfo("Not allowed", "At least one frame must exist.")
            return
        del self.frames[self.current_frame_index]
        self.current_frame_index = max(0, self.current_frame_index - 1)
        self.update_ui()

    def set_current_frame(self, index):
        self.current_frame_index = index
        self.update_ui()

    # ---------------- TOOLS ----------------
    def set_tool(self, tool):
        self.current_tool = tool
        self.tool_label.config(text=tool.capitalize())
        self.clear_selection()
        self.refresh_canvas()

    def update_brush_size(self, value):
        self.brush_size = int(value)

    # ---------------- CANVAS EVENTS ----------------
    def on_canvas_press(self, event):
        x, y = event.x, event.y

        if self.current_tool in ("brush", "eraser"):
            self.drawing = True
            self.current_points = [(x, y)]
            self.last_x, self.last_y = x, y

        elif self.current_tool == "fill":
            self.apply_fill(x, y)

        elif self.current_tool == "select":
            self.selection_start = (x, y)
            if self.selection_rect_id:
                self.canvas.delete(self.selection_rect_id)
            self.selection_rect_id = self.canvas.create_rectangle(
                x, y, x, y, outline="cyan", dash=(3, 3)
            )

        if self.current_tool == "select" and self.selected_strokes:
            self.is_moving_selection = True
            self.move_last_x = x
            self.move_last_y = y

    def on_canvas_drag(self, event):
        x, y = event.x, event.y

        if self.current_tool in ("brush", "eraser") and self.drawing:
            color = self.brush_color if self.current_tool == "brush" else "white"
            size = self.brush_size if self.current_tool == "brush" else self.brush_size + 4

            self.canvas.create_line(
                self.last_x, self.last_y, x, y,
                fill=color, width=size, capstyle=tk.ROUND, smooth=True
            )
            self.current_points.append((x, y))
            self.last_x, self.last_y = x, y

        elif self.current_tool == "select":
            if self.selection_start and self.selection_rect_id and not self.is_moving_selection:
                x0, y0 = self.selection_start
                self.canvas.coords(self.selection_rect_id, x0, y0, x, y)

            if self.is_moving_selection and self.selected_strokes:
                dx = x - self.move_last_x
                dy = y - self.move_last_y
                for s in self.selected_strokes:
                    s.points = [(px + dx, py + dy) for (px, py) in s.points]
                self.move_last_x = x
                self.move_last_y = y
                self.refresh_canvas()

    def on_canvas_release(self, event):
        if self.current_tool in ("brush", "eraser") and self.drawing:
            self.drawing = False
            if len(self.current_points) > 1:
                color = self.brush_color if self.current_tool == "brush" else "white"
                size = self.brush_size if self.current_tool == "brush" else self.brush_size + 4
                self.frames[self.current_frame_index].strokes.append(
                    Stroke(self.current_points, color, size)
                )
            self.current_points = []

        elif self.current_tool == "select":
            if self.selection_rect_id and self.selection_start and not self.is_moving_selection:
                x0, y0 = self.selection_start
                x1, y1 = event.x, event.y
                x_min, x_max = sorted((x0, x1))
                y_min, y_max = sorted((y0, y1))

                self.selected_strokes = []
                for s in self.frames[self.current_frame_index].strokes:
                    for (px, py) in s.points:
                        if x_min <= px <= x_max and y_min <= py <= y_max:
                            self.selected_strokes.append(s)
                            break

                self.refresh_canvas(selection_rect=(x_min, y_min, x_max, y_max))

            self.is_moving_selection = False

    # ---------------- FILL TOOL ----------------
    def apply_fill(self, x, y):
        size = max(40, self.brush_size * 5)
        color = self.brush_color
        points = []

        for px in range(x - size, x + size, 4):
            for py in range(y - size, y + size, 4):
                if (px - x) ** 2 + (py - y) ** 2 <= size ** 2:
                    points.append((px, py))

        if points:
            self.frames[self.current_frame_index].strokes.append(Stroke(points, color, 6))
            self.refresh_canvas()

    # ---------------- SELECTION ----------------
    def clear_selection(self):
        self.selected_strokes = []
        if self.selection_rect_id:
            self.canvas.delete(self.selection_rect_id)
            self.selection_rect_id = None
        self.selection_start = None
        self.is_moving_selection = False

    # ---------------- RENDERING ----------------
    def refresh_canvas(self, selection_rect=None):
        self.canvas.delete("all")

        if self.onion_var.get() and self.current_frame_index > 0:
            self.draw_frame(self.frames[self.current_frame_index - 1], ghost=True)

        self.draw_frame(self.frames[self.current_frame_index], ghost=False)

        if selection_rect:
            x0, y0, x1, y1 = selection_rect
            self.selection_rect_id = self.canvas.create_rectangle(
                x0, y0, x1, y1, outline="cyan", dash=(3, 3)
            )

    def draw_frame(self, frame, ghost=False):
        for s in frame.strokes:
            if len(s.points) < 2:
                continue

            color = "#d0d0d0" if ghost else s.color
            if s in self.selected_strokes and not ghost:
                color = "cyan"

            for i in range(len(s.points) - 1):
                x1, y1 = s.points[i]
                x2, y2 = s.points[i + 1]
                self.canvas.create_line(
                    x1, y1, x2, y2,
                    fill=color,
                    width=s.size,
                    capstyle=tk.ROUND,
                    smooth=True
                )

    # ---------------- ANIMATION ----------------
    def play_animation(self):
        if not self.is_playing:
            self.is_playing = True
            self.play_loop()

    def play_loop(self):
        if not self.is_playing:
            return
        self.current_frame_index = (self.current_frame_index + 1) % len(self.frames)
        self.update_ui()
        self.root.after(int(1000 / self.fps), self.play_loop)

    def stop_animation(self):
        self.is_playing = False

    # ---------------- MISC ----------------
    def set_fps(self):
        try:
            val = int(self.fps_var.get())
            if val <= 0:
                raise ValueError
            self.fps = val
        except:
            messagebox.showerror("Error", "FPS must be a positive integer.")
            self.fps_var.set(self.fps)

    def update_ui(self):
        self.rebuild_timeline_buttons()
        self.refresh_canvas()

    def not_implemented(self):
        messagebox.showinfo("WIP", "This feature is not implemented yet.")


# ---------------- MAIN ----------------
if __name__ == "__main__":
    root = tk.Tk()
    app = T15AnimatorEditor(root)
    root.mainloop()
