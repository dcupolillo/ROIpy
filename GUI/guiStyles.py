""" Created on Tue Nov  7 10:03:57 2023
    @author: dcupolillo """

import os
from screeninfo import get_monitors
from ROIpy.assets.palette import dim


class StyleSheets():

    def __init__(
            self
    ) -> None:
        """
        Initializes the style sheets for the user interface components,
        adapting their sizes and styles to the screen resolution.
        It defines styles for buttons, entries, line edits, labels,
        titles, and sliders. It also calculates the window size and position
        based on the screen dimensions.

        Returns
        -------
        None

        """

        monitors = get_monitors()
        primary_monitor = monitors[0] if monitors else None

        screen_width = primary_monitor.width if primary_monitor else 1920
        screen_height = primary_monitor.height if primary_monitor else 1080

        width = int(screen_width / 64)
        height = int(screen_height / 35)

        self.button_size = (f'{width}px', f'{height}px')
        self.button_radius = '10px'
        self.button_font_size = '10pt'

        self.entry_size = (f'{width}px', f'{height}px')
        self.entry_font_size = '10pt'

        self.line_edit_size = (f'{width}px', f'{height}px')
        self.line_edit_font_size = '10pt'

        self.label_font_size = '10pt'
        self.title_font_size = '12pt'

        window_screen_ratio = 0.85

        self.window_size = (int(screen_height * window_screen_ratio),
                            int(screen_width * window_screen_ratio))

        # Window centered in the screen
        self.window_offset = (int(screen_width / 2)
                              - int(self.window_size[1] / 2),
                              int(screen_height / 2)
                              - int(self.window_size[0] / 2))

        self.window = f'background-color:{dim.black.hex}'

        self.frame = f'''background-color: {dim.dark.hex};
                          color: {dim.light.hex}'''

        self.button = f'''QPushButton {{ color: {dim.light.hex};
                                         background-color: {dim.d_dark.hex};
                                         width: {self.button_size[0]};
                                         height: {self.button_size[1]};
                                         border-radius : {self.button_radius};
                                         font-size: {self.button_font_size};
                                        }}
                        QPushButton:hover {{ background-color:
                                            {dim.hovering.hex};
                                            }}'''
        self.toggled_button = f'''QPushButton {{ color: {dim.light.hex};
                                               background-color:
                                                   {dim.hovering.hex};
                                               width:
                                                   {self.button_size[0]};
                                               height:
                                                   {self.button_size[1]};
                                               border-radius:
                                                   {self.button_radius};
                                               font-size:
                                                   {self.button_font_size};
                                              }}'''

        self.green_button = f'''QPushButton {{ color: {dim.light.hex};
                                               background-color:
                                                   {dim.green.hex};
                                               width: {self.button_size[0]};
                                               height: {self.button_size[1]};
                                               border-radius:
                                                   {self.button_radius};
                                               font-size:
                                                   {self.button_font_size};
                                              }}
                               QPushButton:hover {{ background-color:
                                                   {dim.hovering.hex};
                                                   }}'''

        self.line_edit = f'''QLineEdit {{ color: {dim.light.hex};
                                          background-color: {dim.d_dark.hex};
                                          width: {self.line_edit_size[0]};
                                          height: {self.line_edit_size[1]};
                                          border: 0px;
                                          font-size:
                                              {self.line_edit_font_size};
                                         }}'''

        self.entry = f'''QLabel {{ border: none;
                                   background-color: {dim.d_dark.hex};
                                   color: {dim.light.hex};
                                   width: {self.entry_size[0]};
                                   height: {self.entry_size[1]};
                                   font-size: {self.entry_font_size}
                                  }}'''

        self.label = f'''QLabel {{ color: {dim.light.hex};
                                   font-size: {self.label_font_size};
                                  }}'''

        self.title = f'''color:{dim.blue.hex};
                         font-weight: bold;
                         font-size: {self.title_font_size};'''

        self.slider = f'''QSlider::groove:horizontal {{ height: 10px;
                                                        background:
                                                            {dim.d_dark.hex}
                                                        }}
                          QSlider::handle:horizontal {{ background:
                                                       {dim.gray.hex};
                                                        width: 10px;
                                                        margin: -1px -1px;
                                                        border-radius: 5px;
                                                        border:
                                                            1px solid
                                                            {dim.d_dark.hex}}}
                          QSlider::handle::horizontal::hover {{ background:
                                                               {dim.hovering.hex};
                                                               border-color:
                                                                   {dim.blue.hex};
                                                               }}
                          QSlider::add-page::horizontal {{ background:
                                                          {dim.d_dark.hex};
                                                           }}
                          QSlider::sub-page:horizontal {{ background:
                                                         {dim.blue.hex}
                                                          }}'''


class Icons:

    def __init__(
            self
    ) -> None:
        """
        Load icons for displaying.
        """

        work_dir = os.path.dirname(__file__)

        self.folder = os.path.join(work_dir, 'icons', 'folder.png')
        self.neuron = os.path.join(work_dir, 'icons', 'nodes.png')
        self.rect = os.path.join(work_dir, 'icons', 'rectangles.png')
        self.next = os.path.join(work_dir, 'icons', 'next.png')
        self.layers = os.path.join(work_dir, 'icons', 'layers.png')
        self.quit = os.path.join(work_dir, 'icons', 'exit.png')
        self.load = os.path.join(work_dir, 'icons', 'load.png')
        self.plot = os.path.join(work_dir, 'icons', 'plot.png')
        self.reset = os.path.join(work_dir, 'icons', 'reset.png')
        self.save = os.path.join(work_dir, 'icons', 'savefile.png')
        self.image = os.path.join(work_dir, 'icons', 'image.png')
        self.max_proj = os.path.join(work_dir, 'icons', 'maxProj.png')


darkMode = StyleSheets()
icon = Icons()
