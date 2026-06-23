"""Фрагмент GUI: PlotViewMixin."""

import numpy as np

from .theme import mpl_angle_label, mpl_hover_peak_text


class PlotViewMixin:
    def _plot_peak_text_props(self) -> dict:
        """Стили подписей пиков на графике (цвет темы + DejaVu Sans)."""
        theme = self._current_theme()
        size = self._plot_peak_label_fontsize()
        return {
            "color": theme.plot_fg,
            "fontsize": size,
            "ha": "center",
            "va": "bottom",
            "alpha": 0.92,
            "clip_on": True,
            "zorder": 6,
        }

    def _build_plot_peak_data(self, all_reflections, x, y_combined):
        """Формирует данные пиков для подписей и всплывающих подсказок.

        Args:
            all_reflections: Список отражений с ``twotheta`` и ``hkl``.
            x: Массив 2θ сетки графика.
            y_combined: Интенсивность на сетке.

        Returns:
            Список словарей с координатами и текстами подписей.
        """
        peaks = []
        x0, x1 = float(x[0]), float(x[-1])
        for ref in all_reflections:
            xc = float(ref["twotheta"])
            if not (x0 <= xc <= x1):
                continue
            hkl = ref["hkl"]
            h, k, l_idx = (
                int(round(hkl[0])),
                int(round(hkl[1])),
                int(round(hkl[2])),
            )
            yp = float(np.interp(xc, x, y_combined))
            hkl_str = f"{h}{k}{l_idx}"
            peaks.append(
                {
                    "xc": xc,
                    "yp": yp,
                    "hkl": hkl_str,
                    "hover_hkl": hkl_str,
                    "hover_full": mpl_hover_peak_text(hkl_str, xc),
                    "angle_label": mpl_angle_label(xc),
                }
            )
        return peaks

    def _build_multi_hover_peaks(
        self, results: list[dict]
    ) -> list[tuple[float, float, str]]:
        """Собирает точки hover hkl/2θ для нескольких наложенных кривых."""
        if self.label_reflection_mode_var.get() == "none":
            return []
        peaks: list[tuple[float, float, str]] = []
        multi = len(results) > 1
        for result in results:
            x = result["x"]
            y = result["y"]
            series = result["name"]
            for peak in self._build_plot_peak_data(result["all_reflections"], x, y):
                hover = peak["hover_full"]
                if multi:
                    hover = f"{series}\n{hover}"
                peaks.append((peak["xc"], peak["yp"], hover))
        return peaks

    def _clear_peak_label_artists(self):
        """Удаляет текстовые подписи пиков с графика."""
        for artist in self._peak_label_artists:
            try:
                if artist.axes is not None:
                    artist.remove()
            except (ValueError, AttributeError):
                pass
        self._peak_label_artists.clear()

    def _apply_reflection_label_mode(self):
        """Применяет режим подписей отражений (углы, hkl или оба)."""
        if self._plot_peak_data is None:
            return
        mode = self.label_reflection_mode_var.get()
        show_both = mode == "both"
        show_angles = mode == "angles"
        self._clear_peak_label_artists()
        self._hkl_hover_peaks = []
        labeled_angles = set()
        y_top = self.ax.get_ylim()[1]
        text_kw = self._plot_peak_text_props()
        for peak in self._plot_peak_data:
            xc, yp = peak["xc"], peak["yp"]
            if show_both:
                y_text = min(yp * 1.02, y_top * 0.98) if yp > 0 else y_top * 0.05
                txt = self.ax.text(
                    xc,
                    y_text,
                    rf"$\mathrm{{{peak['hkl']}}}$" + "\n" + peak["angle_label"],
                    **text_kw,
                )
                self._peak_label_artists.append(txt)
                self._hkl_hover_peaks.append((xc, yp, peak["hover_full"]))
            elif show_angles:
                self._hkl_hover_peaks.append((xc, yp, peak["hover_full"]))
                angle_key = round(xc, 3)
                if angle_key in labeled_angles:
                    continue
                labeled_angles.add(angle_key)
                y_text = min(yp * 1.02, y_top * 0.98) if yp > 0 else y_top * 0.05
                txt = self.ax.text(xc, y_text, peak["angle_label"], **text_kw)
                self._peak_label_artists.append(txt)
            elif mode != "none":
                self._hkl_hover_peaks.append((xc, yp, peak["hover_full"]))
        self.canvas.draw_idle()

    def _on_label_reflection_mode_changed(self):
        """Обработчик смены режима подписей отражений на графике."""
        if not self._undo_restoring:
            self._push_undo_snapshot()
        self._apply_reflection_label_mode()
        if not self._undo_restoring:
            self._commit_form_state()

    def _hover_match_tolerance(self) -> float:
        """Допуск по оси 2θ для попадания курсора на пик.

        Returns:
            Ширина окна сопоставления (градусы).
        """
        x0, x1 = self.ax.get_xlim()
        return max(0.2, (float(x1) - float(x0)) * 0.015)

    def _ensure_hkl_hover_annot(self, theme) -> None:
        """Создаёт или пересоздаёт всплывающую подсказку hkl на текущей оси."""
        if self._hkl_hover_cid is not None:
            try:
                self.canvas.mpl_disconnect(self._hkl_hover_cid)
            except ValueError:
                pass
            self._hkl_hover_cid = None

        fonts = getattr(self, "fonts", None)
        annot_size = fonts.plot_tick[1] if fonts else 10

        self._hkl_hover_annot = self.ax.annotate(
            "",
            xy=(0, 0),
            xytext=(0, 22),
            textcoords="offset points",
            ha="center",
            va="bottom",
            bbox=dict(
                boxstyle="round,pad=0.4",
                fc=theme.tooltip_bg,
                ec=theme.border_soft,
                alpha=0.97,
            ),
            color=theme.tooltip_fg,
            fontsize=annot_size,
            visible=False,
            zorder=20,
        )
        self._hkl_hover_cid = self.canvas.mpl_connect(
            "motion_notify_event", self._on_hkl_hover_motion
        )

    def _on_hkl_hover_motion(self, event):
        """Показывает всплывающую подсказку hkl при наведении на пик.

        Args:
            event: Событие движения мыши matplotlib.
        """
        ann = self._hkl_hover_annot
        if ann is None:
            return
        peaks = self._hkl_hover_peaks
        if not peaks:
            if ann.get_visible():
                ann.set_visible(False)
                self.canvas.draw_idle()
            return
        if event.inaxes != self.ax:
            if ann.get_visible():
                ann.set_visible(False)
                self.canvas.draw_idle()
            return
        mx = event.xdata
        my = event.ydata
        if mx is None:
            return
        tol = self._hover_match_tolerance()
        y0, y1 = self.ax.get_ylim()
        y_tol = max((float(y1) - float(y0)) * 0.12, 1.0)
        best = None
        best_score = None
        for xc, yp, lab in peaks:
            dx = abs(mx - xc)
            if dx > tol:
                continue
            if my is not None:
                dy = abs(my - yp)
                if dy > y_tol:
                    continue
                score = (dx / tol) ** 2 + (dy / y_tol) ** 2
            else:
                score = dx
            if best_score is None or score < best_score:
                best_score = score
                best = (xc, yp, lab)
        if best is None:
            for xc, yp, lab in peaks:
                d = abs(mx - xc)
                if d < tol and (best is None or d < abs(mx - best[0])):
                    best = (xc, yp, lab)
        if best is None:
            if ann.get_visible():
                ann.set_visible(False)
                self.canvas.draw_idle()
            return
        xc, yp, lab = best
        ann.xy = (xc, yp)
        ann.set_text(lab)
        ann.set_visible(True)
        self.canvas.draw_idle()
