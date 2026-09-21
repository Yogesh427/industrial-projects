from __future__ import annotations

import threading
from pathlib import Path
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

import cv2

VIDEO_EXTENSIONS = {".mp4", ".avi", ".mov", ".mkv", ".webm", ".wmv", ".m4v", ".mpeg", ".mpg"}


class VideoExtractorUI:
	def __init__(self, root: tk.Tk) -> None:
		self.root = root
		self.root.title("Bulk Video Frame Extractor")
		self.root.geometry("760x560")
		self.root.minsize(680, 480)
		self.video_dir = tk.StringVar(value=str(Path(__file__).resolve().parent))
		self.output_dir = tk.StringVar(value=str(Path(__file__).resolve().parent / "extracted_images"))
		self.label = tk.StringVar()
		self.duration = tk.DoubleVar(value=5.0)
		self.max_images = tk.IntVar(value=10000)
		self.status = tk.StringVar(value="Choose a folder, then select videos to process.")
		self.progress = tk.DoubleVar(value=0)
		self.video_paths: list[Path] = []
		self.build_ui()
		self.refresh_videos()

	def build_ui(self) -> None:
		root = self.root
		root.columnconfigure(0, weight=1)
		root.rowconfigure(1, weight=1)
		header = ttk.Frame(root, padding=18)
		header.grid(row=0, column=0, sticky="ew")
		ttk.Label(header, text="VIDEO TO IMAGE", font=("Segoe UI", 20, "bold")).pack(anchor="w")
		ttk.Label(header, text="Select videos, give one name, and extract 60 frames per second.", foreground="#227a45").pack(anchor="w")

		content = ttk.Frame(root, padding=(18, 0, 18, 18))
		content.grid(row=1, column=0, sticky="nsew")
		content.columnconfigure(1, weight=1)
		content.rowconfigure(2, weight=1)
		self.folder_row(content, 0, "Video folder", self.video_dir, self.choose_video_dir)
		self.folder_row(content, 1, "Output folder", self.output_dir, self.choose_output_dir)

		frame = ttk.LabelFrame(content, text="Available videos - select one or more", padding=10)
		frame.grid(row=2, column=0, columnspan=3, sticky="nsew", pady=12)
		frame.columnconfigure(0, weight=1)
		frame.rowconfigure(0, weight=1)
		self.video_list = tk.Listbox(frame, selectmode=tk.EXTENDED, exportselection=False)
		self.video_list.grid(row=0, column=0, sticky="nsew")
		scroll = ttk.Scrollbar(frame, orient="vertical", command=self.video_list.yview)
		scroll.grid(row=0, column=1, sticky="ns")
		self.video_list.configure(yscrollcommand=scroll.set)
		ttk.Button(frame, text="Refresh list", command=self.refresh_videos).grid(row=1, column=0, sticky="w", pady=(10, 0))

		options = ttk.LabelFrame(content, text="One name for this batch", padding=10)
		options.grid(row=3, column=0, columnspan=3, sticky="ew", pady=5)
		options.columnconfigure(1, weight=1)
		ttk.Label(options, text="Name after #").grid(row=0, column=0, sticky="w")
		ttk.Entry(options, textvariable=self.label).grid(row=0, column=1, sticky="ew", padx=10)
		ttk.Label(options, text="furina -> #1furina.jpg").grid(row=0, column=2, sticky="e")
		ttk.Label(options, text="Seconds (3-5)").grid(row=1, column=0, sticky="w", pady=(10, 0))
		ttk.Spinbox(options, from_=3, to=5, increment=.5, textvariable=self.duration, width=8).grid(row=1, column=1, sticky="w", padx=10, pady=(10, 0))
		ttk.Label(options, text="Maximum images").grid(row=1, column=2, sticky="e", pady=(10, 0))
		ttk.Spinbox(options, from_=1, to=10000, textvariable=self.max_images, width=8).grid(row=1, column=3, sticky="e", pady=(10, 0))

		actions = ttk.Frame(content)
		actions.grid(row=4, column=0, columnspan=3, sticky="ew", pady=12)
		ttk.Button(actions, text="Extract selected videos", command=self.start_extraction).pack(side="left")
		ttk.Progressbar(actions, variable=self.progress, maximum=100).pack(side="left", fill="x", expand=True, padx=15)
		ttk.Label(content, textvariable=self.status, wraplength=720).grid(row=5, column=0, columnspan=3, sticky="w")

	def folder_row(self, parent, row, label, variable, command) -> None:
		parent.columnconfigure(1, weight=1)
		ttk.Label(parent, text=label).grid(row=row, column=0, sticky="w", pady=7)
		ttk.Entry(parent, textvariable=variable).grid(row=row, column=1, sticky="ew", padx=10, pady=7)
		ttk.Button(parent, text="Browse", command=command).grid(row=row, column=2, pady=7)

	def choose_video_dir(self) -> None:
		selected = filedialog.askdirectory(title="Choose folder containing videos")
		if selected:
			self.video_dir.set(selected)
			self.refresh_videos()

	def choose_output_dir(self) -> None:
		selected = filedialog.askdirectory(title="Choose output folder")
		if selected:
			self.output_dir.set(selected)

	def refresh_videos(self) -> None:
		folder = Path(self.video_dir.get())
		self.video_paths = sorted(path for path in folder.iterdir() if path.is_file() and path.suffix.lower() in VIDEO_EXTENSIONS) if folder.is_dir() else []
		self.video_list.delete(0, tk.END)
		for path in self.video_paths:
			self.video_list.insert(tk.END, path.name)
		self.status.set(f"{len(self.video_paths)} video(s) available. Select the files to extract.")

	def start_extraction(self) -> None:
		selected = [self.video_paths[index] for index in self.video_list.curselection()]
		label = self.label.get().strip()
		if not selected:
			messagebox.showerror("Video extractor", "Select at least one video.")
			return
		if not label or any(character in label for character in '\\/:*?"<>|'):
			messagebox.showerror("Video extractor", "Enter a valid folder name, such as furina.")
			return
		try:
			duration = float(self.duration.get())
			maximum = max(1, min(int(self.max_images.get()), 10000))
		except (ValueError, tk.TclError):
			messagebox.showerror("Video extractor", "Use valid duration and maximum values.")
			return
		if not 3 <= duration <= 5:
			messagebox.showerror("Video extractor", "Duration must be between 3 and 5 seconds.")
			return
		self.status.set("Extracting selected videos...")
		threading.Thread(target=self.extract, args=(selected, label, duration, maximum), daemon=True).start()

	def extract(self, videos: list[Path], label: str, duration: float, maximum: int) -> None:
		output = Path(self.output_dir.get()) / label
		output.mkdir(parents=True, exist_ok=True)
		saved = 0
		try:
			for video in videos:
				capture = cv2.VideoCapture(str(video))
				if not capture.isOpened():
					continue
				fps = capture.get(cv2.CAP_PROP_FPS) or 30.0
				limit = round(fps * duration)
				frame_index = 0
				while saved < maximum and frame_index < limit:
					success, frame = capture.read()
					if not success:
						break
					if round(frame_index * 60 / fps) == frame_index * 60 / fps:
						saved += 1
						cv2.imwrite(str(output / f"#{saved}{label}.jpg"), frame)
						self.update(saved / maximum * 100, f"Created #{saved}{label}.jpg")
					frame_index += 1
				capture.release()
				if saved >= maximum:
					break
			self.update(100, f"Finished: {saved} JPG images saved in {output}")
		except Exception as error:
			self.root.after(0, lambda: messagebox.showerror("Video extractor", str(error)))

	def update(self, value: float, message: str) -> None:
		self.root.after(0, self.progress.set, value)
		self.root.after(0, self.status.set, message)


if __name__ == "__main__":
	app = tk.Tk()
	VideoExtractorUI(app)
	app.mainloop()
