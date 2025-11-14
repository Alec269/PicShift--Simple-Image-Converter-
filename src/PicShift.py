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
root.title("PicShift")
root.geometry("440x480")
root.iconbitmap("Image_Format_Converter.ico")

# Bind Enter key to convert function
root.bind('<Return>', lambda event: convert_image())

# --- Variables ---
input_file = ttk.StringVar()
output_dir = ttk.StringVar()
output_format = ttk.StringVar(value="ICO")
size_input = ttk.StringVar(value="64")
result_text = ttk.StringVar()

# Supported formats
SUPPORTED_FORMATS = (".png", ".ico", ".jpg", ".jpeg", ".tiff", ".tif", ".icns")

# Enable drag and drop for files
root.drop_target_register(DND_FILES)


def handle_drop(event):
   """
   Handles file drop events.
   Checks if the dropped file is supported and sets it as the input file.
   """
   files = root.tk.splitlist(event.data)
   for file in files:
      if file.lower().endswith(SUPPORTED_FORMATS):
         input_file.set(file)
         result_text.set(f"File dropped: {os.path.basename(file)}")
         break
   else:
      result_text.set("Only PNG, ICO, JPEG, TIFF, or ICNS files are accepted.")


# Bind the drop event to the handler
root.dnd_bind('<<Drop>>', handle_drop)


# --- File + Folder Select Functions ---
def select_input_file():
   """Opens a file dialog to select a supported input file."""
   path = filedialog.askopenfilename(
      filetypes=[("Image files", "*.png *.ico *.jpg *.jpeg *.tiff *.tif *.icns")]
   )
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
   Performs the image conversion between supported formats.
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

   # Get the desired output format
   target_format = output_format.get().upper()

   # Get input file extension
   filename = os.path.splitext(os.path.basename(file_path))[0]
   ext = os.path.splitext(file_path)[1].lower()

   # Determine output extension
   format_extensions = {
      "PNG": ".png",
      "ICO": ".ico",
      "JPEG": ".jpg",
      "TIFF": ".tiff",
      "ICNS": ".icns"
   }
   out_ext = format_extensions.get(target_format, ".png")
   out_path = os.path.join(out_dir, f"{filename}{out_ext}")

   try:
      # Open and convert image
      img = Image.open(file_path).convert("RGBA")

      # Handle multi-size formats (ICO and ICNS)
      if target_format in ["ICO", "ICNS"]:
         size_str = size_input.get().replace(" ", "")
         try:
            # Parse and validate sizes
            sizes = sorted(
               list(
                  {
                     int(s)
                     for s in size_str.split(",")
                     if s.isdigit() and 16 <= int(s) <= 1024
                  }
               )
            )
            if not sizes:
               raise ValueError

            # Check for ICO size limit
            if target_format == "ICO":
               oversized = [s for s in sizes if s > 256]
               if oversized:
                  messagebox.showwarning(
                     "Size Warning",
                     f"ICO format works best with sizes 256px and below.\nSizes over 256: eg. {', '.join(map(str, oversized))}\n\nContinuing anyway, but some applications may not display larger sizes correctly.\nWhich includes Windows Explorer."
                  )
         except ValueError:
            messagebox.showerror(
               "Invalid Sizes",
               f"Please enter comma-separated numeric values for {target_format} sizes (16–1024). Example: 32,64,128",
            )
            return

         # Create resized versions
         icons = [img.resize((s, s), Image.LANCZOS) for s in sizes]

         if target_format == "ICO":
            icons[0].save(
               out_path,
               format="ICO",
               append_images=icons[1:] if len(icons) > 1 else [],
               sizes=[(s, s) for s in sizes]
            )
         elif target_format == "ICNS":
            icons[0].save(
               out_path,
               format="ICNS",
               append_images=icons[1:] if len(icons) > 1 else []
            )

         result_text.set(f"✅ Converted to {target_format}\nSaved: {out_path}")

      # Handle single-image formats
      else:
         # Parse size for single-image formats (use first size value)
         size_str = size_input.get().replace(" ", "")
         try:
            sizes = [int(s) for s in size_str.split(",") if s.isdigit() and 16 <= int(s) <= 2048]
            if sizes:
               target_size = sizes[0]  # Use the first size value
               img = img.resize((target_size, target_size), Image.LANCZOS)
         except ValueError:
            pass  # Keep original size if parsing fails

         if target_format == "JPEG":
            # JPEG doesn't support transparency, convert to RGB
            if img.mode == "RGBA":
               # Create white background
               background = Image.new("RGB", img.size, (255, 255, 255))
               background.paste(img, mask=img.split()[3])  # Use alpha channel as mask
               img = background
            else:
               img = img.convert("RGB")

         # Save in target format
         img.save(out_path, format=target_format)
         result_text.set(f"✅ Converted to {target_format}\nSaved: {out_path}")

      if used_default_dir:
         result_text.set(result_text.get() + "\n(Output saved in source folder.)")

      # Attempt to open the output folder
      try:
         if os.name == 'nt':  # Windows
            subprocess.run(["explorer", os.path.realpath(out_dir)])
         elif os.name == 'posix':  # Linux
            subprocess.run(["xdg-open", os.path.realpath(out_dir)], check=True)
         elif os.uname().sysname == 'Darwin':  # macOS
            subprocess.run(["open", os.path.realpath(out_dir)], check=True)
      except (subprocess.CalledProcessError, FileNotFoundError) as e:
         messagebox.showwarning("Open Folder Error", f"Could not open output folder: {e}")

   except Exception as e:
      messagebox.showerror("Conversion Error", f"An error occurred during conversion: {str(e)}")


# --- UI Layout ---
# Title Label
ttk.Label(root, text="PicShift", font=("Roboto", 16, "bold")).pack(pady=12)

# Buttons for file and directory selection (same width, different colors)
btn_width = 25
ttk.Button(root, text="Select Image File", command=select_input_file, bootstyle=PRIMARY, width=btn_width).pack(pady=4)
ttk.Button(root, text="Select Output Directory", command=select_output_dir, bootstyle=INFO, width=btn_width).pack(
   pady=4)

# Output format selection
ttk.Label(root, text="Convert to:").pack(pady=(12, 4))
format_frame = ttk.Frame(root)
format_frame.pack()
for fmt in ["PNG", "ICO", "JPEG", "TIFF", "ICNS"]:
   ttk.Radiobutton(format_frame, text=fmt, variable=output_format, value=fmt).pack(side=LEFT, padx=5)

# Size input
ttk.Label(root, text="Output Size(s) (e.g. 64 or 32,64,128):").pack(pady=(12, 4))
ttk.Entry(root, textvariable=size_input, width=30).pack()

# Convert button
ttk.Button(root, text="Convert", bootstyle=SUCCESS, width=btn_width, command=convert_image).pack(pady=14)

# Display selected file path
ttk.Label(root, text="Selected File:", font=("Roboto", 9)).pack(anchor="w", padx=12)
ttk.Label(root, textvariable=input_file, wraplength=400, font=("Roboto", 8), foreground="#aaa").pack(anchor="w",
                                                                                                     padx=12)

# Display output directory path
ttk.Label(root, text="Output Directory:", font=("Roboto", 9)).pack(anchor="w", padx=12, pady=(8, 0))
ttk.Label(root, textvariable=output_dir, wraplength=400, font=("Roboto", 8), foreground="#aaa").pack(anchor="w",
                                                                                                     padx=12)

# Display conversion result text
ttk.Label(root, textvariable=result_text, wraplength=400, font=("Roboto", 9), foreground="#4caf50").pack(pady=(10, 0))

# Start the Tkinter event loop
root.mainloop()
