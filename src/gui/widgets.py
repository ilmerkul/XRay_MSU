"""Фрагмент GUI: WidgetsMixin."""

import tkinter as tk
from tkinter import ttk

from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
from matplotlib.widgets import RectangleSelector



class WidgetsMixin:
    def create_widgets(self):
        """Создаёт все виджеты главного окна: форму, график и панель результатов."""
        # tk.PanedWindow: есть minsize/paneconfigure; ttk.Panedwindow — другой API
        main_paned = tk.PanedWindow(self.root, orient=tk.HORIZONTAL)
        main_paned.pack(fill=tk.BOTH, expand=True)
        self._main_paned = main_paned

        scroll_outer = ttk.Frame(main_paned)
        plot_outer = ttk.Frame(main_paned)
        self._plot_outer = plot_outer
        main_paned.add(scroll_outer, stretch="always", minsize=440)
        main_paned.add(plot_outer, stretch="always", minsize=360)

        plot_frame = ttk.LabelFrame(
            plot_outer,
            text=self.tr("plot_area"),
            padding=(8, 6),
            style="Card.TLabelframe",
        )
        self._plot_graph_frame = plot_frame

        scroll_canvas = tk.Canvas(scroll_outer, highlightthickness=0)
        vsb = ttk.Scrollbar(
            scroll_outer, orient="vertical", command=scroll_canvas.yview
        )
        scroll_canvas.configure(yscrollcommand=vsb.set)
        vsb.pack(side=tk.RIGHT, fill=tk.Y)
        scroll_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self._scroll_canvas = scroll_canvas

        self.form_container = ttk.Frame(scroll_canvas)
        inner_win = scroll_canvas.create_window(
            (0, 0), window=self.form_container, anchor="nw"
        )

        def _on_inner_configure(_event=None):
            """Обновляет scrollregion при изменении размера формы.

            Args:
                _event: Событие ``Configure`` (не используется).
            """
            scroll_canvas.configure(scrollregion=scroll_canvas.bbox("all"))

        def _on_scroll_canvas_configure(event):
            """Подгоняет ширину внутреннего фрейма под ширину canvas.

            Args:
                event: Событие изменения размера canvas.
            """
            scroll_canvas.itemconfigure(inner_win, width=event.width)

        self.form_container.bind("<Configure>", _on_inner_configure)

        scroll_canvas.bind("<Configure>", _on_scroll_canvas_configure)

        def _on_mousewheel(event):
            """Прокручивает форму колёсиком мыши (Windows/Linux).

            Args:
                event: Событие прокрутки (``MouseWheel``, ``Button-4/5``).
            """
            if getattr(event, "num", None) == 4:
                scroll_canvas.yview_scroll(-1, "units")
            elif getattr(event, "num", None) == 5:
                scroll_canvas.yview_scroll(1, "units")
            elif getattr(event, "delta", 0):
                scroll_canvas.yview_scroll(int(-event.delta / 120), "units")

        scroll_canvas.bind("<MouseWheel>", _on_mousewheel)
        scroll_canvas.bind("<Button-4>", _on_mousewheel)
        scroll_canvas.bind("<Button-5>", _on_mousewheel)
        self.form_container.bind("<MouseWheel>", _on_mousewheel)
        self.form_container.bind("<Button-4>", _on_mousewheel)
        self.form_container.bind("<Button-5>", _on_mousewheel)

        # Фрейм выбора конфига
        config_frame = ttk.LabelFrame(
            self.form_container,
            text=self.tr("config_frame"),
            padding=(14, 12),
            style="Card.TLabelframe",
        )
        config_frame.pack(fill="x", padx=14, pady=(12, 6))

        ttk.Label(config_frame, text=self.tr("select_config")).grid(
            row=0, column=0, sticky="e", padx=5, pady=2
        )
        self.config_combo = ttk.Combobox(
            config_frame, state="readonly", width=self.input_width
        )
        self.config_combo.grid(row=0, column=1, sticky="ew", padx=5, pady=2)
        self.config_combo.bind("<<ComboboxSelected>>", self.on_config_select)
        config_frame.grid_columnconfigure(1, weight=1)

        config_btns = ttk.Frame(config_frame)
        config_btns.grid(row=1, column=0, columnspan=3, sticky="w", padx=5, pady=(4, 0))
        ttk.Button(
            config_btns,
            text=self.tr("add_config_file"),
            command=self._add_config_file_dialog,
        ).pack(side=tk.LEFT, padx=(0, 6))
        ttk.Button(
            config_btns,
            text=self.tr("remove_config"),
            command=self._remove_config_from_list,
        ).pack(side=tk.LEFT)

        # Кристаллографические параметры
        crystal_frame = ttk.LabelFrame(
            self.form_container,
            text=self.tr("crystal_params"),
            padding=(14, 12),
            style="Card.TLabelframe",
        )
        crystal_frame.pack(fill="x", padx=14, pady=6)
        for c in range(4):
            crystal_frame.grid_columnconfigure(c, weight=1)

        row = 0
        name_row = ttk.Frame(crystal_frame)
        name_row.grid(row=row, column=0, columnspan=4, sticky="ew")
        name_inner = ttk.Frame(name_row)
        name_inner.pack(anchor="center", pady=2)
        ttk.Label(name_inner, text=self.tr("name")).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Entry(name_inner, textvariable=self.name_var, width=self.input_width).pack(
            side=tk.LEFT
        )
        row += 1

        cell_mode_row = ttk.Frame(crystal_frame)
        cell_mode_row.grid(
            row=row, column=0, columnspan=4, sticky="ew", padx=5, pady=(4, 2)
        )
        cell_mode_inner = ttk.Frame(cell_mode_row)
        cell_mode_inner.pack(anchor="center")

        bravais_block = ttk.Frame(cell_mode_inner)
        bravais_block.pack(side=tk.LEFT, padx=(0, 20))
        ttk.Label(bravais_block, text=self.tr("centering")).pack(anchor="center")
        bravais_combo = ttk.Combobox(
            bravais_block,
            textvariable=self.bravais_centering_var,
            values=["P", "I", "F", "C", "A", "B"],
            state="readonly",
            width=10,
        )
        bravais_combo.pack(anchor="center", pady=(4, 0))
        self._register_form_undo_combobox(bravais_combo, lambda _e=None: None)

        system_block = ttk.Frame(cell_mode_inner)
        system_block.pack(side=tk.LEFT)
        ttk.Label(system_block, text=self.tr("system")).pack(anchor="center")
        lattice_combo = ttk.Combobox(
            system_block,
            textvariable=self.lattice_family_var,
            values=self._lattice_labels(),
            state="readonly",
            width=12,
        )
        lattice_combo.pack(anchor="center", pady=(4, 0))
        self._register_form_undo_combobox(
            lattice_combo, self._on_lattice_family_selected
        )
        row += 1

        self._cell_entries = {}
        ttk.Label(crystal_frame, text=self.tr("a_axis")).grid(
            row=row, column=0, sticky="e", padx=5, pady=2
        )
        self._cell_entries["a"] = ttk.Entry(
            crystal_frame, textvariable=self.a_var, width=self.input_width
        )
        self._cell_entries["a"].grid(row=row, column=1, sticky="w", padx=5, pady=2)
        ttk.Label(crystal_frame, text=self.tr("alpha_angle")).grid(
            row=row, column=2, sticky="e", padx=(16, 5), pady=2
        )
        self._cell_entries["alpha"] = ttk.Entry(
            crystal_frame, textvariable=self.alpha_var, width=self.input_width
        )
        self._cell_entries["alpha"].grid(row=row, column=3, sticky="w", padx=5, pady=2)
        row += 1

        ttk.Label(crystal_frame, text=self.tr("b_axis")).grid(
            row=row, column=0, sticky="e", padx=5, pady=2
        )
        self._cell_entries["b"] = ttk.Entry(
            crystal_frame, textvariable=self.b_var, width=self.input_width
        )
        self._cell_entries["b"].grid(row=row, column=1, sticky="w", padx=5, pady=2)
        ttk.Label(crystal_frame, text=self.tr("beta_angle")).grid(
            row=row, column=2, sticky="e", padx=(16, 5), pady=2
        )
        self._cell_entries["beta"] = ttk.Entry(
            crystal_frame, textvariable=self.beta_var, width=self.input_width
        )
        self._cell_entries["beta"].grid(row=row, column=3, sticky="w", padx=5, pady=2)
        row += 1

        ttk.Label(crystal_frame, text=self.tr("c_axis")).grid(
            row=row, column=0, sticky="e", padx=5, pady=2
        )
        self._cell_entries["c"] = ttk.Entry(
            crystal_frame, textvariable=self.c_var, width=self.input_width
        )
        self._cell_entries["c"].grid(row=row, column=1, sticky="w", padx=5, pady=2)
        ttk.Label(crystal_frame, text=self.tr("gamma_angle")).grid(
            row=row, column=2, sticky="e", padx=(16, 5), pady=2
        )
        self._cell_entries["gamma"] = ttk.Entry(
            crystal_frame, textvariable=self.gamma_var, width=self.input_width
        )
        self._cell_entries["gamma"].grid(row=row, column=3, sticky="w", padx=5, pady=2)
        row += 1

        self._apply_lattice_constraints()

        # Таблица атомов (сворачиваемая секция)
        atoms_frame = self._create_collapsible_section(
            self.form_container, self.tr("atoms"), expanded=False
        )
        self.atoms_frame = atoms_frame

        atoms_tools = ttk.Frame(atoms_frame)
        atoms_tools.grid(row=0, column=0, columnspan=5, sticky="w", pady=(0, 4))
        ttk.Checkbutton(
            atoms_tools,
            text=self.tr("show_biso"),
            variable=self.show_biso_var,
            command=self._on_toggle_biso_column,
            style="Inset.TCheckbutton",
        ).pack(side=tk.LEFT)

        self.atom_widgets = []
        self._build_atom_headers(atoms_frame)
        self.refresh_atoms_table(atoms_frame)

        btn_frame = ttk.Frame(atoms_frame)
        btn_frame.grid(row=100, column=0, columnspan=5, pady=5)
        ttk.Button(btn_frame, text=self.tr("add_atom"), command=self.add_atom).pack(
            side=tk.LEFT, padx=5
        )
        ttk.Button(
            btn_frame, text=self.tr("remove_atom"), command=self.remove_atom
        ).pack(side=tk.LEFT, padx=5)

        # Параметры дифракции (сворачиваемая секция)
        pattern_frame = self._create_collapsible_section(
            self.form_container, self.tr("pattern_params"), expanded=False
        )

        self._pattern_entry_widgets = []
        row = 0
        ttk.Label(pattern_frame, text=self.tr("wavelength1")).grid(
            row=row, column=0, sticky="e", padx=5, pady=2
        )
        wl1_entry = ttk.Entry(
            pattern_frame, textvariable=self.wavelength_var, width=self.input_width
        )
        wl1_entry.grid(row=row, column=1, sticky="w", padx=5, pady=2)
        self._pattern_entry_widgets.append(wl1_entry)
        row += 1

        ttk.Checkbutton(
            pattern_frame,
            text=self.tr("use_wl2"),
            variable=self.wavelength2_enabled_var,
            command=self._on_wavelength2_toggled,
            style="Inset.TCheckbutton",
        ).grid(row=row, column=0, columnspan=2, sticky="w", padx=5, pady=2)
        row += 1

        self._wl2_fields_frame = ttk.Frame(pattern_frame)
        self._wl2_fields_frame.grid(row=row, column=0, columnspan=2, sticky="ew")
        self._wl2_fields_frame.grid_columnconfigure(1, weight=1)

        ttk.Label(self._wl2_fields_frame, text=self.tr("wavelength2")).grid(
            row=0, column=0, sticky="e", padx=5, pady=2
        )
        wl2_entry = ttk.Entry(
            self._wl2_fields_frame,
            textvariable=self.wavelength2_var,
            width=self.input_width,
        )
        wl2_entry.grid(row=0, column=1, sticky="w", padx=5, pady=2)
        self._pattern_entry_widgets.append(wl2_entry)

        ttk.Label(self._wl2_fields_frame, text=self.tr("wl2_ratio")).grid(
            row=1, column=0, sticky="e", padx=5, pady=2
        )
        wl2_ratio_entry = ttk.Entry(
            self._wl2_fields_frame,
            textvariable=self.wl2_intensity_ratio_var,
            width=self.input_width,
        )
        wl2_ratio_entry.grid(row=1, column=1, sticky="w", padx=5, pady=2)
        self._pattern_entry_widgets.append(wl2_ratio_entry)
        self._toggle_wavelength2_fields()
        row += 1

        ttk.Label(pattern_frame, text=self.tr("tth_range")).grid(
            row=row, column=0, sticky="e", padx=5, pady=2
        )
        range_frame = ttk.Frame(pattern_frame)
        range_frame.grid(row=row, column=1, sticky="w", padx=5, pady=2)
        tth_start_entry = ttk.Entry(
            range_frame, textvariable=self.tth_start_var, width=8
        )
        tth_start_entry.pack(side=tk.LEFT)
        ttk.Label(range_frame, text="-").pack(side=tk.LEFT)
        tth_end_entry = ttk.Entry(range_frame, textvariable=self.tth_end_var, width=8)
        tth_end_entry.pack(side=tk.LEFT)
        ttk.Label(range_frame, text=self.tr("step")).pack(side=tk.LEFT)
        tth_step_entry = ttk.Entry(range_frame, textvariable=self.tth_step_var, width=8)
        tth_step_entry.pack(side=tk.LEFT)
        self._pattern_entry_widgets.extend(
            [tth_start_entry, tth_end_entry, tth_step_entry]
        )
        row += 1

        ttk.Label(pattern_frame, text=self.tr("profile")).grid(
            row=row, column=0, sticky="e", padx=5, pady=2
        )
        self._profile_combo = ttk.Combobox(
            pattern_frame,
            textvariable=self.profile_var,
            values=self._profile_labels(),
            width=self.input_width,
        )
        self._profile_combo.grid(row=row, column=1, sticky="w", padx=5, pady=2)
        self._register_form_undo_combobox(
            self._profile_combo, self._on_profile_selected
        )
        row += 1

        self._eta_label = ttk.Label(pattern_frame, text=self.tr("pseudo_voigt_eta"))
        self._eta_label.grid(row=row, column=0, sticky="e", padx=5, pady=2)
        self._eta_entry = ttk.Entry(
            pattern_frame, textvariable=self.eta_var, width=self.input_width
        )
        self._eta_entry.grid(row=row, column=1, sticky="w", padx=5, pady=2)
        self._pattern_entry_widgets.append(self._eta_entry)
        row += 1

        self._caglioti_label = ttk.Label(pattern_frame, text=self.tr("caglioti"))
        self._caglioti_label.grid(row=row, column=0, sticky="e", padx=5, pady=2)
        self._caglioti_frame = ttk.Frame(pattern_frame)
        self._caglioti_frame.grid(row=row, column=1, sticky="w", padx=5, pady=2)
        self._caglioti_entries = []
        for label, var in (("U", self.U_var), ("V", self.V_var), ("W", self.W_var)):
            ttk.Label(self._caglioti_frame, text=label).pack(side=tk.LEFT, padx=(0, 2))
            entry = ttk.Entry(self._caglioti_frame, textvariable=var, width=10)
            entry.pack(side=tk.LEFT, padx=(0, 8))
            self._caglioti_entries.append(entry)
        row += 1

        ttk.Label(pattern_frame, text=self.tr("thetam")).grid(
            row=row, column=0, sticky="e", padx=5, pady=2
        )
        thetam_entry = ttk.Entry(
            pattern_frame, textvariable=self.thetam_deg_var, width=self.input_width
        )
        thetam_entry.grid(row=row, column=1, sticky="w", padx=5, pady=2)
        self._pattern_entry_widgets.append(thetam_entry)
        row += 1

        self._on_profile_selected()

        actions_row = ttk.Frame(self.form_container)
        actions_row.pack(pady=(14, 8))
        ttk.Button(
            actions_row,
            text=self.tr("generate_pattern"),
            command=self.generate_pattern,
            style="Primary.TButton",
        ).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(
            actions_row,
            text=self.tr("reset_zoom"),
            command=self._reset_zoom,
            style="Secondary.TButton",
        ).pack(side=tk.LEFT)

        fig_h = 6.0
        fig_w = fig_h * self._plot_aspect
        self.figure = Figure(figsize=(fig_w, fig_h), dpi=int(self.plot_dpi_var.get()))
        self.ax = self.figure.add_subplot(111)
        self.ax.set_aspect("auto")
        self.canvas = FigureCanvasTkAgg(self.figure, master=plot_frame)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        plot_frame.bind("<Configure>", self._resize_plot_figure)

        results_panel = ttk.LabelFrame(
            plot_outer,
            text=self.tr("calc_results"),
            padding=(10, 8),
            style="Card.TLabelframe",
        )

        export_btns = ttk.Frame(results_panel)
        export_btns.pack(fill=tk.X, pady=(0, 6))
        ttk.Button(
            export_btns,
            text=self.tr("delete_calc_result"),
            command=self._delete_selected_calc_results,
            style="Secondary.TButton",
        ).pack(side=tk.LEFT)
        ttk.Button(
            export_btns,
            text=self.tr("print_pattern"),
            command=self._print_pattern,
            style="Secondary.TButton",
        ).pack(side=tk.RIGHT)
        ttk.Button(
            export_btns,
            text=self.tr("save_to_folder"),
            command=self._save_selected_result,
            style="Primary.TButton",
        ).pack(side=tk.RIGHT, padx=(0, 8))

        list_row = ttk.Frame(results_panel)
        list_row.pack(fill=tk.X, pady=(0, 4))
        list_scroll = ttk.Scrollbar(list_row, orient=tk.VERTICAL)
        self._calc_listbox = tk.Listbox(
            list_row,
            height=3,
            exportselection=False,
            selectmode=tk.EXTENDED,
            yscrollcommand=list_scroll.set,
            font=self.input_font,
        )
        list_scroll.config(command=self._calc_listbox.yview)
        self._calc_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        list_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self._calc_listbox.bind("<<ListboxSelect>>", self._on_calc_result_selected)
        self._calc_listbox.bind("<Motion>", self._on_calc_list_motion)
        self._calc_listbox.bind("<Leave>", self._on_calc_list_leave)
        self._calc_listbox.bind("<Delete>", self._delete_selected_calc_results)
        ttk.Label(
            results_panel,
            text=self.tr("calc_results_multi_hint"),
            style="Muted.TLabel",
        ).pack(anchor="w", pady=(0, 4))

        save_opts = ttk.LabelFrame(
            results_panel,
            text=self.tr("save_files_group"),
            padding=(8, 6),
            style="Inner.TLabelframe",
        )
        save_opts.pack(fill=tk.X, pady=(0, 4))
        opts_inner = ttk.Frame(save_opts)
        opts_inner.pack(fill=tk.X)
        save_labels = {
            "txt": "save_file_txt",
            "angles_int": "save_file_angles_int",
            "config": "save_file_config",
            "powder_png": "save_file_powder_png",
            "cell_png": "save_file_cell_png",
            "G_csv": "save_file_G_csv",
            "Gstar_csv": "save_file_Gstar_csv",
        }
        self._save_option_vars = {}
        other_keys = tuple(
            k for k in self.SAVE_OUTPUT_KEYS if k not in self.SAVE_OUTPUT_PRIMARY_KEYS
        )
        for col, key in enumerate(self.SAVE_OUTPUT_PRIMARY_KEYS):
            cached = self._save_option_state_cache.get(key)
            if cached is None and key == "config":
                cached = self._save_option_state_cache.get("json")
            default = key in self.SAVE_OUTPUT_DEFAULT_KEYS
            var = tk.BooleanVar(value=default if cached is None else cached)
            self._save_option_vars[key] = var
            ttk.Checkbutton(
                opts_inner,
                text=self.tr(save_labels[key]),
                variable=var,
                style="CardInner.TCheckbutton",
            ).grid(row=0, column=col, sticky="w", padx=6, pady=2)
        for idx, key in enumerate(other_keys):
            cached = self._save_option_state_cache.get(key)
            if cached is None and key == "config":
                cached = self._save_option_state_cache.get("json")
            default = key in self.SAVE_OUTPUT_DEFAULT_KEYS
            var = tk.BooleanVar(value=default if cached is None else cached)
            self._save_option_vars[key] = var
            ttk.Checkbutton(
                opts_inner,
                text=self.tr(save_labels[key]),
                variable=var,
                style="CardInner.TCheckbutton",
            ).grid(row=1 + idx // 2, column=idx % 2, sticky="w", padx=6, pady=2)

        results_panel.pack(fill=tk.X, side=tk.BOTTOM, padx=8, pady=(6, 8))
        plot_frame.pack(fill=tk.BOTH, expand=True)
        self._refresh_calc_results_list()
        self._zoom_selector = RectangleSelector(
            self.ax,
            self._on_zoom_select,
            useblit=True,
            button=[1],
            minspanx=0.05,
            minspany=0.05,
            spancoords="data",
            interactive=False,
        )
        self._zoom_reset_cid = self.canvas.mpl_connect(
            "button_press_event", self._on_zoom_reset_click
        )

        self.root.after_idle(self._set_initial_sash)
        self._register_form_undo_widgets()
        self._create_menu_bar()

    def _register_form_undo_widgets(self) -> None:
        """Подключает отмену к полям ввода формы."""
        for entry in getattr(self, "_cell_entries", {}).values():
            self._register_form_undo_widget(entry)
        for entry in getattr(self, "_pattern_entry_widgets", []):
            self._register_form_undo_widget(entry)
        for entry in getattr(self, "_caglioti_entries", []):
            self._register_form_undo_widget(entry)
        for widgets in getattr(self, "atom_widgets", []):
            for widget in widgets:
                if widget is not None:
                    self._register_form_undo_widget(widget)

    def _on_wavelength2_toggled(self) -> None:
        """Переключает вторую длину волны с поддержкой отмены."""
        if not self._undo_restoring:
            self._push_undo_snapshot()
        self._toggle_wavelength2_fields()
        if not self._undo_restoring:
            self._commit_form_state()

    def _set_initial_sash(self):
        """Задаёт начальную позицию разделителя панелей и размер графика."""
        try:
            self._main_paned.update_idletasks()
            w = self._main_paned.winfo_width()
            if w > 300:
                left_width = max(440, min(int(w * 0.38), 680))
                self._main_paned.sashpos(0, left_width)
            self._resize_plot_figure()
        except (tk.TclError, AttributeError):
            pass

    def _resize_plot_figure(self, _event=None):
        """Подгоняет размер фигуры matplotlib под область графика.

        Args:
            _event: Событие изменения размера фрейма (не используется).
        """
        frame = self._plot_graph_frame
        if frame is None:
            return
        try:
            pw = max(frame.winfo_width() - 12, 200)
            ph = max(frame.winfo_height() - 36, 160)
            dpi = self.figure.get_dpi()
            w_in = pw / dpi
            h_in = ph / dpi
            if w_in / h_in < self._plot_aspect:
                w_in = h_in * self._plot_aspect
            else:
                h_in = w_in / self._plot_aspect
            self.figure.set_size_inches(w_in, h_in, forward=True)
            self.figure.tight_layout(pad=1.0)
            self.canvas.draw_idle()
        except (tk.TclError, AttributeError, ValueError):
            pass

    def _toggle_wavelength2_fields(self):
        """Показывает или скрывает поля второй длины волны."""
        if self._wl2_fields_frame is None:
            return
        if self.wavelength2_enabled_var.get():
            self._wl2_fields_frame.grid()
        else:
            self._wl2_fields_frame.grid_remove()

    def _on_profile_selected(self, _event=None):
        """Показывает η и Caglioti только для подходящих профилей."""
        key = self._profile_key()
        show_eta = key == "pseudo-voigt"
        show_caglioti = key in ("gaussian", "lorentzian", "pseudo-voigt")

        def _set_visible(widget, visible: bool) -> None:
            if widget is None:
                return
            if visible:
                widget.grid()
            else:
                widget.grid_remove()

        _set_visible(self._eta_label, show_eta)
        _set_visible(self._eta_entry, show_eta)
        _set_visible(self._caglioti_label, show_caglioti)
        _set_visible(self._caglioti_frame, show_caglioti)
        if self._eta_entry is not None:
            self._eta_entry.configure(state="normal" if show_eta else "disabled")

    def _create_collapsible_section(self, parent, title: str, expanded: bool = True):
        """Создаёт сворачиваемую секцию формы с кнопкой-заголовком.

        Args:
            parent: Родительский виджет.
            title: Заголовок секции (ключ для ``_toggle_section``).
            expanded: Если ``True``, содержимое изначально развёрнуто.

        Returns:
            Фрейм с содержимым секции.
        """
        section = ttk.Frame(parent)
        section.pack(fill="x", padx=14, pady=6)

        btn = ttk.Button(
            section,
            command=lambda key=title: self._toggle_section(key),
            style="Section.TButton",
        )
        btn.pack(fill="x")

        content = ttk.Frame(section, padding=(14, 10), style="Inset.TFrame")
        if expanded:
            content.pack(fill="x", pady=(6, 0))

        self._section_buttons[title] = btn
        self._section_content[title] = content
        self._update_section_button_text(title)
        return content

    def _toggle_section(self, key: str):
        """Сворачивает или разворачивает секцию формы.

        Args:
            key: Заголовок секции из ``_section_content``.
        """
        content = self._section_content.get(key)
        if content is None:
            return
        if content.winfo_manager():
            content.pack_forget()
        else:
            content.pack(fill="x", pady=(6, 0))
        self._update_section_button_text(key)

    def _update_section_button_text(self, key: str):
        """Обновляет текст кнопки секции (маркер ▼/► и заголовок).

        Args:
            key: Заголовок секции.
        """
        btn = self._section_buttons.get(key)
        content = self._section_content.get(key)
        if btn is None or content is None:
            return
        marker = "▼" if content.winfo_manager() else "►"
        btn.configure(text=f"{marker} {key}")
