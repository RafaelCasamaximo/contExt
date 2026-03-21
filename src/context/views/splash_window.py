from __future__ import annotations

from PyQt6.QtCore import QSignalBlocker, Qt, pyqtSignal
from PyQt6.QtWidgets import (
    QComboBox,
    QDialog,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from context.localization import LocalizationController
from context.views.theme import ThemeController


class SplashWindow(QDialog):
    newProjectRequested = pyqtSignal()
    openProjectRequested = pyqtSignal()
    quitRequested = pyqtSignal()
    themeSelected = pyqtSignal(str)
    localeSelected = pyqtSignal(str)

    def __init__(
        self,
        theme_controller: ThemeController,
        localization_controller: LocalizationController,
        version_text: str,
        parent=None,
    ) -> None:
        super().__init__(parent)
        self._theme_controller = theme_controller
        self._localization = localization_controller
        self._version_text = version_text

        self.setModal(False)
        self.setWindowFlag(Qt.WindowType.FramelessWindowHint, True)
        self.setWindowFlag(Qt.WindowType.Dialog, True)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.setObjectName("splashSurface")
        self.setFixedSize(840, 520)

        self._logo_label = QLabel("CX")
        self._logo_label.setObjectName("logoBadge")
        self._logo_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._logo_label.setFixedSize(120, 120)

        self._title_label = QLabel()
        self._title_label.setObjectName("heroTitle")
        self._title_label.setWordWrap(True)

        self._subtitle_label = QLabel()
        self._subtitle_label.setObjectName("heroSubtitle")
        self._subtitle_label.setWordWrap(True)

        self._version_label = QLabel()
        self._version_label.setObjectName("versionPill")

        self._new_project_button = QPushButton()
        self._new_project_button.setObjectName("startPrimaryButton")
        self._new_project_button.clicked.connect(self.newProjectRequested.emit)

        self._open_project_button = QPushButton()
        self._open_project_button.setObjectName("startSecondaryButton")
        self._open_project_button.clicked.connect(self.openProjectRequested.emit)

        self._quit_button = QPushButton()
        self._quit_button.setObjectName("startCloseButton")
        self._quit_button.clicked.connect(self.quitRequested.emit)

        self._theme_combo = QComboBox()
        self._theme_combo.setObjectName("startupCombo")
        self._theme_combo.setMinimumWidth(240)
        self._locale_combo = QComboBox()
        self._locale_combo.setObjectName("startupCombo")
        self._locale_combo.setMinimumWidth(240)
        self._theme_caption_label = self._build_secondary_label()
        self._locale_caption_label = self._build_secondary_label()

        brand_card = QWidget()
        brand_card.setObjectName("splashBrandCard")
        brand_layout = QVBoxLayout(brand_card)
        brand_layout.setContentsMargins(28, 28, 28, 28)
        brand_layout.setSpacing(18)
        brand_layout.addWidget(self._logo_label, alignment=Qt.AlignmentFlag.AlignLeft)
        brand_layout.addWidget(self._title_label)
        brand_layout.addWidget(self._subtitle_label)
        brand_layout.addStretch(1)
        brand_layout.addWidget(self._version_label, alignment=Qt.AlignmentFlag.AlignLeft)

        action_card = QWidget()
        action_card.setObjectName("splashCard")
        action_card.setMinimumWidth(340)
        action_layout = QVBoxLayout(action_card)
        action_layout.setContentsMargins(26, 26, 26, 26)
        action_layout.setSpacing(18)
        action_layout.addWidget(self._new_project_button)
        action_layout.addWidget(self._open_project_button)

        settings_card = QWidget()
        settings_card.setObjectName("startSettingsCard")
        settings_layout = QVBoxLayout(settings_card)
        settings_layout.setContentsMargins(16, 16, 16, 16)
        settings_layout.setSpacing(12)
        settings_layout.addWidget(self._theme_caption_label)
        settings_layout.addWidget(self._theme_combo)
        settings_layout.addWidget(self._locale_caption_label)
        settings_layout.addWidget(self._locale_combo)
        action_layout.addWidget(settings_card)
        action_layout.addStretch(1)
        action_layout.addWidget(self._quit_button, alignment=Qt.AlignmentFlag.AlignRight)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(28, 28, 28, 28)
        layout.setSpacing(18)
        layout.addWidget(brand_card, 7)
        layout.addWidget(action_card, 6)

        self._theme_combo.currentIndexChanged.connect(self._on_theme_combo_changed)
        self._locale_combo.currentIndexChanged.connect(self._on_locale_combo_changed)
        self._theme_controller.themeChanged.connect(self._sync_theme_selection)
        self._localization.localeChanged.connect(self._on_locale_changed)

        self._populate_theme_combo()
        self._populate_locale_combo()
        self._sync_theme_selection()
        self._sync_locale_selection()
        self._retranslate_ui()

    @property
    def new_project_button(self) -> QPushButton:
        return self._new_project_button

    @property
    def open_project_button(self) -> QPushButton:
        return self._open_project_button

    @property
    def quit_button(self) -> QPushButton:
        return self._quit_button

    @property
    def version_label(self) -> QLabel:
        return self._version_label

    def set_theme_selection(self, theme_name: str) -> None:
        index = self._theme_combo.findData(theme_name)
        if index >= 0:
            self._theme_combo.setCurrentIndex(index)

    def set_locale_selection(self, locale_code: str) -> None:
        index = self._locale_combo.findData(locale_code)
        if index >= 0:
            self._locale_combo.setCurrentIndex(index)

    def _build_secondary_label(self) -> QLabel:
        label = QLabel()
        label.setObjectName("secondaryLabel")
        return label

    def _populate_theme_combo(self) -> None:
        blocker = QSignalBlocker(self._theme_combo)
        try:
            current_theme = self._theme_controller.theme_name
            self._theme_combo.clear()
            for theme_name in self._theme_controller.available_themes():
                self._theme_combo.addItem(self._localization.tr(f"theme.name.{theme_name}"), theme_name)
            if current_theme:
                index = self._theme_combo.findData(current_theme)
                if index >= 0:
                    self._theme_combo.setCurrentIndex(index)
        finally:
            del blocker

    def _populate_locale_combo(self) -> None:
        blocker = QSignalBlocker(self._locale_combo)
        try:
            current_locale = self._localization.locale
            self._locale_combo.clear()
            for locale_code in self._localization.available_locales():
                self._locale_combo.addItem(self._localization.tr(f"language.name.{locale_code}"), locale_code)
            index = self._locale_combo.findData(current_locale)
            if index >= 0:
                self._locale_combo.setCurrentIndex(index)
        finally:
            del blocker

    def _sync_theme_selection(self, _theme=None) -> None:
        self.set_theme_selection(self._theme_controller.theme_name)

    def _sync_locale_selection(self) -> None:
        self.set_locale_selection(self._localization.locale)

    def _on_theme_combo_changed(self, index: int) -> None:
        if index < 0:
            return
        theme_name = str(self._theme_combo.currentData())
        if theme_name != self._theme_controller.theme_name:
            self.themeSelected.emit(theme_name)

    def _on_locale_combo_changed(self, index: int) -> None:
        if index < 0:
            return
        locale_code = str(self._locale_combo.currentData())
        if locale_code != self._localization.locale:
            self.localeSelected.emit(locale_code)

    def _on_locale_changed(self, _locale_code: str) -> None:
        self._populate_theme_combo()
        self._populate_locale_combo()
        self._retranslate_ui()

    def _retranslate_ui(self) -> None:
        self.setWindowTitle(self._localization.tr("app.name"))
        self._title_label.setText(self._localization.tr("startup.title"))
        self._subtitle_label.setText(self._localization.tr("startup.subtitle"))
        self._new_project_button.setText(self._localization.tr("startup.new_project"))
        self._open_project_button.setText(self._localization.tr("startup.open_project"))
        self._quit_button.setText(self._localization.tr("startup.close"))
        self._theme_caption_label.setText(self._localization.tr("startup.select_theme"))
        self._locale_caption_label.setText(self._localization.tr("startup.select_language"))
        self._version_label.setText(self._localization.tr("startup.version", version=self._version_text))
