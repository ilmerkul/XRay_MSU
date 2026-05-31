"""Фрагмент GUI: PlotInteractionMixin."""

import os
import shutil
import subprocess
import tempfile
from tkinter import messagebox


class PlotInteractionMixin:
    def _on_zoom_select(self, eclick, erelease):
        """Применяет масштаб по выделенной области на графике.

        Args:
            eclick: Точка начала выделения (``RectangleSelector``).
            erelease: Точка отпускания кнопки мыши.
        """
        if eclick.xdata is None or eclick.ydata is None:
            return
        if erelease.xdata is None or erelease.ydata is None:
            return
        x0, x1 = sorted((float(eclick.xdata), float(erelease.xdata)))
        if abs(x1 - x0) < 1e-6:
            return
        self.ax.set_xlim(x0, x1)
        self.tth_start_var.set(x0)
        self.tth_end_var.set(x1)
        self.canvas.draw_idle()

    def _on_zoom_reset_click(self, event):
        """Сбрасывает масштаб по правому клику на графике.

        Args:
            event: Событие нажатия кнопки мыши matplotlib.
        """
        if event.inaxes != self.ax or event.button != 3:
            return
        self._reset_zoom()

    def _reset_zoom(self):
        """Восстанавливает исходный диапазон осей и поля 2θ."""
        if self._full_xlim is None or self._full_ylim is None:
            return
        self.ax.set_xlim(*self._full_xlim)
        self.tth_start_var.set(float(self._full_xlim[0]))
        self.tth_end_var.set(float(self._full_xlim[1]))
        self.canvas.draw_idle()

    def _print_pattern(self):
        """Сохраняет график во временный PNG и отправляет на системную печать."""
        if not self.ax.has_data():
            messagebox.showwarning(
                self.tr("warning_title"), self.tr("no_pattern_to_print")
            )
            return

        tmp_path = None
        try:
            with tempfile.NamedTemporaryFile(
                mode="wb", suffix=".png", delete=False
            ) as tmp:
                tmp_path = tmp.name
            self.figure.savefig(tmp_path, dpi=300, bbox_inches="tight")
            if os.name == "nt":
                # Windows: используем системный shell-print для зарегистрированного PNG viewer.
                os.startfile(tmp_path, "print")

                # Дадим spooler время прочитать файл перед удалением.
                def _cleanup_tmp(p):
                    """Удаляет временный файл печати после задержки.

                    Args:
                        p: Путь к временному PNG-файлу.
                    """
                    try:
                        if os.path.exists(p):
                            os.remove(p)
                    except OSError:
                        pass

                self.root.after(120000, lambda p=tmp_path: _cleanup_tmp(p))
                tmp_path = None
            elif shutil.which("lp") is not None:
                subprocess.run(
                    ["lp", tmp_path], check=True, capture_output=True, text=True
                )
            elif shutil.which("lpr") is not None:
                subprocess.run(
                    ["lpr", tmp_path], check=True, capture_output=True, text=True
                )
            else:
                messagebox.showwarning(
                    self.tr("warning_title"), self.tr("printer_not_found")
                )
                return
            messagebox.showinfo(self.tr("success_title"), self.tr("print_sent"))
        except subprocess.CalledProcessError as e:
            msg = e.stderr.strip() if e.stderr else str(e)
            messagebox.showerror(
                self.tr("error_title"), self.tr("print_failed").format(error=msg)
            )
        except Exception as e:
            messagebox.showerror(
                self.tr("error_title"), self.tr("print_failed").format(error=str(e))
            )
        finally:
            if tmp_path and os.path.exists(tmp_path):
                try:
                    os.remove(tmp_path)
                except OSError:
                    pass
