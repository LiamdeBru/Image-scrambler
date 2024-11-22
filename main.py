import tkinter as tk
from tkinter import filedialog, messagebox, simpledialog
from PIL import Image, ImageTk
import random
import hashlib
import requests
from io import BytesIO


def generate_seed(password):
    """Generate a pseudorandom seed from a password."""
    return int(hashlib.sha256(password.encode()).hexdigest(), 16)


def shift_colors(pixels, seed, reverse=False):
    """Shift or reverse color values based on a pseudorandom sequence."""
    random.seed(seed)
    shifted_pixels = []
    for r, g, b in pixels:
        shift_r = random.randint(0, 255)
        shift_g = random.randint(0, 255)
        shift_b = random.randint(0, 255)
        if reverse:
            # Reverse shift
            r = (r - shift_r) % 256
            g = (g - shift_g) % 256
            b = (b - shift_b) % 256
        else:
            # Apply shift
            r = (r + shift_r) % 256
            g = (g + shift_g) % 256
            b = (b + shift_b) % 256
        shifted_pixels.append((r, g, b))
    return shifted_pixels


def shuffle_pixels(image, seed, reverse=False):
    """Shuffle or unshuffle pixels in an image using a pseudorandom sequence."""
    width, height = image.size
    pixels = list(image.getdata())
    total_pixels = len(pixels)

    random.seed(seed)
    indices = list(range(total_pixels))
    random.shuffle(indices)

    if reverse:
        # Create a reverse mapping to restore original order
        reverse_indices = [0] * total_pixels
        for i, shuffled_index in enumerate(indices):
            reverse_indices[shuffled_index] = i
        indices = reverse_indices

    shuffled_pixels = [pixels[i] for i in indices]
    shuffled_image = Image.new(image.mode, (width, height))
    shuffled_image.putdata(shuffled_pixels)
    return shuffled_image


class PixelShufflerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Image Pixel Shuffler and Color Shifter")
        self.image = None
        self.processed_image = None

        self.canvas = tk.Canvas(root, width=500, height=500, bg="gray")
        self.canvas.pack()

        self.controls_frame = tk.Frame(root)
        self.controls_frame.pack()

        self.load_button = tk.Button(self.controls_frame, text="Load Image", command=self.load_image)
        self.load_button.grid(row=0, column=0, padx=5, pady=5)

        self.url_button = tk.Button(self.controls_frame, text="Load from URL", command=self.load_from_url)
        self.url_button.grid(row=0, column=1, padx=5, pady=5)

        self.password_label = tk.Label(self.controls_frame, text="Password:")
        self.password_label.grid(row=0, column=2, padx=5, pady=5)

        self.password_entry = tk.Entry(self.controls_frame, show="*")
        self.password_entry.grid(row=0, column=3, padx=5, pady=5)

        self.encrypt_button = tk.Button(self.controls_frame, text="Encrypt", command=self.encrypt_image)
        self.encrypt_button.grid(row=0, column=4, padx=5, pady=5)

        self.decrypt_button = tk.Button(self.controls_frame, text="Decrypt", command=self.decrypt_image)
        self.decrypt_button.grid(row=0, column=5, padx=5, pady=5)

        self.save_button = tk.Button(self.controls_frame, text="Save", command=self.save_image)
        self.save_button.grid(row=0, column=6, padx=5, pady=5)

        # Checkbox for color shifting option
        self.color_shift_var = tk.BooleanVar(value=True)  # Default is True (enabled)
        self.color_shift_checkbox = tk.Checkbutton(self.controls_frame, text="Enable Color Shifting", variable=self.color_shift_var)
        self.color_shift_checkbox.grid(row=1, column=0, columnspan=2, padx=5, pady=5)

    def load_image(self):
        """Load an image from file."""
        file_path = filedialog.askopenfilename(filetypes=[("Image Files", "*.png *.jpg *.jpeg *.bmp")])
        if file_path:
            self.image = Image.open(file_path).convert("RGB")  # Ensure image is in RGB mode
            self.display_image(self.image)

    def load_from_url(self):
        """Load an image from a URL and cache it locally."""
        url = simpledialog.askstring("Enter URL", "Enter the URL of the image:")
        if not url:
            return

        try:
            response = requests.get(url)
            response.raise_for_status()  # Raise an exception for HTTP errors
            image_data = BytesIO(response.content)
            self.image = Image.open(image_data).convert("RGB")
            self.display_image(self.image)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load image from URL: {e}")

    def display_image(self, image):
        """Display the image on the canvas."""
        self.processed_image = image
        image.thumbnail((500, 500))
        self.tk_image = ImageTk.PhotoImage(image)
        self.canvas.create_image(250, 250, image=self.tk_image, anchor=tk.CENTER)

    def encrypt_image(self):
        """Encrypt the image by optionally shifting colors and shuffling pixels."""
        if self.image is None:
            messagebox.showwarning("Warning", "No image loaded!")
            return

        password = self.password_entry.get()
        if not password:
            messagebox.showwarning("Warning", "Password is required!")
            return

        seed = generate_seed(password)

        if self.color_shift_var.get():  # Check if color shifting is enabled
            pixels = list(self.image.getdata())
            shifted_pixels = shift_colors(pixels, seed)
            self.image.putdata(shifted_pixels)

        encrypted_image = shuffle_pixels(self.image, seed)
        self.display_image(encrypted_image)

    def decrypt_image(self):
        """Decrypt the image by unshuffling pixels and optionally reversing color shifts."""
        if self.image is None:
            messagebox.showwarning("Warning", "No image loaded!")
            return

        password = self.password_entry.get()
        if not password:
            messagebox.showwarning("Warning", "Password is required!")
            return

        seed = generate_seed(password)

        unshuffled_image = shuffle_pixels(self.image, seed, reverse=True)

        if self.color_shift_var.get():  # Check if color shifting is enabled
            pixels = list(unshuffled_image.getdata())
            unshifted_pixels = shift_colors(pixels, seed, reverse=True)
            unshuffled_image.putdata(unshifted_pixels)

        self.display_image(unshuffled_image)

    def save_image(self):
        """Save the processed image."""
        if self.processed_image is None:
            messagebox.showwarning("Warning", "No image to save!")
            return

        file_path = filedialog.asksaveasfilename(defaultextension=".png",
                                                 filetypes=[("PNG files", "*.png"),
                                                            ("JPEG files", "*.jpg"),
                                                            ("All files", "*.*")])
        if file_path:
            self.processed_image.save(file_path)
            messagebox.showinfo("Saved", f"Image saved to {file_path}")


if __name__ == "__main__":
    root = tk.Tk()
    app = PixelShufflerApp(root)
    root.mainloop()
