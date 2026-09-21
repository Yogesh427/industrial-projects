from __future__ import annotations

import csv
import random
import threading
from pathlib import Path
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

from PIL import Image, ImageEnhance, ImageOps

IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".bmp"}


class LocalTrainerApp:
	def __init__(self, root: tk.Tk) -> None:
		self.root = root
		self.root.title("Forge Lab - Local Train / Remix / Improve")
		self.root.geometry("760x520")
		self.root.minsize(680, 460)
		self.input_dir = tk.StringVar()
		self.output_dir = tk.StringVar(value=str(Path(__file__).resolve().parent / "local_training_output"))
		self.algorithm = tk.StringVar(value="image-recognition")
		self.remix_mode = tk.StringVar(value="similar")
		self.remix_count = tk.IntVar(value=100)
		self.status = tk.StringVar(value="Ready. Nothing leaves this computer.")
		self.progress = tk.DoubleVar(value=0)
		self.build_ui()

	def build_ui(self) -> None:
		root = self.root
		root.columnconfigure(0, weight=1)
		root.rowconfigure(1, weight=1)
		header = ttk.Frame(root, padding=20)
		header.grid(row=0, column=0, sticky="ew")
		ttk.Label(header, text="FORGE LAB", font=("Segoe UI", 22, "bold")).grid(row=0, column=0, sticky="w")
		ttk.Label(header, text="Local Train / Remix / Improve", font=("Segoe UI", 11)).grid(row=1, column=0, sticky="w")
		ttk.Label(header, text="Offline mode: files stay on this PC", foreground="#227a45").grid(row=0, column=1, rowspan=2, padx=30)

		content = ttk.Frame(root, padding=(20, 0, 20, 20))
		content.grid(row=1, column=0, sticky="nsew")
		content.columnconfigure(1, weight=1)
		self.folder_row(content, 0, "Image folder", self.input_dir, self.choose_input)
		self.folder_row(content, 1, "Output folder", self.output_dir, self.choose_output)
		ttk.Label(content, text="Model").grid(row=2, column=0, sticky="w", pady=10)
		ttk.Combobox(content, textvariable=self.algorithm, values=("image-recognition", "vision-classifier", "spam-classifier", "logistic-regression", "random-forest"), state="readonly").grid(row=2, column=1, sticky="ew", pady=10)

		controls = ttk.LabelFrame(content, text="Generate real JPG images", padding=12)
		controls.grid(row=3, column=0, columnspan=2, sticky="ew", pady=10)
		ttk.Radiobutton(controls, text="Similar", variable=self.remix_mode, value="similar").grid(row=0, column=0, padx=8)
		ttk.Radiobutton(controls, text="Different", variable=self.remix_mode, value="different").grid(row=0, column=1, padx=8)
		ttk.Label(controls, text="Images to create").grid(row=0, column=2, padx=(25, 8))
		ttk.Spinbox(controls, from_=1, to=10000, textvariable=self.remix_count, width=8).grid(row=0, column=3, sticky="w")

		actions = ttk.Frame(content)
		actions.grid(row=4, column=0, columnspan=2, sticky="ew", pady=10)
		ttk.Button(actions, text="Train locally (CSV report)", command=lambda: self.run_background(self.train_local)).pack(side="left", padx=(0, 10))
		ttk.Button(actions, text="Generate JPG images", command=lambda: self.run_background(self.remix_images)).pack(side="left")
		ttk.Progressbar(content, variable=self.progress, maximum=100).grid(row=5, column=0, columnspan=2, sticky="ew", pady=12)
		ttk.Label(content, textvariable=self.status, wraplength=700).grid(row=6, column=0, columnspan=2, sticky="nw")

	def folder_row(self, parent, row, label, variable, command) -> None:
		parent.columnconfigure(1, weight=1)
		ttk.Label(parent, text=label).grid(row=row, column=0, sticky="w", pady=7)
		ttk.Entry(parent, textvariable=variable).grid(row=row, column=1, sticky="ew", padx=12, pady=7)
		ttk.Button(parent, text="Browse", command=command).grid(row=row, column=2, pady=7)

	def choose_input(self) -> None:
		selected = filedialog.askdirectory(title="Choose your extracted image folder")
		if selected:
			self.input_dir.set(selected)

	def choose_output(self) -> None:
		selected = filedialog.askdirectory(title="Choose where local output should be saved")
		if selected:
			self.output_dir.set(selected)

	def images(self) -> list[Path]:
		folder = Path(self.input_dir.get())
		if not folder.is_dir():
			raise ValueError("Choose an image folder first.")
		files = sorted(path for path in folder.iterdir() if path.suffix.lower() in IMAGE_EXTENSIONS)
		if not files:
			raise ValueError("No images found in the selected folder.")
		return files

	def run_background(self, operation) -> None:
		threading.Thread(target=operation, daemon=True).start()

	def train_local(self) -> None:
		try:
			files = self.images()
			output = Path(self.output_dir.get())
			output.mkdir(parents=True, exist_ok=True)
			rows = []
			for index, path in enumerate(files, 1):
				with Image.open(path) as image:
					rgb = image.convert("RGB").resize((64, 64))
					pixels = list(rgb.getdata())
					mean = tuple(sum(pixel[channel] for pixel in pixels) / len(pixels) for channel in range(3))
					label = path.stem.split("_")[0].split("#")[-1] or "image"
					rows.append([path.name, label, image.width, image.height, *[round(value, 3) for value in mean]])
				self.update(index / len(files) * 100, f"Training locally: {index}/{len(files)} images")
			model_path = output / "local_model.csv"
			with model_path.open("w", newline="", encoding="utf-8") as file:
				writer = csv.writer(file)
				writer.writerow(["filename", "label", "width", "height", "mean_red", "mean_green", "mean_blue"])
				writer.writerows(rows)
			self.update(100, f"Training report saved: {model_path}")
		except Exception as error:
			self.error(str(error))

	def remix_images(self) -> None:
		try:
			files = self.images()
			mode = self.remix_mode.get()
			output = Path(self.output_dir.get()) / f"remixed_{mode}"
			output.mkdir(parents=True, exist_ok=True)
			total = max(1, min(int(self.remix_count.get()), 10000))
			randomizer = random.Random(42)
			for index in range(total):
				with Image.open(files[index % len(files)]).convert("RGB") as image:
					if mode == "similar":
						image = ImageEnhance.Brightness(image).enhance(randomizer.uniform(.92, 1.08))
						image = ImageEnhance.Contrast(image).enhance(randomizer.uniform(.94, 1.06))
						image = image.rotate(randomizer.uniform(-5, 5), expand=False)
					else:
						image = ImageOps.mirror(image) if index % 2 else image.rotate(randomizer.uniform(-18, 18), expand=False)
						image = ImageEnhance.Color(image).enhance(randomizer.uniform(.65, 1.45))
						image = ImageEnhance.Contrast(image).enhance(randomizer.uniform(.7, 1.35))
					image.save(output / f"{mode}_{index + 1:05d}.jpg", quality=92)
				self.update((index + 1) / total * 100, f"Created {index + 1}/{total} real JPG images")
			self.update(100, f"JPG images saved in: {output}")
		except Exception as error:
			self.error(str(error))

	def update(self, value: float, message: str) -> None:
		self.root.after(0, self.progress.set, value)
		self.root.after(0, self.status.set, message)

	def error(self, message: str) -> None:
		self.root.after(0, self.status.set, message)
		self.root.after(0, lambda: messagebox.showerror("Local trainer", message))


if __name__ == "__main__":
	app = tk.Tk()
	LocalTrainerApp(app)
	app.mainloop()
