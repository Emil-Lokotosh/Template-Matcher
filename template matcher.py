import cv2
import numpy as np
from tkinter import Tk, Canvas, Scrollbar, HORIZONTAL, VERTICAL, NW, Frame, Button
from PIL import Image, ImageTk

# Load images
large_image_path = r"path for image where you search"
template_image_path = r"template path"

large_image = cv2.imread(large_image_path)
template_image = cv2.imread(template_image_path)

# Create flipped versions of the template
templates = [
    template_image,
    cv2.flip(template_image, 0),  # Vertical flip
    cv2.flip(template_image, 1),  # Horizontal flip
    cv2.flip(template_image, -1)  # Both vertical and horizontal flip
]

# Template matching
matches = []

for idx, tmpl in enumerate(templates):
    result = cv2.matchTemplate(large_image, tmpl, cv2.TM_CCOEFF_NORMED)
    threshold = 0.99  # Only consider perfect matches
    locations = np.where(result >= threshold)
    matches.extend(list(zip(*locations[::-1])))

print(f"Found {len(matches)} matches")

# Create GUI
class ImageZoomPan:
    def __init__(self, root, image, matches, template_size):
        self.root = root
        self.image = Image.fromarray(cv2.cvtColor(image, cv2.COLOR_BGR2RGB))
        self.original_image = self.image.copy()
        self.zoom_level = 1.0
        
        # Calculate the initial zoom level
        screen_width = root.winfo_screenwidth()
        screen_height = root.winfo_screenheight()
        
        image_width, image_height = self.original_image.size
        scale_width = screen_width / image_width
        scale_height = screen_height / image_height
        initial_zoom_level = min(scale_width, scale_height)
        
        # Resize the image to fit the screen while maintaining aspect ratio
        new_width = int(image_width * initial_zoom_level)
        new_height = int(image_height * initial_zoom_level)
        self.image = self.original_image.resize((new_width, new_height), Image.Resampling.LANCZOS)
        
        # Create Frame and Scrollbars
        self.frame = Frame(root)
        self.frame.pack(fill="both", expand=True)
        
        self.canvas = Canvas(self.frame)
        self.canvas.pack(side="left", fill="both", expand=True)
        
        self.hbar = Scrollbar(self.frame, orient=HORIZONTAL)
        self.hbar.pack(side="bottom", fill="x")
        self.hbar.config(command=self.canvas.xview)
        
        self.vbar = Scrollbar(self.frame, orient=VERTICAL)
        self.vbar.pack(side="right", fill="y")
        self.vbar.config(command=self.canvas.yview)
        
        self.canvas.config(xscrollcommand=self.hbar.set, yscrollcommand=self.vbar.set)
        self.canvas.config(scrollregion=(0, 0, new_width, new_height))
        
        self.tk_image = ImageTk.PhotoImage(self.image)
        self.image_id = self.canvas.create_image(0, 0, anchor=NW, image=self.tk_image)
        
        self.template_size = template_size
        self.matches = matches
        
        # Draw rectangles and set initial zoom level
        self.draw_rectangles()
        
        # Center the image in the canvas
        self.canvas.configure(scrollregion=(0, 0, new_width, new_height))
        
        self.canvas.bind("<Motion>", self.motion)
        
        # Bind mouse wheel events
        self.canvas.bind("<MouseWheel>", self.zoom_windows)
        self.canvas.bind("<Button-4>", self.zoom_linux)
        self.canvas.bind("<Button-5>", self.zoom_linux)
        
    def draw_rectangles(self):
        self.canvas.delete("rect")
        for top_left in self.matches:
            bottom_right = (top_left[0] + self.template_size[1], top_left[1] + self.template_size[0])
            self.canvas.create_rectangle(top_left[0] * self.zoom_level, top_left[1] * self.zoom_level, 
                                         bottom_right[0] * self.zoom_level, bottom_right[1] * self.zoom_level, 
                                         outline="red", width=2, tag="rect")
            print(f"Match found at: {top_left}")
        
    def motion(self, event):
        x, y = self.canvas.canvasx(event.x), self.canvas.canvasy(event.y)
        print(f"Cursor at: ({int(x / self.zoom_level)}, {int(y / self.zoom_level)})")
        
    def zoom_windows(self, event):
        scale = 1.1 if event.delta > 0 else 0.9
        self.zoom(scale, event.x, event.y)
        
    def zoom_linux(self, event):
        scale = 1.1 if event.num == 4 else 0.9
        self.zoom(scale, event.x, event.y)
        
    def zoom(self, scale, x, y):
        self.zoom_level *= scale
        new_width, new_height = int(self.original_image.width * self.zoom_level), int(self.original_image.height * self.zoom_level)
        self.image = self.original_image.resize((new_width, new_height), Image.Resampling.LANCZOS)
        self.tk_image = ImageTk.PhotoImage(self.image)
        
        # Update image on canvas
        self.canvas.delete(self.image_id)
        self.image_id = self.canvas.create_image(0, 0, anchor=NW, image=self.tk_image)
        
        # Adjust scroll region
        self.canvas.config(scrollregion=(0, 0, new_width, new_height))
        
        # Center zoom on cursor
        self.canvas.scale("all", x, y, scale, scale)
        
        self.draw_rectangles()

root = Tk()
app = ImageZoomPan(root, large_image, matches, template_image.shape)
root.mainloop()
