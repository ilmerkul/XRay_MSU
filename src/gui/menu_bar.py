"""Верхнее меню: File, View, Help."""

from __future__ import annotations

import os
import tkinter as tk
from tkinter import filedialog, messagebox, ttk


class MenuBarMixin:
    def _create_menu_bar(self) -> None:
        """Создаёт или пересоздаёт строку меню (после смены языка)."""
        self._menubar = tk.Menu(self.root)
        self.root.config(menu=self._menubar)

        file_menu = tk.Menu(self._menubar, tearoff=0)
        self._menubar.add_cascade(label=self.tr("menu_file"), menu=file_menu)
        file_menu.add_command(
            label=self.tr("menu_open_config"),
            command=self._open_config_file,
            accelerator="Ctrl+O",
        )
        file_menu.add_command(
            label=self.tr("menu_add_config"),
            command=self._add_config_file_dialog,
        )
        file_menu.add_command(
            label=self.tr("generate_pattern"),
            command=self.generate_pattern,
            accelerator="F5",
        )
        file_menu.add_command(
            label=self.tr("save_to_folder"),
            command=self._save_selected_result,
            accelerator="Ctrl+S",
        )
        file_menu.add_command(
            label=self.tr("print_pattern"),
            command=self._print_pattern,
            accelerator="Ctrl+P",
        )
        file_menu.add_separator()
        file_menu.add_command(
            label=self.tr("menu_exit"),
            command=self.root.quit,
            accelerator="Ctrl+Q",
        )

        edit_menu = tk.Menu(self._menubar, tearoff=0)
        self._menubar.add_cascade(label=self.tr("menu_edit"), menu=edit_menu)
        edit_menu.add_command(
            label=self.tr("menu_undo"),
            command=self._undo_last_action,
            accelerator="Ctrl+Z",
            state=tk.DISABLED,
        )
        edit_menu.add_command(
            label=self.tr("delete_calc_result"),
            command=self._delete_selected_calc_results,
            accelerator="Del",
        )
        self._undo_menu = edit_menu

        view_menu = tk.Menu(self._menubar, tearoff=0)
        self._menubar.add_cascade(label=self.tr("menu_view"), menu=view_menu)

        lang_menu = tk.Menu(view_menu, tearoff=0)
        view_menu.add_cascade(label=self.tr("menu_language"), menu=lang_menu)
        for code, label in self.LANGUAGE_LABELS.items():
            lang_menu.add_radiobutton(
                label=label,
                variable=self.language_var,
                value=code,
                command=self._on_language_selected,
            )

        theme_menu = tk.Menu(view_menu, tearoff=0)
        view_menu.add_cascade(label=self.tr("menu_theme"), menu=theme_menu)
        for key in ("light", "dark"):
            theme_menu.add_radiobutton(
                label=self._theme_label(key),
                variable=self.theme_var,
                value=self._theme_label(key),
                command=self._on_theme_selected,
            )

        view_menu.add_separator()
        view_menu.add_radiobutton(
            label=self.tr("label_reflection_hide"),
            variable=self.label_reflection_mode_var,
            value="none",
            command=self._on_label_reflection_mode_changed,
        )
        view_menu.add_radiobutton(
            label=self.tr("label_reflection_angles"),
            variable=self.label_reflection_mode_var,
            value="angles",
            command=self._on_label_reflection_mode_changed,
        )
        view_menu.add_radiobutton(
            label=self.tr("label_reflection_angles_hkl"),
            variable=self.label_reflection_mode_var,
            value="both",
            command=self._on_label_reflection_mode_changed,
        )
        view_menu.add_separator()
        view_menu.add_command(
            label=self.tr("menu_plot_settings"),
            command=self._open_plot_settings_dialog,
            accelerator="Ctrl+G",
        )
        view_menu.add_command(
            label=self.tr("reset_zoom"),
            command=self._reset_zoom,
            accelerator="Ctrl+R",
        )

        help_menu = tk.Menu(self._menubar, tearoff=0)
        self._menubar.add_cascade(label=self.tr("menu_help"), menu=help_menu)
        help_menu.add_command(
            label=self.tr("menu_about"), command=self._show_about_dialog
        )
        help_menu.add_command(
            label=self.tr("menu_help_guide"),
            command=self._show_help_guide_dialog,
            accelerator="F1",
        )
        help_menu.add_command(
            label=self.tr("menu_help_shortcuts"), command=self._show_shortcuts_dialog
        )

        self._bind_app_shortcuts()
        self._update_undo_menu_state()

    def _open_config_file(self) -> None:
        """Открывает YAML/JSON конфиг и загружает параметры в форму."""
        path = filedialog.askopenfilename(
            title=self.tr("menu_open_config"),
            filetypes=[
                (self.tr("menu_config_filter"), "*.yaml *.yml *.json *.txt"),
                (self.tr("menu_all_files"), "*.*"),
            ],
        )
        if not path:
            return
        if not self._is_config_file(path):
            messagebox.showerror(
                self.tr("input_error_title"),
                self.tr("config_invalid_path").format(path=path),
            )
            return
        try:
            config = self.parse_config_file(path)
            self.apply_config(config)
            stem = os.path.splitext(os.path.basename(path))[0]
            if stem in self.config_files:
                self.config_combo.set(stem)
            else:
                self.config_combo.set("")
            messagebox.showinfo(
                self.tr("success_title"),
                self.tr("config_loaded").format(name=stem, path=path),
            )
        except Exception as exc:
            messagebox.showerror(
                self.tr("error_title"),
                self.tr("failed_load_config").format(error=str(exc)),
            )

    def _show_about_dialog(self) -> None:
        messagebox.showinfo(
            self.tr("menu_about"),
            self.tr("about_text"),
        )

    def _show_help_guide_dialog(self) -> None:
        """Подробное описание программы и расчётной модели."""
        if getattr(self, "_help_guide_win", None) is not None:
            try:
                if self._help_guide_win.winfo_exists():
                    self._help_guide_win.lift()
                    return
            except tk.TclError:
                pass

        theme = self._current_theme()
        win = tk.Toplevel(self.root)
        self._help_guide_win = win
        win.title(self.tr("menu_help_guide"))
        win.transient(self.root)
        win.geometry("640x520")
        win.configure(bg=theme.bg)

        outer = ttk.Frame(win, padding=(12, 10))
        outer.pack(fill=tk.BOTH, expand=True)

        text_frame = ttk.Frame(outer)
        text_frame.pack(fill=tk.BOTH, expand=True)

        text = tk.Text(
            text_frame,
            wrap=tk.WORD,
            font=self.input_font,
            bg=theme.tooltip_bg,
            fg=theme.tooltip_fg,
            relief=tk.FLAT,
            padx=12,
            pady=10,
            highlightthickness=1,
            highlightbackground=theme.border_soft,
        )
        scroll = ttk.Scrollbar(text_frame, orient=tk.VERTICAL, command=text.yview)
        text.configure(yscrollcommand=scroll.set)
        scroll.pack(side=tk.RIGHT, fill=tk.Y)
        text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        text.insert("1.0", self.tr("about_detailed_text"))
        text.configure(state=tk.DISABLED)

        ttk.Button(
            outer,
            text=self.tr("plot_settings_close"),
            command=win.destroy,
            style="Secondary.TButton",
        ).pack(anchor="e", pady=(8, 0))

        win.protocol("WM_DELETE_WINDOW", win.destroy)

    def _open_plot_settings_dialog(self) -> None:
        """Диалог настройки вида графика matplotlib."""
        if getattr(self, "_plot_settings_win", None) is not None:
            try:
                if self._plot_settings_win.winfo_exists():
                    self._plot_settings_win.lift()
                    return
            except tk.TclError:
                pass

        theme = self._current_theme()
        win = tk.Toplevel(self.root)
        self._plot_settings_win = win
        win.title(self.tr("plot_settings_title"))
        win.transient(self.root)
        win.resizable(True, True)
        win.configure(bg=theme.bg)

        outer = ttk.Frame(win, padding=(12, 10))
        outer.pack(fill=tk.BOTH, expand=True)

        canvas = tk.Canvas(outer, highlightthickness=0, bg=theme.bg)
        scroll = ttk.Scrollbar(outer, orient=tk.VERTICAL, command=canvas.yview)
        canvas.configure(yscrollcommand=scroll.set)
        scroll.pack(side=tk.RIGHT, fill=tk.Y)
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        frame = ttk.Frame(canvas, padding=(8, 6))
        canvas_window = canvas.create_window((0, 0), window=frame, anchor="nw")

        def _on_frame_configure(_event=None):
            canvas.configure(scrollregion=canvas.bbox("all"))

        def _on_canvas_configure(event):
            canvas.itemconfigure(canvas_window, width=event.width)

        frame.bind("<Configure>", _on_frame_configure)
        canvas.bind("<Configure>", _on_canvas_configure)

        row = 0

        def add_entry(label_key: str, var) -> None:
            nonlocal row
            ttk.Label(frame, text=self.tr(label_key)).grid(
                row=row, column=0, sticky="e", padx=(0, 10), pady=3
            )
            ttk.Entry(frame, textvariable=var, width=10).grid(
                row=row, column=1, sticky="w", pady=3
            )
            row += 1

        def add_check(label_key: str, var) -> None:
            nonlocal row
            ttk.Checkbutton(frame, text=self.tr(label_key), variable=var).grid(
                row=row, column=0, columnspan=2, sticky="w", pady=2
            )
            row += 1

        ttk.Label(
            frame, text=self.tr("plot_settings_section_curve"), style="Muted.TLabel"
        ).grid(row=row, column=0, columnspan=2, sticky="w", pady=(0, 4))
        row += 1
        add_entry("plot_settings_line_width", self.plot_line_width_var)
        add_check("plot_settings_antialiased", self.plot_antialiased_var)
        add_entry("plot_settings_aspect", self.plot_aspect_var)
        add_entry("plot_settings_dpi", self.plot_dpi_var)
        add_entry("plot_settings_y_margin", self.plot_y_top_margin_var)
        add_entry("plot_settings_layout_pad", self.plot_layout_pad_var)

        ttk.Label(
            frame, text=self.tr("plot_settings_section_grid"), style="Muted.TLabel"
        ).grid(row=row, column=0, columnspan=2, sticky="w", pady=(8, 4))
        row += 1
        add_check("plot_settings_grid_major", self.plot_grid_major_var)
        add_entry("plot_settings_grid_major_lw", self.plot_grid_major_lw_var)
        add_entry("plot_settings_grid_major_alpha", self.plot_grid_major_alpha_var)
        add_check("plot_settings_grid_minor", self.plot_grid_minor_var)
        add_entry("plot_settings_grid_minor_lw", self.plot_grid_minor_lw_var)
        add_entry("plot_settings_grid_minor_alpha", self.plot_grid_minor_alpha_var)
        add_check("plot_settings_vlines", self.plot_vlines_var)
        add_entry("plot_settings_vline_width", self.plot_vline_width_var)
        add_entry("plot_settings_vline_alpha", self.plot_vline_alpha_var)

        ttk.Label(
            frame, text=self.tr("plot_settings_section_labels"), style="Muted.TLabel"
        ).grid(row=row, column=0, columnspan=2, sticky="w", pady=(8, 4))
        row += 1
        add_check("plot_settings_title_show", self.plot_title_show_var)
        add_entry("plot_settings_title_size", self.plot_title_size_var)
        add_entry("plot_settings_axis_label_size", self.plot_axis_label_size_var)
        add_entry("plot_settings_tick_size", self.plot_tick_label_size_var)
        add_entry("plot_settings_peak_label_size", self.plot_peak_label_size_var)
        add_check("plot_settings_legend_show", self.plot_legend_show_var)
        ttk.Label(frame, text=self.tr("plot_settings_legend_loc")).grid(
            row=row, column=0, sticky="e", padx=(0, 10), pady=3
        )
        ttk.Combobox(
            frame,
            textvariable=self.plot_legend_loc_var,
            values=list(self.PLOT_LEGEND_LOCS),
            state="readonly",
            width=14,
        ).grid(row=row, column=1, sticky="w", pady=3)
        row += 1

        ttk.Label(
            frame, text=self.tr("plot_settings_size_hint"), style="Muted.TLabel"
        ).grid(row=row, column=0, columnspan=2, sticky="w", pady=(4, 0))
        row += 1

        btns = ttk.Frame(frame)
        btns.grid(row=row, column=0, columnspan=2, sticky="e", pady=(12, 0))
        ttk.Button(
            btns,
            text=self.tr("plot_settings_apply"),
            command=lambda: self._apply_plot_settings(close=False),
            style="Primary.TButton",
        ).pack(side=tk.LEFT, padx=(0, 8))
        ttk.Button(
            btns,
            text=self.tr("plot_settings_close"),
            command=win.destroy,
            style="Secondary.TButton",
        ).pack(side=tk.LEFT)

        win.protocol("WM_DELETE_WINDOW", win.destroy)
        win.update_idletasks()
        rx = self.root.winfo_rootx()
        ry = self.root.winfo_rooty()
        rw = self.root.winfo_width()
        ww = max(win.winfo_width(), 420)
        wh = min(max(win.winfo_height(), 480), 720)
        win.geometry(f"{ww}x{wh}+{rx + max((rw - ww) // 2, 0)}+{ry + 60}")

    def _apply_plot_settings(self, *, close: bool = False) -> None:
        """Применяет параметры графика и перерисовывает текущий вид."""
        try:
            lw = float(self.plot_line_width_var.get())
            dpi = int(self.plot_dpi_var.get())
            aspect = float(self.plot_aspect_var.get())
            y_margin = float(self.plot_y_top_margin_var.get())
            layout_pad = float(self.plot_layout_pad_var.get())
            grid_major_alpha = float(self.plot_grid_major_alpha_var.get())
            grid_minor_alpha = float(self.plot_grid_minor_alpha_var.get())
            grid_major_lw = float(self.plot_grid_major_lw_var.get())
            grid_minor_lw = float(self.plot_grid_minor_lw_var.get())
            vline_width = float(self.plot_vline_width_var.get())
            vline_alpha = float(self.plot_vline_alpha_var.get())
            tick_size = int(self.plot_tick_label_size_var.get())
            axis_label_size = int(self.plot_axis_label_size_var.get())
            title_size = int(self.plot_title_size_var.get())
            peak_label_size = int(self.plot_peak_label_size_var.get())
        except (tk.TclError, ValueError):
            messagebox.showerror(
                self.tr("input_error_title"),
                self.tr("plot_settings_invalid"),
            )
            return
        if (
            lw <= 0
            or dpi < 50
            or aspect <= 0
            or y_margin <= 1.0
            or layout_pad < 0
            or not (0.0 <= grid_major_alpha <= 1.0)
            or not (0.0 <= grid_minor_alpha <= 1.0)
            or grid_major_lw <= 0
            or grid_minor_lw <= 0
            or vline_width <= 0
            or not (0.0 <= vline_alpha <= 1.0)
            or tick_size < 6
            or axis_label_size < 0
            or title_size < 0
            or peak_label_size < 0
        ):
            messagebox.showerror(
                self.tr("input_error_title"),
                self.tr("plot_settings_invalid"),
            )
            return

        if not self._undo_restoring:
            self._push_undo_snapshot()

        legend_loc = self.plot_legend_loc_var.get().strip()
        if legend_loc not in self.PLOT_LEGEND_LOCS:
            self.plot_legend_loc_var.set("upper right")

        self.plot_line_width_var.set(lw)
        self.plot_dpi_var.set(dpi)
        self.plot_aspect_var.set(aspect)
        self.plot_y_top_margin_var.set(y_margin)
        self.plot_layout_pad_var.set(layout_pad)
        self.plot_grid_major_alpha_var.set(grid_major_alpha)
        self.plot_grid_minor_alpha_var.set(grid_minor_alpha)
        self.plot_grid_major_lw_var.set(grid_major_lw)
        self.plot_grid_minor_lw_var.set(grid_minor_lw)
        self.plot_vline_width_var.set(vline_width)
        self.plot_vline_alpha_var.set(vline_alpha)
        self.plot_tick_label_size_var.set(tick_size)
        self.plot_axis_label_size_var.set(axis_label_size)
        self.plot_title_size_var.set(title_size)
        self.plot_peak_label_size_var.set(peak_label_size)
        self._plot_aspect = aspect
        try:
            self.figure.set_dpi(dpi)
        except (AttributeError, ValueError):
            pass

        selected = self._get_selected_calc_results()
        if selected:
            self._display_calc_results(selected)
        else:
            self._resize_plot_figure()

        if not self._undo_restoring:
            self._commit_form_state()

        if close and getattr(self, "_plot_settings_win", None) is not None:
            try:
                self._plot_settings_win.destroy()
            except tk.TclError:
                pass
