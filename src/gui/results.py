"""Фрагмент GUI: ResultsMixin."""

import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox

import numpy as np
import yaml

from ..model.pattern.plot import Plot
from .theme import THEMES, apply_mpl_theme, mpl_plot_xlabel
from .ui_text import ascii_ui_text

_OVERLAY_LINE_COLORS = (
    "#0b7285",
    "#c92a2a",
    "#2b8a3e",
    "#e67700",
    "#5f3dc4",
    "#1098ad",
    "#862e9c",
    "#495057",
)


class ResultsMixin:
    def _plot_tick_fontsize(self) -> int:
        v = int(self.plot_tick_label_size_var.get())
        if v > 0:
            return v
        fonts = getattr(self, "fonts", None)
        return fonts.plot_tick[1] if fonts else 10

    def _plot_axis_label_fontsize(self) -> int:
        v = int(self.plot_axis_label_size_var.get())
        if v > 0:
            return v
        fonts = getattr(self, "fonts", None)
        return fonts.plot_label[1] if fonts else 11

    def _plot_title_fontsize(self) -> int:
        v = int(self.plot_title_size_var.get())
        if v > 0:
            return v
        fonts = getattr(self, "fonts", None)
        return fonts.plot_title[1] if fonts else 12

    def _plot_peak_label_fontsize(self) -> int:
        v = int(self.plot_peak_label_size_var.get())
        if v > 0:
            return v
        return self._plot_tick_fontsize()

    def _clear_calc_plot(self) -> None:
        """Очищает график, когда в списке нет расчётов."""
        if not hasattr(self, "ax"):
            return
        self.ax.clear()
        self._peak_label_artists.clear()
        self._plot_peak_data = None
        self._hkl_hover_peaks = None
        self._hkl_hover_annot = None
        self._full_xlim = None
        self._full_ylim = None
        theme = self._current_theme()
        apply_mpl_theme(self.figure, self.ax, theme, getattr(self, "fonts", None))
        self.canvas.draw()

    def _delete_selected_calc_results(self, _event=None):
        """Удаляет выбранные расчёты из списка."""
        indices = sorted(getattr(self, "_selected_calc_indices", []), reverse=True)
        if not indices:
            messagebox.showwarning(
                self.tr("warning_title"), self.tr("delete_calc_none")
            )
            return "break" if _event is not None else None
        first_deleted = min(indices)
        if len(indices) == 1:
            name = self._calc_results[indices[0]]["name"]
            msg = self.tr("delete_calc_confirm").format(name=name)
        else:
            msg = self.tr("delete_calc_confirm_multi").format(n=len(indices))
        if not messagebox.askyesno(self.tr("delete_calc_result"), msg):
            return "break" if _event is not None else None

        if not self._undo_restoring:
            self._push_undo_snapshot()
        self._hide_calc_list_tooltip()
        for i in indices:
            if 0 <= i < len(self._calc_results):
                del self._calc_results[i]
        self._selected_calc_indices = []
        self._refresh_calc_results_list()
        if self._calc_results:
            new_idx = min(first_deleted, len(self._calc_results) - 1)
            self._select_calc_result_index(new_idx)
        else:
            self._clear_calc_plot()
        if not self._undo_restoring:
            self._commit_form_state()
        return "break" if _event is not None else None

    def _format_calc_result_label(self, index: int, result: dict) -> str:
        """Краткая подпись расчёта для listbox."""
        name = result["name"]
        wl_part = ", ".join(f"{w:.4f}" for w in result["wavelengths"])
        if len(result["wavelengths"]) > 1:
            wl_part += f" (x{result['wl2_ratio']:g})"
        tth = (
            f"2θ {result['tth_start']:.0f}-{result['tth_end']:.0f}"
            f" h{result['tth_step']:.3g}"
        )
        profile = result["profile_label"]
        text = f"#{index + 1} {name} | λ {wl_part} | {tth} | {profile}"
        return ascii_ui_text(text)

    def _calc_result_tooltip(self, result: dict) -> str:
        """Многострочная подсказка с параметрами расчёта."""
        p0 = result["patterns"][0]
        crystal = p0.crystal
        lines = [
            self.tr("calc_result_tip_name").format(name=result["name"]),
            self.tr("calc_result_tip_wl").format(
                wl=", ".join(f"{w:.4f}" for w in result["wavelengths"])
            ),
            self.tr("calc_result_tip_tth").format(
                start=result["tth_start"],
                end=result["tth_end"],
                step=result["tth_step"],
            ),
            self.tr("calc_result_tip_profile").format(profile=result["profile_label"]),
            self.tr("calc_result_tip_cell").format(
                a=crystal.a, b=crystal.b, c=crystal.c
            ),
            self.tr("calc_result_tip_angles").format(
                alpha=float(np.degrees(crystal.alpha)),
                beta=float(np.degrees(crystal.beta)),
                gamma=float(np.degrees(crystal.gamma)),
            ),
            self.tr("calc_result_tip_refl").format(n=len(result["all_reflections"])),
        ]
        if len(result["wavelengths"]) > 1:
            lines.insert(
                2,
                self.tr("calc_result_tip_wl2_ratio").format(ratio=result["wl2_ratio"]),
            )
        if result.get("normalize_intensity", True):
            lines.append(
                self.tr("calc_result_tip_norm_yes").format(max=p0.intensity_max_value)
            )
        else:
            lines.append(self.tr("calc_result_tip_norm_no"))
        return ascii_ui_text("\n".join(lines))

    def _hide_calc_list_tooltip(self) -> None:
        win = getattr(self, "_calc_tooltip_win", None)
        if win is not None:
            try:
                win.destroy()
            except tk.TclError:
                pass
            self._calc_tooltip_win = None
        self._calc_tooltip_idx = None

    def _show_calc_list_tooltip(self, index: int, x_root: int, y_root: int) -> None:
        if index < 0 or index >= len(self._calc_results):
            self._hide_calc_list_tooltip()
            return
        if getattr(self, "_calc_tooltip_idx", None) == index and self._calc_tooltip_win:
            return
        self._hide_calc_list_tooltip()
        theme = self._current_theme()
        text = self._calc_result_tooltip(self._calc_results[index])
        win = tk.Toplevel(self.root)
        win.wm_overrideredirect(True)
        win.configure(bg=theme.tooltip_bg)
        lbl = tk.Label(
            win,
            text=text,
            justify=tk.LEFT,
            bg=theme.tooltip_bg,
            fg=theme.tooltip_fg,
            font=self.input_font,
            padx=10,
            pady=8,
            relief=tk.SOLID,
            borderwidth=1,
            highlightbackground=theme.border_soft,
            highlightthickness=1,
        )
        lbl.pack()
        win.update_idletasks()
        win.geometry(f"+{x_root + 16}+{y_root + 16}")
        self._calc_tooltip_win = win
        self._calc_tooltip_idx = index

    def _on_calc_list_motion(self, event) -> None:
        if self._calc_listbox is None:
            return
        idx = self._calc_listbox.nearest(event.y)
        if idx < 0 or idx >= len(self._calc_results):
            self._hide_calc_list_tooltip()
            return
        bbox = self._calc_listbox.bbox(idx)
        if bbox is None:
            self._hide_calc_list_tooltip()
            return
        _, y0, _, h = bbox
        if event.y < y0 or event.y > y0 + h:
            self._hide_calc_list_tooltip()
            return
        self._show_calc_list_tooltip(idx, event.x_root, event.y_root)

    def _on_calc_list_leave(self, _event=None) -> None:
        self._hide_calc_list_tooltip()

    def _refresh_calc_results_list(self):
        """Обновляет содержимое listbox рассчитанных дифрактограмм."""
        if self._calc_listbox is None:
            return
        selected = list(getattr(self, "_selected_calc_indices", []))
        self._calc_listbox.delete(0, tk.END)
        for i, item in enumerate(self._calc_results):
            item["label"] = self._format_calc_result_label(i, item)
            self._calc_listbox.insert(tk.END, item["label"])
        if selected:
            self._select_calc_result_indices(selected, redraw=False)

    def _select_calc_result_indices(
        self, indices: list[int], redraw: bool = True
    ) -> None:
        """Выделяет один или несколько расчётов и отображает их на графике."""
        if self._calc_listbox is None:
            return
        valid = [i for i in indices if 0 <= i < len(self._calc_results)]
        self._selected_calc_indices = valid
        self._calc_listbox.selection_clear(0, tk.END)
        for i in valid:
            self._calc_listbox.selection_set(i)
        if valid:
            self._calc_listbox.activate(valid[-1])
        if redraw and valid:
            self._display_calc_results([self._calc_results[i] for i in valid])

    def _select_calc_result_index(self, index: int, redraw: bool = True) -> None:
        """Выделяет один расчёт (удобная обёртка)."""
        self._select_calc_result_indices([index], redraw=redraw)

    def _on_calc_result_selected(self, _event=None):
        """Обработчик выбора расчёта в listbox (поддерживает мультивыбор)."""
        if self._calc_listbox is None:
            return
        sel = self._calc_listbox.curselection()
        if not sel:
            self._selected_calc_indices = []
            return
        self._select_calc_result_indices([int(i) for i in sel])

    def _get_selected_calc_results(self) -> list[dict]:
        """Все выбранные расчёты."""
        out = []
        for idx in getattr(self, "_selected_calc_indices", []):
            if 0 <= idx < len(self._calc_results):
                out.append(self._calc_results[idx])
        return out

    def _get_selected_calc_result(self):
        """Первый выбранный расчёт (для сохранения на диск)."""
        results = self._get_selected_calc_results()
        return results[0] if results else None

    @staticmethod
    def _hkl_labels_on_curve(patterns, x, y):
        """Собирает подписи hkl на кривой для экспорта PNG.

        Args:
            patterns: Список объектов ``PowderPattern``.
            x: Массив 2θ.
            y: Массив интенсивности.

        Returns:
            Список кортежей ``(hkl, xc, yp)`` без дубликатов по углу.
        """
        labels = []
        seen = set()
        for pattern in patterns:
            for hkl, xc, _ in pattern.hkl_labels:
                key = round(float(xc), 4)
                if key in seen:
                    continue
                seen.add(key)
                yp = float(np.interp(xc, x, y))
                labels.append((hkl, float(xc), yp))
        return labels

    def _plot_ylabel_for_result(self, result: dict) -> str:
        """Подпись оси Y с учётом нормировки интенсивности."""
        if result.get("normalize_intensity", True):
            return self.tr("plot_ylabel_normalized")
        return self.tr("plot_ylabel")

    def _display_calc_result(self, result: dict):
        """Отображает один расчёт на графике."""
        self._display_calc_results([result])

    def _display_calc_results(self, results: list[dict]):
        """Отображает один или несколько расчётов на одном графике."""
        if not results:
            return
        theme = THEMES[self._theme_key()]
        fonts = getattr(self, "fonts", None)
        mpl_family = fonts.mpl_family if fonts else "DejaVu Sans"
        lang = self.language_var.get().strip().lower()
        self.ax.clear()
        self._peak_label_artists.clear()
        self._hkl_hover_annot = None
        y_top = 0.0
        x_left = min(float(r["x"][0]) for r in results)
        x_right = max(float(r["x"][-1]) for r in results)
        multi = len(results) > 1
        line_width = float(self.plot_line_width_var.get())
        antialiased = bool(self.plot_antialiased_var.get())
        grid_major = bool(self.plot_grid_major_var.get())
        grid_minor = bool(self.plot_grid_minor_var.get())
        show_vlines = bool(self.plot_vlines_var.get())
        show_title = bool(self.plot_title_show_var.get())
        show_legend = bool(self.plot_legend_show_var.get())
        legend_loc = self.plot_legend_loc_var.get().strip() or "upper right"
        tick_size = self._plot_tick_fontsize()
        axis_label_size = self._plot_axis_label_fontsize()
        title_size = self._plot_title_fontsize()
        y_margin = float(self.plot_y_top_margin_var.get())
        layout_pad = float(self.plot_layout_pad_var.get())
        grid_major_alpha = float(self.plot_grid_major_alpha_var.get())
        grid_minor_alpha = float(self.plot_grid_minor_alpha_var.get())
        grid_major_lw = float(self.plot_grid_major_lw_var.get())
        grid_minor_lw = float(self.plot_grid_minor_lw_var.get())
        vline_width = float(self.plot_vline_width_var.get())
        vline_alpha = float(self.plot_vline_alpha_var.get())

        for i, result in enumerate(results):
            x = result["x"]
            y = result["y"]
            color = (
                _OVERLAY_LINE_COLORS[i % len(_OVERLAY_LINE_COLORS)]
                if multi
                else theme.mpl_line
            )
            label = result["name"] if multi else None
            self.ax.plot(
                x,
                y,
                linewidth=line_width,
                color=color,
                label=label,
                antialiased=antialiased,
            )
            y_top = max(y_top, float(np.max(y)) if len(y) else 0.0)

        if fonts:
            self.ax.set_xlabel(
                mpl_plot_xlabel(lang),
                fontsize=axis_label_size,
                fontfamily=mpl_family,
            )
            ylabel = (
                self.tr("plot_ylabel")
                if multi
                and len({r.get("normalize_intensity", True) for r in results}) > 1
                else self._plot_ylabel_for_result(results[0])
            )
            self.ax.set_ylabel(ylabel, fontfamily=mpl_family, fontsize=axis_label_size)
            if show_title:
                title = (
                    self.tr("plot_title")
                    if not multi
                    else ascii_ui_text(f"{self.tr('plot_title')} ({len(results)})")
                )
                self.ax.set_title(
                    title,
                    fontfamily=mpl_family,
                    fontsize=title_size,
                    fontweight="bold",
                )
        else:
            self.ax.set_xlabel(mpl_plot_xlabel(lang), fontsize=axis_label_size)
            self.ax.set_ylabel(
                self._plot_ylabel_for_result(results[0]), fontsize=axis_label_size
            )
            if show_title:
                self.ax.set_title(self.tr("plot_title"), fontsize=title_size)

        self.ax.tick_params(axis="both", labelsize=tick_size)
        self._configure_twotheta_axis(self.ax)
        if grid_major:
            self.ax.grid(
                True,
                axis="x",
                which="major",
                linewidth=grid_major_lw,
                alpha=grid_major_alpha,
            )
        if grid_minor:
            self.ax.grid(
                True,
                axis="x",
                which="minor",
                linewidth=grid_minor_lw,
                alpha=grid_minor_alpha,
            )
        self.ax.set_xlim(x_left, x_right)
        self._ensure_hkl_hover_annot(theme)
        self.ax.set_ylim(bottom=0.0, top=(y_top * y_margin if y_top > 0 else 1.0))
        self.ax.margins(x=0)

        if multi and show_legend:
            self.ax.legend(loc=legend_loc, fontsize=tick_size, framealpha=0.94)
            self._plot_peak_data = []
            self._hkl_hover_peaks = self._build_multi_hover_peaks(results)
            self._clear_peak_label_artists()
        else:
            result = results[0]
            x = result["x"]
            y = result["y"]
            all_reflections = result["all_reflections"]
            angle_values = sorted(
                {
                    ref["twotheta"]
                    for ref in all_reflections
                    if x[0] <= ref["twotheta"] <= x[-1]
                }
            )
            self._plot_peak_data = self._build_plot_peak_data(all_reflections, x, y)
            self._apply_reflection_label_mode()
            if angle_values and show_vlines:
                vline_color = theme.muted
                self.ax.vlines(
                    angle_values,
                    [0.0] * len(angle_values),
                    [float(np.interp(a, x, y)) for a in angle_values],
                    colors=vline_color,
                    linewidth=vline_width,
                    alpha=vline_alpha,
                    zorder=2,
                )

        self._full_xlim = (x_left, x_right)
        self._full_ylim = tuple(self.ax.get_ylim())
        apply_mpl_theme(self.figure, self.ax, theme, fonts)
        self.figure.tight_layout(pad=layout_pad)
        self.canvas.draw()

    def _append_calc_result(
        self,
        name: str,
        patterns,
        wl2_ratio: float,
        x,
        y,
        all_reflections,
        wavelengths,
        *,
        normalize_intensity: bool = True,
        run_config: dict | None = None,
    ):
        """Добавляет новый расчёт в список и выбирает его.

        Args:
            name: Имя расчёта.
            patterns: Список объектов ``PowderPattern``.
            wl2_ratio: Отношение интенсивностей второй и первой длин волн.
            x: Массив 2θ комбинированной кривой.
            y: Массив интенсивности.
            all_reflections: Объединённый список отражений.
            wavelengths: Использованные длины волн.
        """
        p0 = patterns[0]
        tth = p0.twotheta
        tth_step = float(tth[1] - tth[0]) if len(tth) > 1 else 0.0
        result = {
            "name": name,
            "patterns": patterns,
            "wl2_ratio": wl2_ratio,
            "x": x,
            "y": y,
            "all_reflections": all_reflections,
            "wavelengths": list(wavelengths),
            "normalize_intensity": normalize_intensity,
            "run_config": run_config or self.collect_run_config(),
            "profile_label": self._profile_label(p0.profile),
            "tth_start": float(tth[0]),
            "tth_end": float(tth[-1]),
            "tth_step": tth_step,
        }
        result["label"] = self._format_calc_result_label(
            len(self._calc_results), result
        )
        self._calc_results.append(result)
        self._refresh_calc_results_list()
        self._select_calc_result_index(len(self._calc_results) - 1)

    def _export_calc_result(self, result: dict, dest_dir: str, options: dict) -> None:
        """Экспортирует выбранные артефакты расчёта в указанный каталог.

        Args:
            result: Словарь расчёта с ``patterns``, ``x``, ``y``.
            dest_dir: Целевой каталог.
            options: Флаги типов файлов (txt, config, png, csv и т.д.).

        Raises:
            OSError: При ошибке записи файлов.
        """
        dest = Path(dest_dir)
        dest.mkdir(parents=True, exist_ok=True)
        base_name = result["name"]
        patterns = result["patterns"]
        crystal = patterns[0].crystal
        lang = self.language_var.get().strip().lower()
        export_names = self.EXPORT_FILENAMES.get(
            lang, self.EXPORT_FILENAMES["en"]
        )

        if options.get("txt"):
            for pattern in patterns:
                pattern.write_reflections_txt(dest / export_names["txt"])
        if options.get("angles_int"):
            for pattern in patterns:
                pattern.write_angles_int_txt(dest / export_names["angles_int"])
        if options.get("config"):
            run_cfg = result.get("run_config") or self.collect_run_config()
            with open(dest / f"{base_name}.yaml", "w", encoding="utf-8") as fh:
                yaml.safe_dump(
                    run_cfg,
                    fh,
                    allow_unicode=True,
                    sort_keys=False,
                    default_flow_style=False,
                )
        if options.get("G_csv"):
            np.savetxt(dest / "G.csv", crystal.G, delimiter=",")
        if options.get("Gstar_csv"):
            np.savetxt(dest / "Gstar.csv", crystal.Gstar, delimiter=",")
        if options.get("cell_png"):
            crystal.save_image(filename=dest / f"{base_name}.png")
        if options.get("powder_png"):
            hkl_plot = self._hkl_labels_on_curve(patterns, result["x"], result["y"])
            theme = THEMES[self._theme_key()]
            x = result["x"]
            Plot.save_powder_png(
                dest / export_names["powder_png"],
                x,
                result["y"],
                hkl_plot,
                base_name,
                ylabel=self._plot_ylabel_for_result(result),
                xlim=(float(x[0]), float(x[-1])),
                line_color=theme.mpl_line,
                facecolor=theme.plot_bg,
            )

    def _save_selected_result(self):
        """Сохраняет выбранный расчёт в папку, выбранную пользователем."""
        result = self._get_selected_calc_result()
        if result is None:
            messagebox.showwarning(
                self.tr("warning_title"), self.tr("save_no_result_selected")
            )
            return
        options = {k: v.get() for k, v in self._save_option_vars.items()}
        if not any(options.values()):
            messagebox.showwarning(
                self.tr("warning_title"), self.tr("save_nothing_selected")
            )
            return
        dest = filedialog.askdirectory(
            title=self.tr("save_pick_folder"), mustexist=False
        )
        if not dest:
            return
        try:
            self._export_calc_result(result, dest, options)
            messagebox.showinfo(
                self.tr("success_title"),
                self.tr("save_success").format(path=dest),
            )
        except Exception as e:
            messagebox.showerror(
                self.tr("error_title"), self.tr("save_failed").format(error=str(e))
            )
