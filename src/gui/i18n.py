"""Фрагмент GUI: I18nMixin."""

from matplotlib.ticker import MultipleLocator

from ..model.pattern.utils import normalize_profile
from .ui_text import ascii_ui_text


class I18nMixin:
    def tr(self, key: str) -> str:
        """Возвращает локализованную строку интерфейса.

        Args:
            key: Ключ из ``UI_TEXTS``.

        Returns:
            Перевод для текущего языка или сам ключ, если перевод не найден.
        """
        lang = self.language_var.get().strip().lower()
        raw = self.UI_TEXTS.get(lang, self.UI_TEXTS["en"]).get(key, key)
        return ascii_ui_text(raw)

    @staticmethod
    def _configure_twotheta_axis(ax) -> None:
        """Настраивает ось 2θ: подписи каждые 10°, деления — каждый градус.

        Args:
            ax: Ось matplotlib для оси абсцисс графика.
        """
        ax.xaxis.set_major_locator(MultipleLocator(10))
        ax.xaxis.set_minor_locator(MultipleLocator(1))
        ax.tick_params(axis="x", which="major", length=6)
        ax.tick_params(axis="x", which="minor", length=3)

    def _lattice_label(self, key: str) -> str:
        """Возвращает локализованную подпись сингонии по внутреннему ключу.

        Args:
            key: Ключ из ``LATTICE_FAMILY_KEYS``.

        Returns:
            Строка для отображения в комбобоксе.
        """
        lang = self.language_var.get().strip().lower()
        return ascii_ui_text(
            self.LATTICE_FAMILY_LABELS_BY_LANG.get(
                lang, self.LATTICE_FAMILY_LABELS_BY_LANG["en"]
            ).get(key, key)
        )

    def _lattice_labels(self):
        """Список подписей всех сингоний для комбобокса.

        Returns:
            Список локализованных строк в порядке ``LATTICE_FAMILY_KEYS``.
        """
        return [self._lattice_label(k) for k in self.LATTICE_FAMILY_KEYS]

    def _set_lattice_family_by_key(self, key: str):
        """Устанавливает выбранную сингонию по внутреннему ключу.

        Args:
            key: Ключ из ``LATTICE_FAMILY_KEYS``.
        """
        self.lattice_family_var.set(self._lattice_label(key))

    def _profile_label(self, key: str) -> str:
        """Возвращает локализованную подпись профиля линии.

        Args:
            key: Ключ из ``PROFILE_KEYS``.

        Returns:
            Строка для отображения в комбобоксе профиля.
        """
        lang = self.language_var.get().strip().lower()
        return ascii_ui_text(
            self.PROFILE_LABELS_BY_LANG.get(
                lang, self.PROFILE_LABELS_BY_LANG["en"]
            ).get(key, key)
        )

    def _profile_labels(self):
        """Список подписей профилей для комбобокса.

        Returns:
            Список локализованных строк в порядке ``PROFILE_KEYS``.
        """
        return [self._profile_label(k) for k in self.PROFILE_KEYS]

    def _profile_key(self) -> str:
        """Определяет внутренний ключ профиля по текущей подписи в GUI.

        Returns:
            Ключ профиля (``bar``, ``gaussian`` и т.д.).
        """
        label = self.profile_var.get().strip()
        for labels in self.PROFILE_LABELS_BY_LANG.values():
            for key, lbl in labels.items():
                if lbl == label:
                    return key
        return normalize_profile(label)

    def _set_profile_by_key(self, key: str):
        """Устанавливает профиль линии по внутреннему ключу.

        Args:
            key: Ключ профиля или его нормализованное имя.
        """
        self.profile_var.set(self._profile_label(normalize_profile(key)))

    def _on_language_selected(self, _event=None):
        """Перестраивает интерфейс при смене языка, сохраняя состояние формы.

        Args:
            _event: Событие комбобокса (не используется).
        """
        current_family = self._lattice_family_key()
        current_profile = self._profile_key()
        current_theme = self._theme_key()
        label_mode = self.label_reflection_mode_var.get()
        selected_indices = list(getattr(self, "_selected_calc_indices", []))
        self._save_option_state_cache = {
            k: v.get() for k, v in self._save_option_vars.items()
        }
        selected_config = (
            self.config_combo.get().strip() if hasattr(self, "config_combo") else ""
        )
        for child in self.root.winfo_children():
            child.destroy()
        self._section_content = {}
        self._section_buttons = {}
        self.create_widgets()
        self._set_lattice_family_by_key(current_family)
        self._set_profile_by_key(current_profile)
        self._set_theme_by_key(current_theme)
        self._on_profile_selected()
        self._apply_gui_theme(redraw_plot=False)
        self.label_reflection_mode_var.set(label_mode)
        self._selected_calc_indices = selected_indices
        self._refresh_calc_results_list()
        if self._selected_calc_indices:
            self._select_calc_result_indices(self._selected_calc_indices, redraw=False)
            selected = self._get_selected_calc_results()
            if selected:
                self._display_calc_results(selected)
        self.root.title(self.tr("window_title"))
        self.scan_config_files()
        if selected_config and selected_config in self.config_files:
            self.config_combo.set(selected_config)
        self._commit_form_state()
