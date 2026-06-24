"""Константы и строки локализации GUI."""


class GuiConstants:
    APP_VERSION = "0.1.5"

    SAVE_OUTPUT_KEYS = (
        "powder_png",
        "txt",
        "angles_int",
        "config",
        "cell_png",
        "G_csv",
        "Gstar_csv",
    )
    SAVE_OUTPUT_PRIMARY_KEYS = ("powder_png", "txt", "angles_int")
    SAVE_OUTPUT_DEFAULT_KEYS = frozenset(SAVE_OUTPUT_PRIMARY_KEYS)
    EXPORT_FILENAMES = {
        "ru": {
            "powder_png": "Дифрактограмма.png",
            "txt": "Рассчит.данные.txt",
            "angles_int": "углы-инт.txt",
        },
        "en": {
            "powder_png": "Diffractogram.png",
            "txt": "Calculated data.txt",
            "angles_int": "angles-int.txt",
        },
    }
    PLOT_LEGEND_LOCS = (
        "best",
        "upper right",
        "upper left",
        "lower right",
        "lower left",
        "center right",
        "center left",
    )
    LATTICE_FAMILY_KEYS = (
        "manual",
        "cubic",
        "tetragonal",
        "orthorhombic",
        "hexagonal",
        "rhombohedral",
        "monoclinic",
    )
    LATTICE_FAMILY_LABELS_BY_LANG = {
        "ru": {
            "manual": "Вручную",
            "cubic": "Куб.",
            "tetragonal": "Тетр.",
            "orthorhombic": "Орт.",
            "hexagonal": "Гекс.",
            "rhombohedral": "Ромб.",
            "monoclinic": "Монокл.",
        },
        "en": {
            "manual": "Manual",
            "cubic": "Cubic",
            "tetragonal": "Tetragonal",
            "orthorhombic": "Orthorhombic",
            "hexagonal": "Hexagonal",
            "rhombohedral": "Rhombohedral",
            "monoclinic": "Monoclinic",
        },
    }
    LANGUAGE_LABELS = {"ru": "Русский", "en": "English"}
    PROFILE_KEYS = ("bar", "gaussian", "lorentzian", "pseudo-voigt")
    PROFILE_LABELS_BY_LANG = {
        "ru": {
            "bar": "штрих",
            "gaussian": "гаусс",
            "lorentzian": "лоренц",
            "pseudo-voigt": "псевдо-войт",
        },
        "en": {
            "bar": "bar",
            "gaussian": "gaussian",
            "lorentzian": "lorentzian",
            "pseudo-voigt": "pseudo-voigt",
        },
    }
    UI_TEXTS = {
        "ru": {
            "config_frame": "Загрузка данных из списка",
            "select_config": "Список:",
            "refresh_list": "Обновить список",
            "add_config_file": "Добавить файл",
            "remove_config": "Удалить из списка",
            "add_config_file_title": "Выберите файл конфигурации",
            "remove_config_confirm": "Удалить «{name}» из списка?",
            "config_removed": "«{name}» удалён из списка.",
            "config_added": "Добавлено: {path}",
            "config_add_failed": "Не удалось добавить:\n{error}",
            "config_remove_failed": "Не удалось убрать:\n{error}",
            "config_nothing_selected": "Выберите пункт в списке.",
            "config_invalid_path": "Файл или папка не найдены:\n{path}",
            "language": "Язык:",
            "theme": "Тема:",
            "ui_settings": "Интерфейс",
            "crystal_params": "Параметры кристалла",
            "centering": "Тип ячейки:",
            "system": "Сингония:",
            "name": "Имя файла:",
            "element_col": "Элемент",
            "a_axis": "a (Å):",
            "b_axis": "b (Å):",
            "c_axis": "c (Å):",
            "alpha_angle": "α (град):",
            "beta_angle": "β (град):",
            "gamma_angle": "γ (град):",
            "atoms": "Атомы",
            "show_biso": "Показать колонку B_iso",
            "add_atom": "Добавить атом",
            "remove_atom": "Удалить последний атом",
            "pattern_params": "Параметры дифракции",
            "wavelength1": "Длина волны (Å):",
            "wavelength2": "Длина волны 2 (Å):",
            "wl2_ratio": "I(λ2)/I(λ1):",
            "tth_range": "2θ диапазон:",
            "step": "шаг",
            "profile": "Профиль:",
            "pseudo_voigt_eta": "η (pseudo-Voigt):",
            "caglioti": "Кальотти U, V, W:",
            "thetam": "θm (град, поляризация):",
            "use_wl2": "Использовать вторую длину волны",
            "generate_pattern": "Рассчитать дифрактограмму",
            "reset_zoom": "Вернуть исх. масштаб",
            "plot_area": "Дифрактограмма",
            "calc_results": "Рассчитанные дифрактограммы",
            "calc_results_multi_hint": "Ctrl+клик — несколько кривых на графике",
            "calc_result_tip_name": "Имя: {name}",
            "calc_result_tip_wl": "λ (Å): {wl}",
            "calc_result_tip_wl2_ratio": "I(λ2)/I(λ1): {ratio:g}",
            "calc_result_tip_tth": "2θ: {start}–{end} град, шаг {step}",
            "calc_result_tip_profile": "Профиль: {profile}",
            "calc_result_tip_cell": "Ячейка: a={a:.4f} b={b:.4f} c={c:.4f} Å",
            "calc_result_tip_angles": "Углы: α={alpha:.1f} β={beta:.1f} γ={gamma:.1f} град",
            "calc_result_tip_refl": "Отражений: {n}",
            "calc_result_tip_norm_yes": "Нормировка: да (max={max:.0f})",
            "calc_result_tip_norm_no": "Нормировка: нет",
            "save_to_folder": "Сохранить",
            "save_pick_folder": "Выберите папку для сохранения",
            "save_files_group": "Файлы для сохранения:",
            "save_file_txt": "Рассчит.данные (.txt)",
            "save_file_angles_int": "углы-инт (.txt)",
            "save_file_config": "Конфиг расчёта (.yaml)",
            "save_file_powder_png": "Дифрактограмма (.png)",
            "save_file_cell_png": "Схема ячейки (.png)",
            "save_file_G_csv": "Матрица G (.csv)",
            "save_file_Gstar_csv": "Матрица G* (.csv)",
            "save_nothing_selected": "Отметьте хотя бы один тип файла.",
            "save_no_result_selected": "Выберите дифрактограмму в списке.",
            "save_success": "Сохранено в:\n{path}",
            "save_failed": "Не удалось сохранить:\n{error}",
            "calc_done_message": (
                "Расчёт добавлен в список справа.\nДлины волн: {wl_msg}{ratio_msg}"
            ),
            "calc_progress_title": "Расчёт дифрактограммы",
            "calc_progress_start": "Подготовка…",
            "calc_progress_crystal": "Построение кристалла…",
            "calc_progress_reuse": "Переиспользование отражений…",
            "calc_progress_pattern": "Расчёт отражений (λ {n}/{total})…",
            "calc_progress_curve": "Свёртка профилей (λ {n}/{total})…",
            "calc_progress_combine": "Суммирование кривых…",
            "calc_progress_done": "Готово",
            "label_reflection_hide": "Не показывать углы и hkl",
            "label_reflection_hkl": "Показать hkl",
            "label_reflection_angles": "Показать углы",
            "label_reflection_angles_hkl": "Показать углы и hkl",
            "hover_angle": "2θ = {angle:.3f}°",
            "print_pattern": "Печать",
            "warning_title": "Предупреждение",
            "error_title": "Ошибка",
            "input_error_title": "Ошибка ввода",
            "no_pattern_to_print": "Сначала постройте дифрактограмму.",
            "printer_not_found": "Не найден доступный механизм печати в системе.",
            "print_failed": "Не удалось отправить на печать:\n{error}",
            "print_sent": "График отправлен на печать.",
            "at_least_one_atom": "Нужен хотя бы один атом.",
            "failed_load_config": "Не удалось загрузить конфиг:\n{error}",
            "config_dir_not_found": "Папка с конфигами не найдена: {path}",
            "invalid_atom_number": "Некорректное число в атоме: {error}",
            "failed_generate_pattern": "Не удалось построить дифрактограмму:\n{error}",
            "invalid_space_group": "Некорректная группа симметрии (номер Hall или пусто для авто): {value!r}",
            "invalid_second_wavelength": "Некорректная вторая длина волны: {value!r}",
            "invalid_ratio_nonnegative": "Отношение интенсивностей I(λ2)/I(λ1) должно быть неотрицательным.",
            "orthogonal_cell_title": "Ортогональная ячейка",
            "orthogonal_cell_warning": "Развёртка P/I/F/C/A/B задаётся в дробях по базису при α≈β≈γ≈90° (куб, тетрагон, орторомб и т.п.). Атомы не разворачиваются.",
            "plot_xlabel": "2θ (град)",
            "plot_ylabel": "I, отн. ед.",
            "plot_ylabel_normalized": "I, отн. ед.",
            "plot_title": "Дифрактограмма",
            "ratio_on_plot": "\nI(λ2)/I(λ1) = {ratio:g} (на графике)",
            "success_title": "Успех",
            "success_message": "Рассчитано для длин волн: {wl_msg}{ratio_msg}\nСохранено в {run_dir}: TXT и изображение для первой длины волны.",
            "window_title": "Расчёт дифрактограммы",
            "menu_file": "Файл",
            "menu_edit": "Правка",
            "menu_undo": "Отменить",
            "menu_view": "Вид",
            "menu_help": "Справка",
            "menu_open_config": "Открыть конфигурацию…",
            "menu_add_config": "Добавить в список…",
            "menu_exit": "Выход",
            "menu_language": "Язык",
            "menu_theme": "Тема",
            "menu_plot_settings": "Вид графика…",
            "menu_about": "О программе",
            "menu_config_filter": "Конфигурация YAML/JSON",
            "menu_all_files": "Все файлы",
            "config_loaded": "Загружено: {name}\n{path}",
            "plot_settings_title": "Вид графика",
            "plot_settings_section_curve": "Кривая и холст",
            "plot_settings_section_grid": "Сетка и линии отражений",
            "plot_settings_section_labels": "Подписи и легенда",
            "plot_settings_line_width": "Толщина линии:",
            "plot_settings_antialiased": "Сглаживание линии",
            "plot_settings_dpi": "DPI:",
            "plot_settings_aspect": "Соотношение сторон:",
            "plot_settings_y_margin": "Запас по Y (×):",
            "plot_settings_layout_pad": "Отступ tight_layout:",
            "plot_settings_grid_major": "Сетка (каждые 10°)",
            "plot_settings_grid_major_lw": "Толщина major-сетки:",
            "plot_settings_grid_major_alpha": "Прозрачность major:",
            "plot_settings_grid_minor": "Деления сетки (1°)",
            "plot_settings_grid_minor_lw": "Толщина minor-сетки:",
            "plot_settings_grid_minor_alpha": "Прозрачность minor:",
            "plot_settings_vlines": "Линии отражений",
            "plot_settings_vline_width": "Толщина линий отражений:",
            "plot_settings_vline_alpha": "Прозрачность линий отражений:",
            "plot_settings_title_show": "Заголовок графика",
            "plot_settings_title_size": "Размер заголовка (0=авто):",
            "plot_settings_axis_label_size": "Размер подписей осей (0=авто):",
            "plot_settings_tick_size": "Размер делений осей:",
            "plot_settings_peak_label_size": "Размер подписей пиков (0=как деления):",
            "plot_settings_legend_show": "Легенда (несколько кривых)",
            "plot_settings_legend_loc": "Положение легенды:",
            "plot_settings_size_hint": "0 — использовать размер из темы интерфейса.",
            "plot_settings_apply": "Применить",
            "plot_settings_close": "Закрыть",
            "plot_settings_invalid": "Проверьте числовые значения (размеры, прозрачность 0–1, запас Y > 1).",
            "delete_calc_result": "Удалить дифрактограмму",
            "delete_calc_none": "Выберите расчёт в списке.",
            "delete_calc_confirm": "Удалить расчёт «{name}»?",
            "delete_calc_confirm_multi": "Удалить {n} выбранных расчётов?",
            "menu_help_guide": "Подробное описание…",
            "menu_help_shortcuts": "Сочетания клавиш…",
            "shortcuts_intro": "Горячие клавиши работают в окне программы (Delete на списке расчётов — удаление).",
            "shortcut_open_config": "Открыть конфигурацию",
            "shortcut_save": "Сохранить расчёт в папку",
            "shortcut_print": "Печать графика",
            "shortcut_calc": "Рассчитать дифрактограмму",
            "shortcut_undo": "Отменить последнее действие",
            "shortcut_plot_settings": "Вид графика",
            "shortcut_reset_zoom": "Сброс масштаба графика",
            "shortcut_delete_result": "Удалить выбранный расчёт",
            "shortcut_quit": "Выход",
            "shortcut_help": "Подробное описание",
            "about_text": (
                "XRay MSU — расчёт порошковой рентгеновской дифрактограммы.\n\n"
                "Версия 0.1.5\n"
                "Разработка кафедры физики твердого тела, физического факультета "
                "МГУ им. М. В. Ломоносова.\n\n"
                "Модель: кристалл → отражения → свёртка профилей.\n"
                "Справка → «Сочетания клавиш» (Ctrl+O, F5, Ctrl+S и др.)."
            ),
            "about_detailed_text": (
                "XRay MSU — симуляция порошковой рентгеновской дифрактограммы.\n\n"
                "Автор и разработка: Меркулов Илья merkuloviv@my.msu.ru / проект XRay MSU (кафедра физики твердого тела"
                ", МГУ им. М. В. Ломоносова).\n"
                "Версия 0.1.5\n\n"
                "1. Общая схема расчёта\n"
                "Задаются параметры элементарной ячейки (a, b, c; α, β, γ) и дробные координаты "
                "атомов. По метрическим тензорам G и G* находятся межплоскостные расстояния d(hkl), "
                "структурные факторы F(hkl), кратности M, факторы L и P. Интенсивности пиков "
                "I = S·M·L·P·|F|² сворачиваются выбранным профилем (штрих, Gaussian, Lorentz, "
                "pseudo-Voigt) с шириной по формулам Кальотти (U, V, W).\n\n"
                "2. Окно программы\n"
                "Слева — параметры кристалла и расчёта, справа — график I(2θ). Конфигурации "
                "загружаются из YAML/JSON (File или список). Результаты накапливаются в списке "
                "справа; их можно сравнивать, сохранять и удалять.\n\n"
                "3. Центровка и симметрия\n"
                "Тип ячейки P/I/F/C/A/B разворачивает атомы в дробях базиса при отсутствии "
                "номера space group. Сингония подставляет ограничения на параметры ячейки.\n\n"
                "4. Две длины волн\n"
                "Можно задать вторую λ и отношение интенсивностей; кривые суммируются на одном "
                "графике.\n\n"
                "5. Экспорт\n"
                "TXT-таблица отражений, YAML конфиг, PNG дифрактограммы и ячейки, CSV для G и G*.\n\n"
                "6. Сочетания клавиш\n"
                "Ctrl+O — открыть конфиг; Ctrl+S — сохранить; Ctrl+P — печать; F5 или Ctrl+Enter — расчёт; "
                "Ctrl+Z — отмена; Ctrl+G — вид графика; Ctrl+R — сброс масштаба; Delete / Ctrl+Delete — "
                "удалить расчёт; Ctrl+Q — выход; F1 — эта справка. Полный список: Справка → Сочетания клавиш.\n\n"
                "Подробная физическая модель — в doc/README-overview.md репозитория."
            ),
        },
        "en": {
            "config_frame": "Load data from list",
            "select_config": "List:",
            "refresh_list": "Refresh list",
            "add_config_file": "Add file",
            "remove_config": "Remove from list",
            "add_config_file_title": "Select configuration file",
            "remove_config_confirm": "Remove «{name}» from the list?",
            "config_removed": "Removed «{name}» from the list.",
            "config_added": "Added: {path}",
            "config_add_failed": "Failed to add:\n{error}",
            "config_remove_failed": "Failed to remove:\n{error}",
            "config_nothing_selected": "Select an item from the list.",
            "config_invalid_path": "File or folder not found:\n{path}",
            "language": "Language:",
            "theme": "Theme:",
            "ui_settings": "Interface",
            "crystal_params": "Crystal Parameters",
            "centering": "Cell type:",
            "system": "Crystal system:",
            "name": "File name:",
            "element_col": "Element",
            "a_axis": "a (Å):",
            "b_axis": "b (Å):",
            "c_axis": "c (Å):",
            "alpha_angle": "α (°):",
            "beta_angle": "β (°):",
            "gamma_angle": "γ (°):",
            "atoms": "Atoms",
            "show_biso": "Show B_iso column",
            "add_atom": "Add Atom",
            "remove_atom": "Remove Last Atom",
            "pattern_params": "Pattern Parameters",
            "wavelength1": "Wavelength (Å):",
            "wavelength2": "Wavelength 2 (Å):",
            "wl2_ratio": "I(λ2)/I(λ1):",
            "tth_range": "2θ range:",
            "step": "step",
            "profile": "Profile:",
            "pseudo_voigt_eta": "η (pseudo-Voigt):",
            "caglioti": "Caglioti U, V, W:",
            "thetam": "θm (deg, polarization):",
            "use_wl2": "Use second wavelength",
            "generate_pattern": "Calculate diffractogram",
            "reset_zoom": "Restore initial zoom",
            "plot_area": "Diffractogram",
            "calc_results": "Calculated patterns",
            "calc_results_multi_hint": "Ctrl+click — overlay multiple curves",
            "calc_result_tip_name": "Name: {name}",
            "calc_result_tip_wl": "λ (Å): {wl}",
            "calc_result_tip_wl2_ratio": "I(λ2)/I(λ1): {ratio:g}",
            "calc_result_tip_tth": "2θ: {start}–{end} deg, step {step}",
            "calc_result_tip_profile": "Profile: {profile}",
            "calc_result_tip_cell": "Cell: a={a:.4f} b={b:.4f} c={c:.4f} Å",
            "calc_result_tip_angles": "Angles: α={alpha:.1f} β={beta:.1f} γ={gamma:.1f} deg",
            "calc_result_tip_refl": "Reflections: {n}",
            "calc_result_tip_norm_yes": "Normalized: yes (max={max:.0f})",
            "calc_result_tip_norm_no": "Normalized: no",
            "save_to_folder": "Save",
            "save_pick_folder": "Choose folder to save",
            "save_files_group": "Files to save:",
            "save_file_txt": "Calculated data (.txt)",
            "save_file_angles_int": "angles-int (.txt)",
            "save_file_config": "Run config (.yaml)",
            "save_file_powder_png": "Diffractogram (.png)",
            "save_file_cell_png": "Unit cell (.png)",
            "save_file_G_csv": "Metric G (.csv)",
            "save_file_Gstar_csv": "Metric G* (.csv)",
            "save_nothing_selected": "Select at least one file type.",
            "save_no_result_selected": "Select a pattern from the list.",
            "save_success": "Saved to:\n{path}",
            "save_failed": "Failed to save:\n{error}",
            "calc_done_message": (
                "Result added to the list on the right.\n"
                "Wavelengths: {wl_msg}{ratio_msg}"
            ),
            "calc_progress_title": "Calculating diffractogram",
            "calc_progress_start": "Preparing…",
            "calc_progress_crystal": "Building crystal…",
            "calc_progress_reuse": "Reusing reflections…",
            "calc_progress_pattern": "Computing reflections (λ {n}/{total})…",
            "calc_progress_curve": "Convoluting profiles (λ {n}/{total})…",
            "calc_progress_combine": "Combining curves…",
            "calc_progress_done": "Done",
            "label_reflection_hide": "Hide angles and hkl",
            "label_reflection_hkl": "Show hkl",
            "label_reflection_angles": "Show angles",
            "label_reflection_angles_hkl": "Show angles and hkl",
            "hover_angle": "2θ = {angle:.3f}°",
            "print_pattern": "Print pattern",
            "warning_title": "Warning",
            "error_title": "Error",
            "input_error_title": "Input Error",
            "no_pattern_to_print": "Build a diffractogram first.",
            "printer_not_found": "No available system print backend was found.",
            "print_failed": "Failed to print:\n{error}",
            "print_sent": "Diffractogram was sent to printer.",
            "at_least_one_atom": "At least one atom required.",
            "failed_load_config": "Failed to load config:\n{error}",
            "config_dir_not_found": "Config directory not found: {path}",
            "invalid_atom_number": "Invalid number in atom: {error}",
            "failed_generate_pattern": "Failed to build diffractogram:\n{error}",
            "invalid_space_group": "Invalid space group (Hall number or empty for auto): {value!r}",
            "invalid_second_wavelength": "Invalid second wavelength: {value!r}",
            "invalid_ratio_nonnegative": "Intensity ratio I(λ2)/I(λ1) must be non-negative.",
            "orthogonal_cell_title": "Orthogonal cell",
            "orthogonal_cell_warning": "P/I/F/C/A/B expansion is defined in fractional shifts for basis with α≈β≈γ≈90° (cubic, tetragonal, orthorhombic, etc.). Atoms are not expanded.",
            "plot_xlabel": "2θ (deg)",
            "plot_ylabel": "Intensity, rel. units",
            "plot_ylabel_normalized": "Intensity, normalized",
            "plot_title": "Diffractogram",
            "ratio_on_plot": "\nI(λ2)/I(λ1) = {ratio:g} (on plot)",
            "success_title": "Success",
            "success_message": "Calculated for wavelengths: {wl_msg}{ratio_msg}\nSaved under {run_dir}: TXT and image files for the first wavelength.",
            "window_title": "Diffractogram calculator",
            "menu_file": "File",
            "menu_edit": "Edit",
            "menu_undo": "Undo",
            "menu_view": "View",
            "menu_help": "Help",
            "menu_open_config": "Open configuration…",
            "menu_add_config": "Add to list…",
            "menu_exit": "Exit",
            "menu_language": "Language",
            "menu_theme": "Theme",
            "menu_plot_settings": "Plot appearance…",
            "menu_about": "About",
            "menu_config_filter": "YAML/JSON configuration",
            "menu_all_files": "All files",
            "config_loaded": "Loaded: {name}\n{path}",
            "plot_settings_title": "Plot appearance",
            "plot_settings_section_curve": "Curve and canvas",
            "plot_settings_section_grid": "Grid and reflection lines",
            "plot_settings_section_labels": "Labels and legend",
            "plot_settings_line_width": "Line width:",
            "plot_settings_antialiased": "Antialiased line",
            "plot_settings_dpi": "DPI:",
            "plot_settings_aspect": "Aspect ratio:",
            "plot_settings_y_margin": "Y headroom (×):",
            "plot_settings_layout_pad": "tight_layout padding:",
            "plot_settings_grid_major": "Major grid (every 10°)",
            "plot_settings_grid_major_lw": "Major grid line width:",
            "plot_settings_grid_major_alpha": "Major grid alpha:",
            "plot_settings_grid_minor": "Minor grid (1°)",
            "plot_settings_grid_minor_lw": "Minor grid line width:",
            "plot_settings_grid_minor_alpha": "Minor grid alpha:",
            "plot_settings_vlines": "Reflection guide lines",
            "plot_settings_vline_width": "Reflection line width:",
            "plot_settings_vline_alpha": "Reflection line alpha:",
            "plot_settings_title_show": "Plot title",
            "plot_settings_title_size": "Title size (0=auto):",
            "plot_settings_axis_label_size": "Axis label size (0=auto):",
            "plot_settings_tick_size": "Tick label size:",
            "plot_settings_peak_label_size": "Peak label size (0=tick size):",
            "plot_settings_legend_show": "Legend (multiple curves)",
            "plot_settings_legend_loc": "Legend location:",
            "plot_settings_size_hint": "0 — use size from the UI theme.",
            "plot_settings_apply": "Apply",
            "plot_settings_close": "Close",
            "plot_settings_invalid": "Check numeric values (sizes, alpha 0–1, Y headroom > 1).",
            "delete_calc_result": "Delete",
            "delete_calc_none": "Select a result in the list.",
            "delete_calc_confirm": "Delete result «{name}»?",
            "delete_calc_confirm_multi": "Delete {n} selected results?",
            "menu_help_guide": "Detailed description…",
            "menu_help_shortcuts": "Keyboard shortcuts…",
            "shortcuts_intro": "Shortcuts work while the main window is focused (Delete on the results list removes items).",
            "shortcut_open_config": "Open configuration",
            "shortcut_save": "Save result to folder",
            "shortcut_print": "Print plot",
            "shortcut_calc": "Calculate diffractogram",
            "shortcut_undo": "Undo last action",
            "shortcut_plot_settings": "Plot appearance",
            "shortcut_reset_zoom": "Reset plot zoom",
            "shortcut_delete_result": "Delete selected result",
            "shortcut_quit": "Quit",
            "shortcut_help": "Detailed description",
            "about_text": (
                "XRay MSU — powder X-ray diffractogram simulation.\n\n"
                "Version 0.1.5\n"
                "Development: XRay MSU project, Lomonosov Moscow State University.\n\n"
                "Pipeline: crystal → reflections → profile convolution.\n"
                "Help → Keyboard shortcuts (Ctrl+O, F5, Ctrl+S, etc.)."
            ),
            "about_detailed_text": (
                "XRay MSU simulates a powder X-ray diffraction pattern from a crystal structure.\n\n"
                "Author / development: Merkulov Ilya merkuloviv@my.msu.ru / XRay MSU project (Department of Solid State Physics, "
                "Lomonosov Moscow State University).\n"
                "Version 0.1.5\n\n"
                "1. Calculation pipeline\n"
                "Unit-cell parameters and fractional atomic coordinates define metric tensors G "
                "and G*. For each reflection (hkl) the program computes d, structure factor F, "
                "multiplicity M, Lorentz L and polarization P factors. Peak intensities "
                "I = S·M·L·P·|F|² are convolved with a line profile (bar, Gaussian, Lorentz, "
                "pseudo-Voigt). Line width follows Caglioti U, V, W.\n\n"
                "2. Main window\n"
                "Input form on the left, I(2θ) plot on the right. Load YAML/JSON configs via "
                "File or the preset list. Multiple runs can be overlaid, exported, or removed.\n\n"
                "3. Centering and symmetry\n"
                "Cell type P/I/F/C/A/B expands atoms in fractional coordinates when no space "
                "group number is set. Crystal system presets constrain cell angles and lengths.\n\n"
                "4. Two wavelengths\n"
                "Optional second wavelength with intensity ratio; curves are summed on one plot.\n\n"
                "5. Export\n"
                "Reflection TXT, YAML config, powder/cell PNG, G and G* CSV.\n\n"
                "6. Keyboard shortcuts\n"
                "Ctrl+O open config; Ctrl+S save; Ctrl+P print; F5 or Ctrl+Enter calculate; "
                "Ctrl+Z undo; Ctrl+G plot appearance; Ctrl+R reset zoom; Delete / Ctrl+Delete "
                "remove result; Ctrl+Q quit; F1 this guide. Full list: Help → Keyboard shortcuts.\n\n"
                "Full physical model: see doc/README-overview.md in the repository."
            ),
        },
    }
