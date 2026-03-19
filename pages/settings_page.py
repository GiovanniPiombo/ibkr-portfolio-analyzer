from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QDoubleSpinBox, QSpinBox, QPushButton, QFormLayout, QMessageBox, QComboBox
from PySide6.QtCore import Qt
from core.utils import read_json, write_json

class SettingsPage(QWidget):
    """The SettingsPage provides a user interface for configuring application settings, including Gemini API credentials, Monte Carlo defaults, and IBKR connection parameters. It allows users to input and save their preferences, which are stored in the config.json file. The page is structured with clear sections for different categories of settings and includes validation and feedback mechanisms for saving changes."""
    def __init__(self):
        super().__init__()
        self.setup_ui()
        self.load_settings()

    def setup_ui(self):
        """Sets up the user interface components of the SettingsPage, including input fields for Gemini API configuration, Monte Carlo defaults, and IBKR connection settings. The layout is organized with headers and a form layout for better readability."""
        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(20)
        main_layout.setContentsMargins(28, 24, 28, 24)

        header_label = QLabel("System Settings")
        header_label.setObjectName("page_header")
        main_layout.addWidget(header_label)

        form_layout = QFormLayout()
        form_layout.setSpacing(15)
        form_layout.setLabelAlignment(Qt.AlignRight | Qt.AlignVCenter)

        # --- AI & MATH CONFIGURATION ---
        ai_section = QLabel("AI & MATH CONFIGURATION")
        ai_section.setObjectName("section_label")
        form_layout.addRow(ai_section)

        self.api_key_input = QLineEdit()
        self.api_key_input.setEchoMode(QLineEdit.Password)
        self.api_key_input.setMinimumWidth(300)

        self.model_input = QLineEdit()
        
        self.language_input = QComboBox()
        self.language_input.addItems(["English", "Italiano", "Español", "Français", "Deutsch"])

        self.risk_free_input = QDoubleSpinBox()
        self.risk_free_input.setRange(-10.0, 20.0)
        self.risk_free_input.setSingleStep(0.1)
        self.risk_free_input.setSuffix(" %")

        form_layout.addRow(QLabel("Gemini API Key:"), self.api_key_input)
        form_layout.addRow(QLabel("AI Model:"), self.model_input)
        form_layout.addRow(QLabel("AI Output Language:"), self.language_input)
        form_layout.addRow(QLabel("Risk-Free Rate:"), self.risk_free_input)

        # --- MONTE CARLO DEFAULTS ---
        mc_section = QLabel("MONTE CARLO DEFAULTS")
        mc_section.setObjectName("section_label")
        mc_section.setStyleSheet("margin-top: 10px;")
        form_layout.addRow(mc_section)

        self.mc_years_input = QSpinBox()
        self.mc_years_input.setRange(1, 30)
        
        self.mc_sims_input = QComboBox()
        self.mc_sims_input.addItems(["1000", "10000", "50000", "100000"])

        form_layout.addRow(QLabel("Default Years:"), self.mc_years_input)
        form_layout.addRow(QLabel("Default Simulations:"), self.mc_sims_input)

        # --- BROKER SETTINGS ---
        broker_section = QLabel("IBKR CONNECTION SETTINGS")
        broker_section.setObjectName("section_label")
        broker_section.setStyleSheet("margin-top: 10px;") 
        form_layout.addRow(broker_section)

        self.ibkr_host_input = QLineEdit()
        self.ibkr_port_input = QSpinBox()
        self.ibkr_port_input.setRange(1000, 9999)
        self.ibkr_client_id_input = QSpinBox()
        self.ibkr_client_id_input.setRange(1, 999)
        
        self.ibkr_timeout_input = QDoubleSpinBox()
        self.ibkr_timeout_input.setRange(1.0, 30.0)
        self.ibkr_timeout_input.setSingleStep(0.5)
        self.ibkr_timeout_input.setSuffix(" sec")
        self.ibkr_timeout_input.setToolTip("Max time to wait for PnL data to settle from the broker.")

        form_layout.addRow(QLabel("Host (IP):"), self.ibkr_host_input)
        form_layout.addRow(QLabel("Port:"), self.ibkr_port_input)
        form_layout.addRow(QLabel("Client ID:"), self.ibkr_client_id_input)
        form_layout.addRow(QLabel("Data Timeout:"), self.ibkr_timeout_input)

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
        """Loads settings from the config.json file and populates the input fields with the current values. If the config file or specific keys are missing, it uses safe defaults to ensure the application remains functional."""
        config = read_json("config.json")
        if config:
            self.api_key_input.setText(config.get("GEMINI_API_KEY", ""))
            self.model_input.setText(config.get("GEMINI_MODEL", "gemini-1.5-pro"))
            self.language_input.setCurrentText(config.get("AI_LANGUAGE", "English"))
            self.risk_free_input.setValue(config.get("RISK_FREE_RATE", 0.0) * 100)
            
            self.mc_years_input.setValue(config.get("DEFAULT_YEARS", 5))
            self.mc_sims_input.setCurrentText(str(config.get("DEFAULT_SIMS", 10000)))

            self.ibkr_host_input.setText(config.get("IBKR_HOST", "127.0.0.1"))
            self.ibkr_port_input.setValue(config.get("IBKR_PORT", 4001))
            self.ibkr_client_id_input.setValue(config.get("IBKR_CLIENT_ID", 1))
            self.ibkr_timeout_input.setValue(config.get("IBKR_TIMEOUT", 5.0))

    def save_settings(self):
        """Collects the current values from the input fields and saves them to the config.json file. It provides user feedback on whether the save operation was successful and prompts for an application restart to apply changes."""
        config = read_json("config.json")
        if not isinstance(config, dict):
            config = {}
            
        config["GEMINI_API_KEY"] = self.api_key_input.text().strip()
        config["GEMINI_MODEL"] = self.model_input.text().strip()
        config["AI_LANGUAGE"] = self.language_input.currentText()
        config["RISK_FREE_RATE"] = round(self.risk_free_input.value() / 100.0, 4)
        
        config["DEFAULT_YEARS"] = self.mc_years_input.value()
        config["DEFAULT_SIMS"] = int(self.mc_sims_input.currentText())

        config["IBKR_HOST"] = self.ibkr_host_input.text().strip()
        config["IBKR_PORT"] = self.ibkr_port_input.value()
        config["IBKR_CLIENT_ID"] = self.ibkr_client_id_input.value()
        config["IBKR_TIMEOUT"] = self.ibkr_timeout_input.value()

        if write_json("config.json", config):
            QMessageBox.information(
                self, 
                "Restart Recommended", 
                "Settings saved successfully!\n\nPlease restart the application for all changes to take full effect."
            )
        else:
            QMessageBox.critical(self, "Error", "Could not save the config.json file.")