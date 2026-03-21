from __future__ import annotations

from PyQt6.QtCore import QSignalBlocker, QTimer, Qt, pyqtSignal
from PyQt6.QtWidgets import (
    QComboBox,
    QDialog,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QProgressBar,
    QVBoxLayout,
    QWidget,
)

from context.localization import LocalizationController
from context.views.theme import ThemeController


class SplashWindow(QDialog):
    continueRequested = pyqtSignal()
    themeSelected = pyqtSignal(str)
    localeSelected = pyqtSignal(str)
    userInteracted = pyqtSignal()

    def __init__(
        self,
        theme_controller: ThemeController,
        localization_controller: LocalizationController,
        auto_continue_ms: int = 1200,
        parent=None,
    ) -> None:
        super().__init__(parent)
        self._theme_controller = theme_controller
        self._localization = localization_controller
        self._auto_continue_ms = auto_continue_ms
        self._boot_complete = False
        self._user_interacted = False
        self._current_status_key = "startup.wait"

        self.setModal(False)
        self.setWindowFlag(Qt.WindowType.FramelessWindowHint, True)
        self.setWindowFlag(Qt.WindowType.Dialog, True)
        self.setObjectName("splashSurface")
        self.setFixedSize(560, 420)

        self._auto_continue_timer = QTimer(self)
        self._auto_continue_timer.setSingleShot(True)
        self._auto_continue_timer.timeout.connect(self.continueRequested.emit)

        self._title_label = QLabel()
        self._title_label.setObjectName("heroTitle")
        self._title_label.setWordWrap(True)

        self._subtitle_label = QLabel()
        self._subtitle_label.setObjectName("heroSubtitle")
        self._subtitle_label.setWordWrap(True)

        self._progress_label = QLabel()
        self._progress_label.setObjectName("secondaryLabel")

        self._hint_label = QLabel()
        self._hint_label.setObjectName("secondaryLabel")
        self._hint_label.setWordWrap(True)

        self._progress_bar = QProgressBar()
        self._progress_bar.setRange(0, 100)
        self._progress_bar.setValue(0)
        self._progress_bar.setTextVisible(False)

        self._theme_combo = QComboBox()
        self._locale_combo = QComboBox()
        self._continue_button = QPushButton()
        self._continue_button.setEnabled(False)
        self._continue_button.clicked.connect(self.continueRequested.emit)
        self._theme_caption_label = self._build_label()
        self._locale_caption_label = self._build_label()

        selectors_card = QWidget()
        selectors_card.setObjectName("splashCard")
        form = QFormLayout(selectors_card)
        form.setContentsMargins(18, 18, 18, 18)
        form.setSpacing(14)
        form.addRow(self._theme_caption_label, self._theme_combo)
        form.addRow(self._locale_caption_label, self._locale_combo)

        button_row = QHBoxLayout()
        button_row.addStretch(1)
        button_row.addWidget(self._continue_button)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(28, 28, 28, 28)
        layout.setSpacing(16)
        layout.addWidget(self._title_label)
        layout.addWidget(self._subtitle_label)
        layout.addWidget(self._progress_bar)
        layout.addWidget(self._progress_label)
        layout.addWidget(selectors_card)
        layout.addWidget(self._hint_label)
        layout.addLayout(button_row)

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
    def theme_code(self) -> str:
        return str(self._theme_combo.currentData())

    @property
    def locale_code(self) -> str:
        return str(self._locale_combo.currentData())

    @property
    def is_ready(self) -> bool:
        return self._boot_complete

    @property
    def continue_button(self) -> QPushButton:
        return self._continue_button

    def set_progress(self, completed_steps: int, total_steps: int, status_key: str) -> None:
        percent = int((completed_steps / total_steps) * 100)
        self._current_status_key = status_key
        self._progress_bar.setValue(percent)
        self._progress_label.setText(self._localization.tr(status_key))
        if not self._boot_complete:
            self._hint_label.setText(self._localization.tr("startup.wait"))

    def mark_ready(self) -> None:
        self._boot_complete = True
        self._current_status_key = "startup.ready"
        self._progress_bar.setValue(100)
        self._progress_label.setText(self._localization.tr("startup.ready"))
        self._continue_button.setEnabled(True)
        if self._user_interacted:
            self._hint_label.setText(self._localization.tr("startup.click_continue"))
        else:
            self._hint_label.setText(self._localization.tr("startup.auto_continue"))
            self._auto_continue_timer.start(self._auto_continue_ms)

    def cancel_auto_continue(self) -> None:
        self._auto_continue_timer.stop()
        if self._boot_complete:
            self._hint_label.setText(self._localization.tr("startup.click_continue"))

    def set_theme_selection(self, theme_name: str) -> None:
        index = self._theme_combo.findData(theme_name)
        if index >= 0:
            self._theme_combo.setCurrentIndex(index)

    def set_locale_selection(self, locale_code: str) -> None:
        index = self._locale_combo.findData(locale_code)
        if index >= 0:
            self._locale_combo.setCurrentIndex(index)

    def _build_label(self) -> QLabel:
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
        self._register_interaction()
        theme_name = str(self._theme_combo.currentData())
        if theme_name != self._theme_controller.theme_name:
            self.themeSelected.emit(theme_name)

    def _on_locale_combo_changed(self, index: int) -> None:
        if index < 0:
            return
        self._register_interaction()
        locale_code = str(self._locale_combo.currentData())
        if locale_code != self._localization.locale:
            self.localeSelected.emit(locale_code)

    def _on_locale_changed(self, _locale_code: str) -> None:
        self._populate_theme_combo()
        self._populate_locale_combo()
        self._retranslate_ui()

    def _register_interaction(self) -> None:
        self._user_interacted = True
        self.cancel_auto_continue()
        self.userInteracted.emit()

    def _retranslate_ui(self) -> None:
        self.setWindowTitle(self._localization.tr("app.name"))
        self._title_label.setText(self._localization.tr("startup.title"))
        self._subtitle_label.setText(self._localization.tr("startup.subtitle"))
        self._theme_caption_label.setText(self._localization.tr("startup.select_theme"))
        self._locale_caption_label.setText(self._localization.tr("startup.select_language"))
        self._continue_button.setText(self._localization.tr("startup.continue"))
        self._progress_label.setText(self._localization.tr(self._current_status_key))
        if self._boot_complete:
            self._hint_label.setText(
                self._localization.tr("startup.click_continue" if self._user_interacted else "startup.auto_continue")
            )
        else:
            self._hint_label.setText(self._localization.tr("startup.wait"))
