import tkinter

import matplotlib
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.colors import Normalize
from matplotlib.image import AxesImage

from service.app_service import AppService
import utils.utils as myUtils

matplotlib.use('TkAgg')


class MRIPlotComponent:
    _base_image_path = ""
    _mask_image_path = ""

    _base_image_data = None
    _mask_image_data = None
    _image_min_max = (0, 1)

    _mask_transparency = 0.333

    _axial_pos = 0
    _sagittal_pos = 0
    _coronal_pos = 0

    _plot_canvas = None
    _plot_artists = []

    _is_mask_displayed = True

    def __init__(self, root, app_service: AppService, transparency=None):
        self.root = root
        self._app_service = app_service

        self._plot_canvas, self._plot_axes = plt.subplots(nrows=1, ncols=3)

        #plt.ion()
        canvas = FigureCanvasTkAgg(self._plot_canvas, master=self.root)  # A tk.DrawingArea.
        canvas.draw()
        canvas.get_tk_widget().pack(side=tkinter.TOP, fill=tkinter.BOTH, expand=1)
        canvas.mpl_connect('pick_event', self._on_pick)
        canvas.mpl_connect('close_event', self._handle_close)

    def set_image_paths(self, image_path, mask_path, transparency=None):
        self._base_image_path = image_path
        self._mask_image_path = mask_path
        if transparency is not None:
            self._mask_transparency = max(min(transparency, 1), 0)

        self.reload()

    def reload(self):
        if self._base_image_path != "":
            self._base_image_data, _ = myUtils.load_nifti_image(self._base_image_path)
            self._image_min_max = (self._base_image_data.min(), self._base_image_data.max())

            print(self._base_image_data.shape)

            self._axial_pos = self._base_image_data.shape[0] // 2
            self._sagittal_pos = self._base_image_data.shape[1] // 2
            self._coronal_pos = self._base_image_data.shape[2] // 2
        else:
            self._base_image_data = None

        if self._mask_image_path != "":
            self._mask_image_data, _ = myUtils.load_nifti_image(self._mask_image_path)

            if self._mask_image_data.shape != self._base_image_data.shape:
                print("ERROR: Incorrect mask dimensions")
                self._mask_image_data = None
        else:
            self._mask_image_data = None

        self._display_current_frame()

    def set_mask_transparency(self, new_transparency):
        self._mask_transparency = new_transparency
        self._display_current_frame()

    def set_mask_showing(self, showing):
        if self._mask_image_path == "":
            self.set_image_paths(self._app_service.get_image_path(), self._app_service.get_label_path())
        self._is_mask_displayed = showing
        self._display_current_frame()

    def _handle_close(self, evt):
        plt.close('all')

    def _display_current_frame(self):
        slices = [self._base_image_data[self._axial_pos, :, :],
                  self._base_image_data[:, self._sagittal_pos, :],
                  self._base_image_data[:, :, self._coronal_pos]]
        self._plot_artists = [None, None, None]

        if self._is_mask_displayed and self._mask_image_data is not None:
            mask_slices = [self._mask_image_data[self._axial_pos, :, :],
                           self._mask_image_data[:, self._sagittal_pos, :],
                           self._mask_image_data[:, :, self._coronal_pos]]

        for i, slice in enumerate(slices):
            self._plot_axes[i].clear()
            self._plot_artists[i] = self._plot_axes[i].imshow(slice.T,
                                                              cmap="gray",
                                                              origin="lower",
                                                              norm=Normalize(vmax=self._image_min_max[1],
                                                                             vmin=self._image_min_max[0]),
                                                              picker=True)
            if self._is_mask_displayed and self._mask_image_data is not None:
                self._plot_axes[i].imshow(mask_slices[i].T,
                                          cmap="viridis",
                                          origin="lower",
                                          alpha=self._mask_transparency,
                                          picker=False)

        self._plot_canvas.canvas.draw()

    def _move_slice(self, axial_delta, saggital_delta, coronal_delta):
        self._axial_pos = self._axial_pos + axial_delta
        self._axial_pos = self._axial_pos % self._base_image_data.shape[0]

        self._sagittal_pos = self._sagittal_pos + saggital_delta
        self._sagittal_pos = self._sagittal_pos % self._base_image_data.shape[1]

        self._coronal_pos = self._coronal_pos + coronal_delta
        self._coronal_pos = self._coronal_pos % self._base_image_data.shape[2]

    def _on_pick(self, event):
        mouse_event = event.mouseevent
        artist = event.artist
        delta = 0
        if mouse_event.button == 'up':
            delta = 2
        elif mouse_event.button == 'down':
            delta = -2

        if delta != 0 and isinstance(artist, AxesImage):
            # Axial plot
            if artist is self._plot_artists[0]:
                self._move_slice(delta, 0, 0)

            # Saggital plot
            if artist is self._plot_artists[1]:
                self._move_slice(0, delta, 0)

            # Coronal plot
            if artist is self._plot_artists[2]:
                self._move_slice(0, 0, delta)

            self._display_current_frame()
