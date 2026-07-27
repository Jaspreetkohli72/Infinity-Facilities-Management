import sys
import os
import json
import shutil
import re
import subprocess
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple

try:
    from PySide6.QtWidgets import (
        QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
        QLabel, QLineEdit, QTextEdit, QComboBox, QPushButton, QFileDialog,
        QListWidget, QListWidgetItem, QProgressBar, QMessageBox, QFrame,
        QScrollArea, QSplitter, QGroupBox, QGridLayout
    )
    from PySide6.QtGui import QIcon, QPixmap, QFont, QColor
    from PySide6.QtCore import Qt, QThread, Signal
    HAS_PYSIDE = True
except ImportError:
    HAS_PYSIDE = False
    import tkinter as tk
    from tkinter import ttk, filedialog, messagebox


# ==========================================
# Data Models & Utilities
# ==========================================

class ProjectData:
    """Dataclass holding project details."""
    def __init__(
        self,
        title: str,
        category: str,
        description: str,
        client: str = "",
        completion_date: str = "",
        location: str = "",
        features: Optional[List[str]] = None,
        cover_image: Optional[str] = None,
        logo_image: Optional[str] = None,
        gallery_images: Optional[List[str]] = None
    ) -> None:
        self.title = title.strip()
        self.category = category.strip()
        self.description = description.strip()
        self.client = client.strip()
        self.completion_date = completion_date.strip()
        self.location = location.strip()
        self.features = features or []
        self.cover_image = cover_image
        self.logo_image = logo_image
        self.gallery_images = gallery_images or []

    @property
    def slug(self) -> str:
        """Generate URL-safe slug from project title."""
        s = self.title.lower()
        s = re.sub(r'[^a-z0-9]+', '-', s)
        return s.strip('-') or "project"


def get_workspace_root() -> Path:
    """Find the root directory containing projects.json or .git."""
    if getattr(sys, 'frozen', False):
        exe_dir = Path(sys.executable).resolve().parent
        for p in [exe_dir, exe_dir.parent, exe_dir.parent.parent]:
            if (p / "projects.json").exists() or (p / ".git").exists():
                return p
        return exe_dir.parent if (exe_dir.parent / "projects.json").exists() else exe_dir

    curr = Path(__file__).resolve().parent
    # Walk up to find .git or projects.json
    for p in [curr, curr.parent, curr.parent.parent]:
        if (p / "projects.json").exists() or (p / ".git").exists():
            return p
    return curr.parent  # default fallback to parent directory


