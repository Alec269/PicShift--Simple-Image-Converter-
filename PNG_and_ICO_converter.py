import os
import subprocess
from PIL import Image
import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from tkinter import filedialog, messagebox
from tkinterdnd2 import TkinterDnD, DND_FILES



# --- Window ---
class ThemedDnDWindow(TkinterDnD.Tk):
   def __init__(self, theme="darkly", *args, **kwargs):
      super().__init__(*args, **kwargs)

      self.style = ttk.Style(theme)
      self.style.master = self

   # Create the main window instance
root = ThemedDnDWindow(theme="darkly")
root.title("PNG ⇄ ICO Converter")
root.geometry("440x450")
#root.iconbitmap("ico_tonfrom_png-convert.ico") 
# root.resizable(False, False)

# --- Variables ---
input_file = ttk.StringVar()
output_dir = ttk.StringVar()
size_input = ttk.StringVar(value="64")
result_text = ttk.StringVar()

# Enable drag and drop for files
root.drop_target_register(DND_FILES)

def handle_drop(event):
   """
   Handles file drop events.
   Checks if the dropped file is a PNG or ICO and sets it as the input file.
   """
   files = root.tk.splitlist(event.data)
   for file in files:
      if file.lower().endswith((".png", ".ico")):
         input_file.set(file)
         result_text.set(f"File dropped: {os.path.basename(file)}")
         break
   else:
      result_text.set("Only .png or .ico files are accepted.")


# Bind the drop event to the handler
root.dnd_bind('<<Drop>>', handle_drop)

# --- File + Folder Select Functions ---
def select_input_file():
   """Opens a file dialog to select a PNG or ICO input file."""
   path = filedialog.askopenfilename(filetypes=[("Image files", "*.png *.ico")])
   if path:
      input_file.set(path)
      result_text.set(f"Selected: {os.path.basename(path)}")

def select_output_dir():
   """Opens a directory dialog to select the output folder."""
   path = filedialog.askdirectory()
   if path:
      output_dir.set(path)
      result_text.set(f"Output set to: {os.path.basename(path)}")


# --- Convert Function ---
def convert_image():
   """
   Performs the image conversion from PNG to ICO or ICO to PNG.
   Handles file validation, size parsing, and saving.
   """
   file_path = input_file.get()
   if not file_path:
      messagebox.showwarning("Missing File", "Please select a file to convert.")
      return

   used_default_dir = False
   out_dir = output_dir.get()
   # If no output directory is specified, use the source file's directory
   if not out_dir:
      out_dir = os.path.dirname(file_path)
      used_default_dir = True

   size_str = size_input.get().replace(" ", "")
   try:
      # Parse and validate ICO sizes
      sizes = sorted(
         list(
            {
               int(s)
               for s in size_str.split(",")
               if s.isdigit() and 16 <= int(s) <= 256 # Ensure sizes are within valid range
            }
         )
      )
      if not sizes: # If no valid sizes were parsed
         raise ValueError
   except ValueError:
      messagebox.showerror(
         "Invalid Sizes",
         "Please enter comma-separated numeric values for ICO sizes (16–256 only). Example: 32,64,128",
      )
      return

   # Determine output filename and path
   filename = os.path.splitext(os.path.basename(file_path))[0]
   ext = os.path.splitext(file_path)[1].lower()
   out_path = os.path.join(
      out_dir, f"{filename}.ico" if ext == ".png" else f"{filename}.png"
   )

   try:
      # Open and convert image
      img = Image.open(file_path).convert("RGBA") # Convert to RGBA for proper transparency handling

      if ext == ".png":
         # Resize PNG for multiple ICO sizes and save
         icons = [img.resize((s, s), Image.LANCZOS) for s in sizes]
         icons[0].save(out_path, format="ICO", append_images=icons[1:] if len(icons) > 1 else [], sizes=[(s, s) for s in sizes])
         result_text.set(f"✅ PNG ➜ ICO\nSaved: {out_path}")
      elif ext == ".ico":
         # Convert ICO to PNG
         img.save(out_path, format="PNG")
         result_text.set(f"✅ ICO ➜ PNG\nSaved: {out_path}")
      else:
         messagebox.showerror("Unsupported File Type", "Only PNG and ICO files are supported for conversion.")
         return

      if used_default_dir:
         result_text.set(result_text.get() + "\n(Output saved in source folder.)")

      # Attempt to open the output folder
      try:
         # Cross-platform way to open a directory
         if os.name == 'nt':  # Windows
            # Removed check=True for Windows explorer as it can return non-zero even on success
            subprocess.run(["explorer", os.path.realpath(out_dir)])
         elif os.name == 'posix': # macOS or Linux
            subprocess.run(["xdg-open", os.path.realpath(out_dir)], check=True) # Linux
         elif os.uname().sysname == 'Darwin': # macOS
            subprocess.run(["open", os.path.realpath(out_dir)], check=True) # macOS
      except (subprocess.CalledProcessError, FileNotFoundError) as e:
         messagebox.showwarning("Open Folder Error", f"Could not open output folder: {e}")

   except Exception as e:
      messagebox.showerror("Conversion Error", f"An error occurred during conversion: {str(e)}")

# --- UI Layout ---
# Title Label
ttk.Label(root, text="PNG ⇄ ICO Converter", font=("Roboto", 16, "bold")).pack(pady=12)

# Buttons for file and directory selection
ttk.Button(root, text="Select PNG or ICO File", command=select_input_file, bootstyle=PRIMARY).pack(pady=4)
ttk.Button(root, text="Select Output Directory", command=select_output_dir, bootstyle=INFO).pack(pady=4)

# ICO Size input
ttk.Label(root, text="ICO Size(s) (e.g. 32,64,128):").pack(pady=(12, 4))
ttk.Entry(root, textvariable=size_input, width=30).pack()

# Convert button
ttk.Button(root, text="Convert", bootstyle=SUCCESS, command=convert_image).pack(pady=14)

# Display selected file path
ttk.Label(root, text="Selected File:", font=("Roboto", 9)).pack(anchor="w", padx=12)
ttk.Label(root, textvariable=input_file, wraplength=400, font=("Roboto", 8), foreground="#aaa").pack(anchor="w", padx=12)

# Display output directory path
ttk.Label(root, text="Output Directory:", font=("Roboto", 9)).pack(anchor="w", padx=12, pady=(8, 0))
ttk.Label(root, textvariable=output_dir, wraplength=400, font=("Roboto", 8), foreground="#aaa").pack(anchor="w", padx=12)

# Display conversion result text
ttk.Label(root, textvariable=result_text, wraplength=400, font=("Roboto", 9), foreground="#4caf50").pack(pady=(10, 0))

# Start the Tkinter event loop
root.mainloop()
