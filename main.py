import sys
import os
import sqlite3
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout,
    QHBoxLayout, QListWidget, QLineEdit, QStackedWidget,
    QPushButton, QLabel, QSplitter, QFileDialog,
    QFormLayout, QPlainTextEdit, QListWidgetItem, QMessageBox
)
from PyQt6.QtCore import Qt

from db.database import (
    init_db, get_all_contacts, add_contact, update_contact,
    delete_contact, connect, get_contact_by_id
)
from models.contact import Contact, ContactSummary


def copy_file_to_assets(src_path):
    if not src_path:
        return ""
    dest_dir = "assets"
    os.makedirs(dest_dir, exist_ok=True)
    filename = os.path.basename(src_path)
    dest_path = os.path.join(dest_dir, filename)
    try:
        with open(src_path, 'rb') as fr, open(dest_path, 'wb') as fw:
            fw.write(fr.read())
        return dest_path
    except Exception:
        return src_path


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        init_db()
        os.makedirs('assets', exist_ok=True)

        self.setWindowTitle("K TUMI?")
        self.setGeometry(100, 100, 800, 600)

        splitter = QSplitter(Qt.Orientation.Horizontal)

        # Left pane
        nav_widget = QWidget()
        nav_layout = QVBoxLayout(nav_widget)
        self.search_bar = QLineEdit()
        self.search_bar.setPlaceholderText("Search contacts...")
        self.search_bar.textChanged.connect(self.on_search)
        self.contact_list = QListWidget()
        nav_layout.addWidget(self.search_bar)
        nav_layout.addWidget(self.contact_list)
        splitter.addWidget(nav_widget)

        # Right pane stack
        self.stack = QStackedWidget()
        self.home_page = self._make_label_page("Select a contact or choose an option.")
        self.detail_page = self._build_detail_page()
        self.new_contact_page = self._build_new_contact_form()
        self.settings_page = self._make_label_page("Settings")
        self.about_page = self._make_label_page("About K TUMI?")

        for page in (self.home_page, self.detail_page, self.new_contact_page,
                     self.settings_page, self.about_page):
            self.stack.addWidget(page)
        splitter.addWidget(self.stack)
        splitter.setSizes([200, 600])

        # Bottom toolbar
        button_layout = QHBoxLayout()
        self.btn_new = QPushButton("New Contact")
        self.btn_settings = QPushButton("Settings")
        self.btn_about = QPushButton("About")
        button_layout.addWidget(self.btn_new)
        button_layout.addWidget(self.btn_settings)
        button_layout.addWidget(self.btn_about)

        # Main layout
        central = QWidget()
        central_layout = QVBoxLayout(central)
        central_layout.addWidget(splitter)
        central_layout.addLayout(button_layout)
        self.setCentralWidget(central)

        # Signals
        self.btn_new.clicked.connect(lambda: self.stack.setCurrentWidget(self.new_contact_page))
        self.btn_settings.clicked.connect(lambda: self.stack.setCurrentWidget(self.settings_page))
        self.btn_about.clicked.connect(lambda: self.stack.setCurrentWidget(self.about_page))
        self.contact_list.itemClicked.connect(self._on_contact_selected)

        # Load contacts
        self.refresh_contact_list()

    def on_search(self, text: str):
        self.refresh_contact_list(filter_text=text)

    def refresh_contact_list(self, filter_text: str = ""):
        self.contact_list.clear()
        for contact in get_all_contacts():
            if filter_text.lower() in contact.name.lower() or filter_text.lower() in contact.phone:
                item = QListWidgetItem(f"{contact.name} ({contact.phone})")
                item.setData(Qt.ItemDataRole.UserRole, contact.id)
                self.contact_list.addItem(item)

    def _make_label_page(self, text):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.addWidget(QLabel(text))
        layout.addStretch()
        return page

    def _build_detail_page(self):
        page = QWidget()
        layout = QFormLayout(page)

        # Detail labels
        self.lbl_name = QLabel()
        self.lbl_phone = QLabel()
        self.lbl_present = QLabel()
        self.lbl_permanent = QLabel()
        self.lbl_dl = QLabel()
        self.lbl_passport = QLabel()
        self.lbl_nid = QLabel()
        self.lbl_notes = QPlainTextEdit()
        self.lbl_notes.setReadOnly(True)
        self.lbl_profile_pic = QLabel()
        self.attachments_layout = QVBoxLayout()

        for label, widget in (
            ("Name:", self.lbl_name),
            ("Phone:", self.lbl_phone),
            ("Present Address:", self.lbl_present),
            ("Permanent Address:", self.lbl_permanent),
            ("Driver License No:", self.lbl_dl),
            ("Passport No:", self.lbl_passport),
            ("NID No:", self.lbl_nid),
            ("Notes:", self.lbl_notes),
            ("Profile Picture Path:", self.lbl_profile_pic),
        ):
            layout.addRow(label, widget)
        layout.addRow(QLabel("Attachments:"), QWidget())
        layout.addRow(self._widget_for_layout(self.attachments_layout))

        # Action buttons
        action_layout = QHBoxLayout()
        self.btn_edit = QPushButton("Edit Contact")
        self.btn_delete = QPushButton("Delete Contact")
        action_layout.addWidget(self.btn_edit)
        action_layout.addWidget(self.btn_delete)
        layout.addRow(action_layout)

        # Connect actions
        self.btn_edit.clicked.connect(self.start_edit_contact)
        self.btn_delete.clicked.connect(self.delete_current_contact)

        return page

    def _build_new_contact_form(self):
        page = QWidget()
        form = QFormLayout(page)

        # Input fields
        self.in_name = QLineEdit()
        self.in_phone = QLineEdit()
        self.in_present = QLineEdit()
        self.in_permanent = QLineEdit()
        self.in_dl = QLineEdit()
        self.in_passport = QLineEdit()
        self.in_nid = QLineEdit()
        self.in_notes = QPlainTextEdit()
        self.profile_pic_path = ""
        self.attachment_paths = []

        # File pickers
        self.in_profile_btn = QPushButton("Choose Profile Picture…")
        self.in_attachments_btn = QPushButton("Add Attachments…")

        form.addRow("Name*", self.in_name)
        form.addRow("Phone*", self.in_phone)
        form.addRow("Present Address", self.in_present)
        form.addRow("Permanent Address", self.in_permanent)
        form.addRow("Driver License No", self.in_dl)
        form.addRow("Passport No", self.in_passport)
        form.addRow("NID No", self.in_nid)
        form.addRow("Notes", self.in_notes)
        form.addRow("Profile Picture", self.in_profile_btn)
        form.addRow("Attachments", self.in_attachments_btn)

        self.btn_save = QPushButton("Save Contact")
        form.addRow(self.btn_save)

        self.in_profile_btn.clicked.connect(self.select_profile_pic)
        self.in_attachments_btn.clicked.connect(self.select_attachments)
        self.btn_save.clicked.connect(self.save_new_contact)

        return page

    def _widget_for_layout(self, layout):
        container = QWidget()
        container.setLayout(layout)
        return container

    def select_profile_pic(self):
        path, _ = QFileDialog.getOpenFileName(self, "Select Profile Picture")
        if path:
            self.profile_pic_path = path

    def select_attachments(self):
        paths, _ = QFileDialog.getOpenFileNames(self, "Select Attachments")
        if paths:
            self.attachment_paths.extend(paths)

    def save_new_contact(self):
        name = self.in_name.text().strip()
        phone = self.in_phone.text().strip()
        if not name or not phone:
            QMessageBox.warning(self, "Validation Error", "Name and Phone are required.")
            return
        profile = copy_file_to_assets(self.profile_pic_path)
        attachments = [copy_file_to_assets(p) for p in self.attachment_paths]
        contact = Contact(
            name=name,
            phone=phone,
            present_address=self.in_present.text().strip(),
            permanent_address=self.in_permanent.text().strip(),
            driver_license=self.in_dl.text().strip(),
            passport_no=self.in_passport.text().strip(),
            nid_no=self.in_nid.text().strip(),
            notes=self.in_notes.toPlainText().strip(),
            profile_pic=profile,
            attachments=attachments
        )
        add_contact(contact)
        self.refresh_contact_list()
        self.stack.setCurrentWidget(self.home_page)

    def start_edit_contact(self):
        item = self.contact_list.currentItem()
        if not item:
            return
        cid = item.data(Qt.ItemDataRole.UserRole)
        contact = get_contact_by_id(cid)
        if not contact:
            return
        # Prefill form
        self.in_name.setText(contact.name)
        self.in_phone.setText(contact.phone)
        self.in_present.setText(contact.present_address)
        self.in_permanent.setText(contact.permanent_address)
        self.in_dl.setText(contact.driver_license)
        self.in_passport.setText(contact.passport_no)
        self.in_nid.setText(contact.nid_no)
        self.in_notes.setPlainText(contact.notes)
        self.profile_pic_path = contact.profile_pic
        self.attachment_paths = contact.attachments.copy()

        self.stack.setCurrentWidget(self.new_contact_page)
        # Rewire save for update
        try:
            self.btn_save.clicked.disconnect()
        except Exception:
            pass
        self.btn_save.clicked.connect(lambda: self.finish_edit_contact(cid))

    def finish_edit_contact(self, contact_id: int):
        name = self.in_name.text().strip()
        phone = self.in_phone.text().strip()
        if not name or not phone:
            QMessageBox.warning(self, "Validation Error", "Name and Phone are required.")
            return
        profile = copy_file_to_assets(self.profile_pic_path)
        attachments = [copy_file_to_assets(p) for p in self.attachment_paths]
        contact = Contact(
            name=name,
            phone=phone,
            present_address=self.in_present.text().strip(),
            permanent_address=self.in_permanent.text().strip(),
            driver_license=self.in_dl.text().strip(),
            passport_no=self.in_passport.text().strip(),
            nid_no=self.in_nid.text().strip(),
            notes=self.in_notes.toPlainText().strip(),
            profile_pic=profile,
            attachments=attachments
        )
        update_contact(contact_id, contact)
        self.refresh_contact_list()
        # Restore save handler
        try:
            self.btn_save.clicked.disconnect()
        except Exception:
            pass
        self.btn_save.clicked.connect(self.save_new_contact)
        self.stack.setCurrentWidget(self.home_page)

    def delete_current_contact(self):
        item = self.contact_list.currentItem()
        if not item:
            return
        cid = item.data(Qt.ItemDataRole.UserRole)
        resp = QMessageBox.question(
            self, "Delete Contact",
            "Are you sure you want to delete this contact?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if resp == QMessageBox.StandardButton.Yes:
            delete_contact(cid)
            self.refresh_contact_list()
            self.stack.setCurrentWidget(self.home_page)

    def _on_contact_selected(self, item):
        cid = item.data(Qt.ItemDataRole.UserRole)
        contact = get_contact_by_id(cid)
        if not contact:
            return
        self.lbl_name.setText(contact.name)
        self.lbl_phone.setText(contact.phone)
        self.lbl_present.setText(contact.present_address)
        self.lbl_permanent.setText(contact.permanent_address)
        self.lbl_dl.setText(contact.driver_license)
        self.lbl_passport.setText(contact.passport_no)
        self.lbl_nid.setText(contact.nid_no)
        self.lbl_notes.setPlainText(contact.notes)
        self.lbl_profile_pic.setText(contact.profile_pic)
        for i in reversed(range(self.attachments_layout.count())):
            w = self.attachments_layout.itemAt(i).widget()
            if w:
                w.setParent(None)
        for path in contact.attachments:
            self.attachments_layout.addWidget(QLabel(path))
        self.stack.setCurrentWidget(self.detail_page)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