class ProjectManager:
    """Manages loading, validating, and saving projects to projects.json."""
    def __init__(self, workspace_root: Path) -> None:
        self.root = workspace_root
        self.json_path = self.root / "projects.json"

    def load_projects(self) -> List[Dict[str, Any]]:
        if not self.json_path.exists():
            return []
        try:
            with open(self.json_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                if isinstance(data, list):
                    return data
                return []
        except Exception as e:
            print(f"Error reading projects.json: {e}")
            return []

    def validate_project(self, project: ProjectData) -> Tuple[bool, str]:
        if not project.title:
            return False, "Project Name is required."
        if not project.category:
            return False, "Category is required."
        if not project.description:
            return False, "Short Description is required."

        existing = self.load_projects()
        for p in existing:
            if p.get("title", "").strip().lower() == project.title.lower():
                return False, f"A project named '{project.title}' already exists in projects.json."
        
        return True, ""

    def get_next_id(self) -> int:
        projects = self.load_projects()
        max_id = 0
        for p in projects:
            p_id = p.get("id")
            if isinstance(p_id, int) and p_id > max_id:
                max_id = p_id
        return max_id + 1

    def append_project(self, project_dict: Dict[str, Any]) -> None:
        projects = self.load_projects()
        projects.append(project_dict)
        with open(self.json_path, 'w', encoding='utf-8') as f:
            json.dump(projects, f, indent=2, ensure_ascii=False)


class AssetManager:
    """Manages copying images into assets/img/projects/<slug>/."""
    def __init__(self, workspace_root: Path) -> None:
        self.root = workspace_root
        self.projects_img_dir = self.root / "assets" / "img" / "projects"

    def process_assets(
        self,
        project: ProjectData,
        log_callback=None
    ) -> Tuple[Optional[str], Optional[str], List[str]]:
        dest_dir = self.projects_img_dir / project.slug
        dest_dir.mkdir(parents=True, exist_ok=True)

        cover_rel_path: Optional[str] = None
        logo_rel_path: Optional[str] = None
        gallery_rel_paths: List[str] = []

        def notify(msg: str):
            if log_callback:
                log_callback(msg)

        # 1. Cover Image
        if project.cover_image and os.path.exists(project.cover_image):
            ext = Path(project.cover_image).suffix.lower() or ".jpg"
            dest_file = dest_dir / f"cover{ext}"
            notify(f"Copying cover image -> {dest_file.name}")
            shutil.copy2(project.cover_image, dest_file)
            cover_rel_path = f"assets/img/projects/{project.slug}/{dest_file.name}"

        # 2. Logo Image
        if project.logo_image and os.path.exists(project.logo_image):
            ext = Path(project.logo_image).suffix.lower() or ".png"
            dest_file = dest_dir / f"logo{ext}"
            notify(f"Copying logo image -> {dest_file.name}")
            shutil.copy2(project.logo_image, dest_file)
            logo_rel_path = f"assets/img/projects/{project.slug}/{dest_file.name}"

        # 3. Gallery Images
        for idx, g_path in enumerate(project.gallery_images, 1):
            if os.path.exists(g_path):
                ext = Path(g_path).suffix.lower() or ".jpg"
                dest_file = dest_dir / f"gallery-{idx}{ext}"
                notify(f"Copying gallery image {idx} -> {dest_file.name}")
                shutil.copy2(g_path, dest_file)
                gallery_rel_paths.append(f"assets/img/projects/{project.slug}/{dest_file.name}")

        return cover_rel_path, logo_rel_path, gallery_rel_paths


class GitManager:
    """Executes git commands via subprocess."""
    def __init__(self, workspace_root: Path) -> None:
        self.root = workspace_root

    def run_command(self, cmd: List[str], log_callback=None) -> Tuple[bool, str]:
        cmd_str = " ".join(cmd)
        if log_callback:
            log_callback(f"$ {cmd_str}")

        try:
            result = subprocess.run(
                cmd,
                cwd=str(self.root),
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                shell=(os.name == "nt")
            )
            output = result.stdout.strip()
            err = result.stderr.strip()
            combined = f"{output}\n{err}".strip()

            if log_callback and combined:
                log_callback(combined)

            if result.returncode != 0:
                return False, f"Git command failed (exit code {result.returncode}): {err or output}"
            return True, output
        except Exception as e:
            err_msg = f"Failed to execute '{cmd_str}': {str(e)}"
            if log_callback:
                log_callback(err_msg)
            return False, err_msg


# ==========================================
# PySide6 Implementation
# ==========================================

if HAS_PYSIDE:
    class StartupSyncWorker(QThread):
        """Worker thread to pull latest files from Git on app launch or manual sync."""
        log_signal = Signal(str)
        finished_signal = Signal(bool, str)

        def __init__(self, workspace_root: Path) -> None:
            super().__init__()
            self.root = workspace_root
            self.gm = GitManager(self.root)

        def run(self) -> None:
            self.log_signal.emit("[Git Sync] Pulling latest repository updates from remote...")
            ok, msg = self.gm.run_command(["git", "pull"], log_callback=self.log_signal.emit)
            if ok:
                self.finished_signal.emit(True, "Successfully synced with latest remote Git repository.")
            else:
                self.finished_signal.emit(False, f"Git pull notice: {msg}")

    class PublishWorker(QThread):
        """Worker thread for publishing projects without freezing UI."""
        progress_signal = Signal(int, str)
        log_signal = Signal(str)
        finished_signal = Signal(bool, str)

        def __init__(self, workspace_root: Path, project: ProjectData) -> None:
            super().__init__()
            self.root = workspace_root
            self.project = project
            self.pm = ProjectManager(self.root)
            self.am = AssetManager(self.root)
            self.gm = GitManager(self.root)

        def run(self) -> None:
            try:
                # Step 0: Pull latest repository changes before starting publish
                self.progress_signal.emit(5, "Syncing latest repository state (git pull)...")
                self.log_signal.emit("[Publish] Pulling latest repository changes before adding project...")
                self.gm.run_command(["git", "pull"], log_callback=self.log_signal.emit)

                # Step 1: Validation
                self.progress_signal.emit(15, "Validating project information...")
                self.log_signal.emit(f"Starting publish process for '{self.project.title}'...")
                valid, err = self.pm.validate_project(self.project)
                if not valid:
                    self.finished_signal.emit(False, err)
                    return

                # Step 2: Copy Assets
                self.progress_signal.emit(35, "Copying image assets...")
                cover_rel, logo_rel, gallery_rels = self.am.process_assets(
                    self.project,
                    log_callback=lambda m: self.log_signal.emit(f"[Assets] {m}")
                )

                # Step 3: Append to projects.json
                self.progress_signal.emit(55, "Updating projects.json...")
                next_id = self.pm.get_next_id()
                project_entry: Dict[str, Any] = {
                    "id": next_id,
                    "title": self.project.title,
                    "category": self.project.category,
                    "client": self.project.client,
                    "completionDate": self.project.completion_date,
                    "location": self.project.location,
                    "logo": logo_rel or "",
                    "image": cover_rel or "",
                    "gallery": gallery_rels,
                    "description": self.project.description,
                    "features": self.project.features
                }
                self.pm.append_project(project_entry)
                self.log_signal.emit(f"[JSON] Successfully appended project ID {next_id} to projects.json")

                # Step 4: Git Add
                self.progress_signal.emit(70, "Running git add...")
                ok, msg = self.gm.run_command(["git", "add", "."], log_callback=self.log_signal.emit)
                if not ok:
                    self.finished_signal.emit(False, f"Git add failed: {msg}")
                    return

                # Step 5: Git Commit
                self.progress_signal.emit(85, "Running git commit...")
                commit_msg = f"Added {self.project.title}"
                ok, msg = self.gm.run_command(["git", "commit", "-m", commit_msg], log_callback=self.log_signal.emit)
                if not ok and "nothing to commit" not in msg:
                    self.finished_signal.emit(False, f"Git commit failed: {msg}")
                    return

                # Step 6: Git Push
                self.progress_signal.emit(95, "Running git push...")
                ok, msg = self.gm.run_command(["git", "push"], log_callback=self.log_signal.emit)
                if not ok:
                    self.finished_signal.emit(False, f"Git push failed: {msg}")
                    return

                self.progress_signal.emit(100, "Published successfully!")
                self.finished_signal.emit(True, f"Project '{self.project.title}' published and pushed successfully!")

            except Exception as e:
                self.log_signal.emit(f"ERROR: {str(e)}")
                self.finished_signal.emit(False, f"Unexpected error: {str(e)}")


    class PySideAppWindow(QMainWindow):
        def __init__(self, workspace_root: Path) -> None:
            super().__init__()
            self.root = workspace_root
            self.pm = ProjectManager(self.root)
            
            self.cover_path: Optional[str] = None
            self.logo_path: Optional[str] = None
            self.gallery_paths: List[str] = []
            self.worker: Optional[PublishWorker] = None
            self.sync_worker: Optional[StartupSyncWorker] = None

            self.init_ui()
            self.run_git_sync(silent_success=True)

        def init_ui(self) -> None:
            self.setWindowTitle("Infinity Facilities Management - Project Uploader")
            self.resize(1000, 750)

            icon_path = self.root / "assets" / "app_icon.png"
            if icon_path.exists():
                self.setWindowIcon(QIcon(str(icon_path)))

            # Modern Styling QSS
            self.setStyleSheet("""
                QMainWindow {
                    background-color: #0F172A;
                    color: #F8FAFC;
                    font-family: 'Segoe UI', Arial, sans-serif;
                }
                QLabel {
                    color: #E2E8F0;
                    font-size: 13px;
                    font-weight: 500;
                }
                QGroupBox {
                    border: 1px solid #334155;
                    border-radius: 10px;
                    margin-top: 15px;
                    font-weight: bold;
                    color: #38BDF8;
                    padding: 15px;
                    background-color: #1E293B;
                }
                QGroupBox::title {
                    subcontrol-origin: margin;
                    left: 15px;
                    padding: 0 5px;
                }
                QLineEdit, QTextEdit, QComboBox {
                    background-color: #0F172A;
                    border: 1px solid #475569;
                    border-radius: 6px;
                    color: #F8FAFC;
                    padding: 8px;
                    font-size: 13px;
                }
                QLineEdit:focus, QTextEdit:focus, QComboBox:focus {
                    border: 1px solid #38BDF8;
                }
                QPushButton {
                    background-color: #3B82F6;
                    color: white;
                    border: none;
                    border-radius: 6px;
                    padding: 9px 16px;
                    font-weight: 600;
                    font-size: 13px;
                }
                QPushButton:hover {
                    background-color: #2563EB;
                }
                QPushButton:pressed {
                    background-color: #1D4ED8;
                }
                QPushButton#publishBtn {
                    background-color: #10B981;
                    font-size: 15px;
                    padding: 12px 24px;
                    border-radius: 8px;
                }
                QPushButton#publishBtn:hover {
                    background-color: #059669;
                }
                QPushButton#secondaryBtn {
                    background-color: #475569;
                }
                QPushButton#secondaryBtn:hover {
                    background-color: #334155;
                }
                QListWidget {
                    background-color: #0F172A;
                    border: 1px solid #475569;
                    border-radius: 6px;
                    color: #F8FAFC;
                }
                QProgressBar {
                    border: 1px solid #334155;
                    border-radius: 6px;
                    text-align: center;
                    color: white;
                    font-weight: bold;
                    background-color: #0F172A;
                }
                QProgressBar::chunk {
                    background-color: #10B981;
                    border-radius: 5px;
                }
            """)

            central_widget = QWidget()
            self.setCentralWidget(central_widget)
            main_layout = QVBoxLayout(central_widget)
            main_layout.setSpacing(15)
            main_layout.setContentsMargins(20, 20, 20, 20)

            # Header
            header_layout = QHBoxLayout()
            header_title = QLabel("Portfolio Project Uploader")
            header_title.setStyleSheet("font-size: 22px; font-weight: 800; color: #38BDF8;")
            header_sub = QLabel("Infinity Facilities Management")
            header_sub.setStyleSheet("font-size: 13px; color: #94A3B8;")
            
            header_v = QVBoxLayout()
            header_v.addWidget(header_title)
            header_v.addWidget(header_sub)
            header_layout.addLayout(header_v)
            header_layout.addStretch()

            main_layout.addLayout(header_layout)

            # Scroll Area containing Forms
            scroll = QScrollArea()
            scroll.setWidgetResizable(True)
            scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")

            container = QWidget()
            container_layout = QHBoxLayout(container)
            container_layout.setSpacing(20)

            # LEFT COLUMN: Text Fields & Features
            left_col = QVBoxLayout()

            # Basic Info Group
            basic_box = QGroupBox("Project Information")
            basic_grid = QGridLayout(basic_box)
            basic_grid.setSpacing(12)

            basic_grid.addWidget(QLabel("Project Name *"), 0, 0)
            self.title_input = QLineEdit()
            self.title_input.setPlaceholderText("e.g. Maruti Lifestyle")
            basic_grid.addWidget(self.title_input, 0, 1)

            basic_grid.addWidget(QLabel("Category *"), 1, 0)
            self.cat_input = QComboBox()
            self.cat_input.setEditable(True)
            self.cat_input.addItems(["residential", "commercial", "healthcare", "industrial", "hospitality"])
            basic_grid.addWidget(self.cat_input, 1, 1)

            basic_grid.addWidget(QLabel("Short Description *"), 2, 0)
            self.desc_input = QTextEdit()
            self.desc_input.setPlaceholderText("Brief overview of the project...")
            self.desc_input.setMaximumHeight(90)
            basic_grid.addWidget(self.desc_input, 2, 1)

            left_col.addWidget(basic_box)

            # Optional Info Group
            opt_box = QGroupBox("Additional Details (Optional)")
            opt_grid = QGridLayout(opt_box)
            opt_grid.setSpacing(12)

            opt_grid.addWidget(QLabel("Client Name"), 0, 0)
            self.client_input = QLineEdit()
            self.client_input.setPlaceholderText("e.g. Avinash Group")
            opt_grid.addWidget(self.client_input, 0, 1)

            opt_grid.addWidget(QLabel("Completion Date"), 1, 0)
            self.date_input = QLineEdit()
            self.date_input.setPlaceholderText("e.g. 2024 or Q3 2025")
            opt_grid.addWidget(self.date_input, 1, 1)

            opt_grid.addWidget(QLabel("Location"), 2, 0)
            self.loc_input = QLineEdit()
            self.loc_input.setPlaceholderText("e.g. Raipur, C.G.")
            opt_grid.addWidget(self.loc_input, 2, 1)

            left_col.addWidget(opt_box)

            # Features Group
            feat_box = QGroupBox("Key Features")
            feat_v = QVBoxLayout(feat_box)
            
            feat_input_h = QHBoxLayout()
            self.feature_edit = QLineEdit()
            self.feature_edit.setPlaceholderText("Enter a feature (e.g. 24/7 Security)...")
            add_feat_btn = QPushButton("+ Add Feature")
            add_feat_btn.clicked.connect(self.add_feature)
            feat_input_h.addWidget(self.feature_edit)
            feat_input_h.addWidget(add_feat_btn)

            self.features_list = QListWidget()
            self.features_list.setMaximumHeight(100)
            
            rem_feat_btn = QPushButton("Remove Selected Feature")
            rem_feat_btn.setObjectName("secondaryBtn")
            rem_feat_btn.clicked.connect(self.remove_feature)

            feat_v.addLayout(feat_input_h)
            feat_v.addWidget(self.features_list)
            feat_v.addWidget(rem_feat_btn)

            left_col.addWidget(feat_box)
            container_layout.addLayout(left_col, stretch=1)

            # RIGHT COLUMN: Images Upload
            right_col = QVBoxLayout()

            img_box = QGroupBox("Project Images")
            img_v = QVBoxLayout(img_box)
            img_v.setSpacing(15)

            # Cover Image
            cover_h = QHBoxLayout()
            self.cover_btn = QPushButton("Select Cover Image")
            self.cover_btn.clicked.connect(self.select_cover_image)
            self.cover_label = QLabel("No file selected")
            self.cover_label.setStyleSheet("color: #94A3B8; font-size: 12px;")
            cover_h.addWidget(self.cover_btn)
            cover_h.addWidget(self.cover_label, stretch=1)
            img_v.addLayout(cover_h)

            # Logo Image
            logo_h = QHBoxLayout()
            self.logo_btn = QPushButton("Select Logo Image")
            self.logo_btn.clicked.connect(self.select_logo_image)
            self.logo_label = QLabel("No file selected")
            self.logo_label.setStyleSheet("color: #94A3B8; font-size: 12px;")
            logo_h.addWidget(self.logo_btn)
            logo_h.addWidget(self.logo_label, stretch=1)
            img_v.addLayout(logo_h)

            # Gallery Images
            gallery_label = QLabel("Gallery Images (Multiple selection allowed)")
            img_v.addWidget(gallery_label)

            gallery_h = QHBoxLayout()
            self.gallery_btn = QPushButton("+ Add Gallery Images")
            self.gallery_btn.clicked.connect(self.select_gallery_images)
            gallery_h.addWidget(self.gallery_btn)
            img_v.addLayout(gallery_h)

            self.gallery_list = QListWidget()
            self.gallery_list.setMaximumHeight(120)
            img_v.addWidget(self.gallery_list)

            rem_gal_btn = QPushButton("Remove Selected Gallery Image")
            rem_gal_btn.setObjectName("secondaryBtn")
            rem_gal_btn.clicked.connect(self.remove_gallery_image)
            img_v.addWidget(rem_gal_btn)

            right_col.addWidget(img_box)

            # Console Log Output
            log_box = QGroupBox("Publishing Log & Output")
            log_v = QVBoxLayout(log_box)
            self.log_console = QTextEdit()
            self.log_console.setReadOnly(True)
            self.log_console.setStyleSheet("font-family: Consolas, monospace; font-size: 11px; background-color: #090D16; color: #A7F3D0;")
            log_v.addWidget(self.log_console)

            right_col.addWidget(log_box, stretch=1)

            container_layout.addLayout(right_col, stretch=1)

            scroll.setWidget(container)
            main_layout.addWidget(scroll, stretch=1)

            # Bottom Controls & Progress
            bottom_v = QVBoxLayout()
            
            self.progress_bar = QProgressBar()
            self.progress_bar.setValue(0)
            self.progress_bar.setFixedHeight(12)
            self.progress_bar.setTextVisible(False)
            bottom_v.addWidget(self.progress_bar)

            bottom_h = QHBoxLayout()
            self.publish_btn = QPushButton("🚀 Publish Project & Push to Git")
            self.publish_btn.setObjectName("publishBtn")
            self.publish_btn.clicked.connect(self.on_publish_clicked)

            sync_btn = QPushButton("🔄 Pull Latest Git")
            sync_btn.setObjectName("secondaryBtn")
            sync_btn.clicked.connect(lambda: self.run_git_sync(silent_success=False))

            clear_btn = QPushButton("Reset Form")
            clear_btn.setObjectName("secondaryBtn")
            clear_btn.clicked.connect(self.reset_form)

            bottom_h.addWidget(self.publish_btn, stretch=2)
            bottom_h.addWidget(sync_btn, stretch=1)
            bottom_h.addWidget(clear_btn, stretch=1)

            bottom_v.addLayout(bottom_h)
            main_layout.addLayout(bottom_v)

        def run_git_sync(self, silent_success: bool = False) -> None:
            self.log_console.append("[Startup] Checking for remote repository updates...")
            self.sync_worker = StartupSyncWorker(self.root)
            self.sync_worker.log_signal.connect(self.append_log)
            def on_sync_finished(success: bool, msg: str):
                if not success:
                    self.append_log(f"[Git Notice] {msg}")
                elif not silent_success:
                    QMessageBox.information(self, "Git Sync Complete", msg)
            self.sync_worker.finished_signal.connect(on_sync_finished)
            self.sync_worker.start()

        def add_feature(self) -> None:
            txt = self.feature_edit.text().strip()
            if txt:
                self.features_list.addItem(txt)
                self.feature_edit.clear()

        def remove_feature(self) -> None:
            row = self.features_list.currentRow()
            if row >= 0:
                self.features_list.takeItem(row)

        def select_cover_image(self) -> None:
            file_path, _ = QFileDialog.getOpenFileName(
                self, "Select Cover Image", "", "Images (*.png *.jpg *.jpeg *.webp *.svg)"
            )
            if file_path:
                self.cover_path = file_path
                self.cover_label.setText(Path(file_path).name)

        def select_logo_image(self) -> None:
            file_path, _ = QFileDialog.getOpenFileName(
                self, "Select Logo Image", "", "Images (*.png *.jpg *.jpeg *.webp *.svg)"
            )
            if file_path:
                self.logo_path = file_path
                self.logo_label.setText(Path(file_path).name)

        def select_gallery_images(self) -> None:
            file_paths, _ = QFileDialog.getOpenFileNames(
                self, "Select Gallery Images", "", "Images (*.png *.jpg *.jpeg *.webp *.svg)"
            )
            for path in file_paths:
                if path not in self.gallery_paths:
                    self.gallery_paths.append(path)
                    self.gallery_list.addItem(Path(path).name)

        def remove_gallery_image(self) -> None:
            row = self.gallery_list.currentRow()
            if row >= 0:
                self.gallery_list.takeItem(row)
                if row < len(self.gallery_paths):
                    self.gallery_paths.pop(row)

        def reset_form(self) -> None:
            self.title_input.clear()
            self.cat_input.setCurrentIndex(0)
            self.desc_input.clear()
            self.client_input.clear()
            self.date_input.clear()
            self.loc_input.clear()
            self.features_list.clear()
            self.feature_edit.clear()
            self.cover_path = None
            self.cover_label.setText("No file selected")
            self.logo_path = None
            self.logo_label.setText("No file selected")
            self.gallery_paths.clear()
            self.gallery_list.clear()
            self.log_console.clear()
            self.progress_bar.setValue(0)

        def on_publish_clicked(self) -> None:
            title = self.title_input.text()
            cat = self.cat_input.currentText()
            desc = self.desc_input.toPlainText()
            client = self.client_input.text()
            date = self.date_input.text()
            loc = self.loc_input.text()

            features = [
                self.features_list.item(i).text()
                for i in range(self.features_list.count())
            ]

            project = ProjectData(
                title=title,
                category=cat,
                description=desc,
                client=client,
                completion_date=date,
                location=loc,
                features=features,
                cover_image=self.cover_path,
                logo_image=self.logo_path,
                gallery_images=self.gallery_paths
            )

            # Pre-validation check
            valid, err = self.pm.validate_project(project)
            if not valid:
                QMessageBox.warning(self, "Validation Error", err)
                return

            # Disable Publish button during processing
            self.publish_btn.setEnabled(False)
            self.progress_bar.setValue(0)
            self.log_console.clear()

            # Start Worker Thread
            self.worker = PublishWorker(self.root, project)
            self.worker.progress_signal.connect(self.update_progress)
            self.worker.log_signal.connect(self.append_log)
            self.worker.finished_signal.connect(self.on_publish_finished)
            self.worker.start()

        def update_progress(self, val: int, msg: str) -> None:
            self.progress_bar.setValue(val)

        def append_log(self, text: str) -> None:
            self.log_console.append(text)

        def on_publish_finished(self, success: bool, message: str) -> None:
            self.publish_btn.setEnabled(True)
            if success:
                QMessageBox.information(self, "Success", message)
                self.reset_form()
            else:
                QMessageBox.critical(self, "Publish Failed", message)


# ==========================================
# Tkinter Fallback Implementation
# ==========================================

class TkinterAppWindow:
    """Tkinter fallback interface when PySide6 is unavailable."""
    def __init__(self, workspace_root: Path) -> None:
        self.root_path = workspace_root
        self.pm = ProjectManager(self.root_path)
        self.am = AssetManager(self.root_path)
        self.gm = GitManager(self.root_path)

        self.cover_path: Optional[str] = None
        self.logo_path: Optional[str] = None
        self.gallery_paths: List[str] = []

        self.root = tk.Tk()
        self.root.title("Infinity Facilities Management - Project Uploader (Tkinter)")
        self.root.geometry("800x650")
        self.init_ui()

    def init_ui(self) -> None:
        tk.Label(self.root, text="Portfolio Project Uploader", font=("Arial", 16, "bold")).pack(pady=10)

        frame = tk.Frame(self.root)
        frame.pack(fill="both", expand=True, px=15, py=10)

        # Title
        tk.Label(frame, text="Project Name *").grid(row=0, column=0, sticky="w")
        self.title_ent = tk.Entry(frame, width=50)
        self.title_ent.grid(row=0, column=1, pady=5)

        # Category
        tk.Label(frame, text="Category *").grid(row=1, column=0, sticky="w")
        self.cat_ent = ttk.Combobox(frame, values=["residential", "commercial", "healthcare", "industrial"], width=47)
        self.cat_ent.grid(row=1, column=1, pady=5)
        self.cat_ent.current(0)

        # Description
        tk.Label(frame, text="Short Description *").grid(row=2, column=0, sticky="w")
        self.desc_txt = tk.Text(frame, height=4, width=50)
        self.desc_txt.grid(row=2, column=1, pady=5)

        # Cover Image
        tk.Label(frame, text="Cover Image").grid(row=3, column=0, sticky="w")
        self.cover_lbl = tk.Label(frame, text="No file selected", fg="gray")
        self.cover_lbl.grid(row=3, column=1, sticky="w")
        tk.Button(frame, text="Browse", command=self.pick_cover).grid(row=3, column=1, sticky="e")

        # Publish Button
        pub_btn = tk.Button(self.root, text="Publish Project & Push Git", bg="#10B981", fg="white", font=("Arial", 12, "bold"), command=self.publish)
        pub_btn.pack(pady=20)

    def pick_cover(self) -> None:
        p = filedialog.askopenfilename(filetypes=[("Images", "*.png;*.jpg;*.jpeg;*.webp")])
        if p:
            self.cover_path = p
            self.cover_lbl.config(text=Path(p).name, fg="black")

    def publish(self) -> None:
        title = self.title_ent.get().strip()
        cat = self.cat_ent.get().strip()
        desc = self.desc_txt.get("1.0", tk.END).strip()

        project = ProjectData(title=title, category=cat, description=desc, cover_image=self.cover_path)
        valid, err = self.pm.validate_project(project)
        if not valid:
            messagebox.showwarning("Validation Error", err)
            return

        cover_rel, logo_rel, gallery_rels = self.am.process_assets(project)
        next_id = self.pm.get_next_id()
        project_entry = {
            "id": next_id,
            "title": project.title,
            "category": project.category,
            "client": "",
            "completionDate": "",
            "location": "",
            "logo": logo_rel or "",
            "image": cover_rel or "",
            "gallery": gallery_rels,
            "description": project.description,
            "features": []
        }
        self.pm.append_project(project_entry)
        self.gm.run_command(["git", "add", "."])
        self.gm.run_command(["git", "commit", "-m", f"Added {project.title}"])
        ok, msg = self.gm.run_command(["git", "push"])

        if ok:
            messagebox.showinfo("Success", f"Project '{project.title}' published!")
        else:
            messagebox.showerror("Git Push Error", msg)

    def run(self) -> None:
        self.root.mainloop()


# ==========================================
# Main Entry Point
# ==========================================

def main() -> None:
    workspace_root = get_workspace_root()
    print(f"Workspace root detected: {workspace_root}")

    if HAS_PYSIDE:
        app = QApplication(sys.argv)
        window = PySideAppWindow(workspace_root)
        window.show()
        sys.exit(app.exec())
    else:
        print("PySide6 not installed. Falling back to Tkinter...")
        app_tk = TkinterAppWindow(workspace_root)
        app_tk.run()


if __name__ == "__main__":
    main()
