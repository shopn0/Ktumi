import sys
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout,
    QHBoxLayout, QListWidget, QLineEdit, QStackedWidget,
    QPushButton, QLabel, QSplitter, QFileDialog,
    QFormLayout, QPlainTextEdit
)
from PyQt6.QtCore import Qt

# Database and models
from db.database import init_db, get_all_contacts, add_contact
from models.contact import Contact


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        # Initialize database
        init_db()
        # Uncomment to seed dummy contacts once, then comment out
        # from db.database import add_dummy_contacts
        # add_dummy_contacts()

        # Window settings
        self.setWindowTitle("K TUMI?")
        self.setGeometry(100, 100, 800, 600)

        # Main splitter
        splitter = QSplitter(Qt.Orientation.Horizontal)

        # Left pane: Search + Contact list
        nav_widget = QWidget()
        nav_layout = QVBoxLayout(nav_widget)
        self.search_bar = QLineEdit()
        self.search_bar.setPlaceholderText("Search contacts...")
        self.contact_list = QListWidget()
        nav_layout.addWidget(self.search_bar)
        nav_layout.addWidget(self.contact_list)

        # Load contacts into list
        self.refresh_contact_list()

        # Right pane: Stacked pages
        self.stack = QStackedWidget()
        self.home_page = self._make_label_page("Select a contact or choose an option.")
        self.settings_page = self._make_label_page("Settings")
        self.about_page = self._make_label_page("About K TUMI?")
        self.new_contact_page = self._build_new_contact_form()

        for page in (self.home_page, self.settings_page, self.about_page, self.new_contact_page):
            self.stack.addWidget(page)

        # Bottom toolbar: buttons
        button_layout = QHBoxLayout()
        self.btn_new = QPushButton("New Contact")
        self.btn_settings = QPushButton("Settings")
        self.btn_about = QPushButton("About")
        button_layout.addWidget(self.btn_new)
        button_layout.addWidget(self.btn_settings)
        button_layout.addWidget(self.btn_about)

        # Assemble main layout
        splitter.addWidget(nav_widget)
        splitter.addWidget(self.stack)
        splitter.setSizes([200, 600])

        central = QWidget()
        central_layout = QVBoxLayout(central)
        central_layout.addWidget(splitter)
        central_layout.addLayout(button_layout)
        self.setCentralWidget(central)

        # Connect signals
        self.btn_new.clicked.connect(lambda: self.stack.setCurrentWidget(self.new_contact_page))
        self.btn_settings.clicked.connect(lambda: self.stack.setCurrentWidget(self.settings_page))
        self.btn_about.clicked.connect(lambda: self.stack.setCurrentWidget(self.about_page))
        self.contact_list.itemClicked.connect(self._on_contact_selected)

    def refresh_contact_list(self):
        self.contact_list.clear()
        for contact in get_all_contacts():
            self.contact_list.addItem(f"{contact.name} ({contact.phone})")

    def _make_label_page(self, text):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.addWidget(QLabel(text))
        layout.addStretch()
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

        # Buttons for file selection
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

        # Save button
        self.btn_save = QPushButton("Save Contact")
        form.addRow(self.btn_save)

        # Connect file dialogs and save
        self.in_profile_btn.clicked.connect(self.select_profile_pic)
        self.in_attachments_btn.clicked.connect(self.select_attachments)
        self.btn_save.clicked.connect(self.save_new_contact)

        return page

    def select_profile_pic(self):
        path, _ = QFileDialog.getOpenFileName(self, "Select Profile Picture")
        if path:
            self.profile_pic_path = path

    def select_attachments(self):
        paths, _ = QFileDialog.getOpenFileNames(self, "Select Attachments")
        if paths:
            self.attachment_paths.extend(paths)

    def save_new_contact(self):
        # Validate required fields
        name = self.in_name.text().strip()
        phone = self.in_phone.text().strip()
        if not name or not phone:
            # Could show a message box here
            return

        contact = Contact(
            name=name,
            phone=phone,
            present_address=self.in_present.text().strip(),
            permanent_address=self.in_permanent.text().strip(),
            driver_license=self.in_dl.text().strip(),
            passport_no=self.in_passport.text().strip(),
            nid_no=self.in_nid.text().strip(),
            notes=self.in_notes.toPlainText().strip(),
            profile_pic=self.profile_pic_path,
            attachments=self.attachment_paths
        )

        add_contact(contact)
        self.refresh_contact_list()
        self.stack.setCurrentWidget(self.home_page)

    def _on_contact_selected(self, item):
        # Placeholder: future detail/edit page
        self.stack.setCurrentWidget(self.home_page)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
