from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                               QLineEdit, QDoubleSpinBox, QSpinBox, QPushButton, 
                               QFormLayout, QMessageBox, QFrame)
from PySide6.QtCore import Qt
from core.utils import read_json, write_json

class SettingsPage(QWidget):
    """
    Page for managing and saving application configurations 
    (API Key, AI Models, Risk-Free Rate, and Broker Connection).
    """
    def __init__(self):
        super().__init__()
        self.setup_ui()
        self.load_settings()

    def setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(20)
        main_layout.setContentsMargins(28, 24, 28, 24)

        # ── HEADER ───────────────────────────────────────────
        header_label = QLabel("System Settings")
        header_label.setObjectName("page_header")
        main_layout.addWidget(header_label)

        # ── FORM LAYOUT ──────────────────────────────────────
        form_layout = QFormLayout()
        form_layout.setSpacing(15)
        form_layout.setLabelAlignment(Qt.AlignRight | Qt.AlignVCenter)

        # --- AI & RISK SETTINGS ---
        ai_section = QLabel("AI & MATH CONFIGURATION")
        ai_section.setObjectName("section_label")
        form_layout.addRow(ai_section)

        self.api_key_input = QLineEdit()
        self.api_key_input.setEchoMode(QLineEdit.Password)
        self.api_key_input.setPlaceholderText("Enter your Google Gemini API Key")
        self.api_key_input.setMinimumWidth(300)

        self.model_input = QLineEdit()
        self.model_input.setPlaceholderText("E.g., gemini-1.5-pro")

        self.risk_free_input = QDoubleSpinBox()
        self.risk_free_input.setRange(-10.0, 20.0)
        self.risk_free_input.setSingleStep(0.1)
        self.risk_free_input.setDecimals(2)
        self.risk_free_input.setSuffix(" %")

        form_layout.addRow(QLabel("Gemini API Key:"), self.api_key_input)
        form_layout.addRow(QLabel("AI Model:"), self.model_input)
        form_layout.addRow(QLabel("Risk-Free Rate:"), self.risk_free_input)

        # --- BROKER SETTINGS ---
        broker_section = QLabel("IBKR CONNECTION SETTINGS")
        broker_section.setObjectName("section_label")
        # Add a little top margin before the next section
        broker_section.setStyleSheet("margin-top: 15px;") 
        form_layout.addRow(broker_section)

        self.ibkr_host_input = QLineEdit()
        self.ibkr_host_input.setPlaceholderText("127.0.0.1")
        
        self.ibkr_port_input = QSpinBox()
        self.ibkr_port_input.setRange(1000, 9999)
        self.ibkr_port_input.setToolTip("TWS Live: 7496 | TWS Paper: 7497\nGateway Live: 4001 | Gateway Paper: 4002")
        
        self.ibkr_client_id_input = QSpinBox()
        self.ibkr_client_id_input.setRange(1, 999)
        self.ibkr_client_id_input.setToolTip("Must be unique if running multiple API apps simultaneously.")

        form_layout.addRow(QLabel("Host (IP):"), self.ibkr_host_input)
        form_layout.addRow(QLabel("Port:"), self.ibkr_port_input)
        form_layout.addRow(QLabel("Client ID:"), self.ibkr_client_id_input)

        main_layout.addLayout(form_layout)

        # ── CONTROLS ─────────────────────────────────────────
        btn_layout = QHBoxLayout()
        self.save_btn = QPushButton("Save Settings")
        self.save_btn.setObjectName("primary_btn")
        self.save_btn.setMinimumHeight(38)
        self.save_btn.clicked.connect(self.save_settings)
        
        btn_layout.addStretch()
        btn_layout.addWidget(self.save_btn)
        
        main_layout.addLayout(btn_layout)
        main_layout.addStretch()

    def load_settings(self):
        """Loads data from config.json and populates the UI fields."""
        config = read_json("config.json")
        if config:
            self.api_key_input.setText(config.get("GEMINI_API_KEY", ""))
            self.model_input.setText(config.get("GEMINI_MODEL", "gemini-1.5-pro"))
            
            rfr = config.get("RISK_FREE_RATE", 0.0)
            self.risk_free_input.setValue(rfr * 100)

            self.ibkr_host_input.setText(config.get("IBKR_HOST", "127.0.0.1"))
            self.ibkr_port_input.setValue(config.get("IBKR_PORT", 4001))
            self.ibkr_client_id_input.setValue(config.get("IBKR_CLIENT_ID", 1))

    def save_settings(self):
        """Gathers data from the UI and saves it to config.json."""
        config = read_json("config.json")
        if not isinstance(config, dict):
            config = {}
            
        config["GEMINI_API_KEY"] = self.api_key_input.text().strip()
        config["GEMINI_MODEL"] = self.model_input.text().strip()
        config["RISK_FREE_RATE"] = round(self.risk_free_input.value() / 100.0, 4)
        
        config["IBKR_HOST"] = self.ibkr_host_input.text().strip()
        config["IBKR_PORT"] = self.ibkr_port_input.value()
        config["IBKR_CLIENT_ID"] = self.ibkr_client_id_input.value()

        if write_json("config.json", config):
            QMessageBox.information(self, "Success", "Settings saved successfully!\nChanges will be applied to future simulations.")
        else:
            QMessageBox.critical(self, "Error", "Could not save the config.json file. Check file permissions.")