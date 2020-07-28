"""
cli-pto
-------
Author: Özenç Bilgili
Description: cli-pto is a CLI text editing tool with encryption.
"""

import sys
import os
import datetime
import re

from asyncio import Future, ensure_future

from prompt_toolkit.application import Application
from prompt_toolkit.shortcuts import input_dialog

from prompt_toolkit.application.current import get_app
from prompt_toolkit.completion import PathCompleter
from prompt_toolkit.filters import Condition
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.layout.controls import FormattedTextControl
from prompt_toolkit.layout.dimension import D
from prompt_toolkit.layout.layout import Layout
from prompt_toolkit.layout.menus import CompletionsMenu
from prompt_toolkit.lexers import DynamicLexer, PygmentsLexer
from prompt_toolkit.search import start_search
from prompt_toolkit.styles import Style
from prompt_toolkit.widgets import (
    Button,
    Dialog,
    Label,
    SearchToolbar,
    TextArea,
)
from prompt_toolkit.layout.containers import (
    ConditionalContainer,
    Float,
    HSplit,
    VSplit,
    Window,
    WindowAlign,
    FloatContainer,
)

from cli_pto.encrypt_decrypt import EncryptDecrypt

class ApplicationState:
    """
    App state.
    This class is not instantiated
    """
    show_status_bar = True
    current_path = ''
    password = ''
    user = ''


class TextInputDialog:
    """
    Input prompts
    """
    def __init__(self, title='', label_text='', completer=None):
        self.future = Future()

        def accept_text(buf):
            get_app().layout.focus(ok_button)
            buf.complete_state = None
            return True

        def accept():
            self.future.set_result(self.text_area.text)

        def cancel():
            self.future.set_result(None)

        self.text_area = TextArea(
            completer=completer,
            multiline=False,
            width=D(preferred=40),
            accept_handler=accept_text,
        )

        ok_button = Button(text='OK', handler=accept)
        cancel_button = Button(text='Cancel', handler=cancel)

        self.dialog = Dialog(
            title=title,
            body=HSplit([Label(text=label_text), self.text_area]),
            buttons=[ok_button, cancel_button],
            width=D(preferred=80),
            modal=True,
        )

    def __pt_container__(self):
        return self.dialog


class MessageDialog:
    """
    Message boxes
    """
    def __init__(self, title, text):
        self.future = Future()

        def set_done():
            self.future.set_result(None)

        ok_button = Button(text='OK', handler=(lambda: set_done()))

        self.dialog = Dialog(
            title=title,
            body=HSplit([Label(text=text),]),
            buttons=[ok_button],
            width=D(preferred=80),
            modal=True,
        )

    def __pt_container__(self):
        return self.dialog



# Global key bindings
# -------------------
BINDINGS = KeyBindings()

# New file
@BINDINGS.add('c-n')
def _(event):
    'New File'

# Open file
@BINDINGS.add('c-o')
def _(event):
    'Open'
    do_open_file(None)

# Save
@BINDINGS.add('c-s')
def _(event):
    'Save'
    do_save_file()

# Quit
@BINDINGS.add('c-q')
def _(event):
    'Quit'
    do_exit()

# Select all
@BINDINGS.add('c-a')
def _(event):
    'Select all'
    do_select_all()

# Deselect
@BINDINGS.add('c-d')
def _(event):
    'Cancel'
    deselect()
@BINDINGS.add('escape')
def _(event):
    'Cancel'
    deselect()

# Go to line
@BINDINGS.add('c-g')
def _(event):
    'Go to line'
    do_go_to()

# Find
@BINDINGS.add('c-f')
def _(event):
    'Find'
    do_find()

# Find Next
@BINDINGS.add('c-f', 'c-n')
def _(event):
    'Find Next'
    do_find_next()

# Copy
@BINDINGS.add('c-c')
def _(event):
    'Copy'
    do_copy()

# Cut
@BINDINGS.add('c-x')
def _(event):
    'Cut'
    do_cut()

# Paste
@BINDINGS.add('c-v')
def _(event):
    'Paste'
    do_paste()

# Undo
@BINDINGS.add('c-z')
def _(event):
    'Undo'
    do_undo()

@BINDINGS.add('f1')
def _(event):
    'Help'
    do_help()

@BINDINGS.add('f11')
def _(event):
    'Help'
    do_about()




# Handlers
# --------

SEARCH_TOOLBAR = SearchToolbar()
TEXT_FIELD = TextArea(
    lexer=DynamicLexer(
        lambda: PygmentsLexer.from_filename(
            ApplicationState.current_path or '.txt', sync_from_start=False
        )
    ),
    scrollbar=False,
    line_numbers=True,
    wrap_lines=True,
    search_field=SEARCH_TOOLBAR,
)
TITLE = Window(
    height=1,
    content=FormattedTextControl('cli-pto'),
    align=WindowAlign.CENTER,
)



def get_statusbar_line():
    return ' {}:{}  '.format(
        TEXT_FIELD.document.cursor_position_row + 1,
        TEXT_FIELD.document.cursor_position_col + 1,
    )


def do_open_file(filename):
    crypto = EncryptDecrypt(ApplicationState.user, ApplicationState.password)

    async def coroutine():
        open_dialog = TextInputDialog(
            title='Open file',
            label_text='Enter the path of a file:',
            completer=PathCompleter(),
        )

        path = filename if filename else await show_dialog_as_float(open_dialog)
        ApplicationState.current_path = path

        if path is not None:
            try:
                if not os.path.isfile(path):
                    open(path, 'a').close()
                with open(path, 'rb+') as f:
                    if os.stat(path).st_size != 0:
                        TEXT_FIELD.text = crypto.decrypt_text(f.read())
                        f.close()
                    else:
                        TEXT_FIELD.text = ''
            except IOError as e:
                show_message('Error', '{}'.format(e))

    ensure_future(coroutine())


def do_save_file():
    crypto = EncryptDecrypt(ApplicationState.user, ApplicationState.password)

    path = ApplicationState.current_path
    if path is not None:
        try:
            with open(path, 'wb') as f:
                enc = crypto.encrypt_text(TEXT_FIELD.text)
                f.write(enc)
                f.close()
        except IOError as e:
            show_message('Error', '{}'.format(e))


def do_about():
    show_message('About',
                 '''
                 cli-pto
                 Created by Özenç Bilgili
                 github.com/ozencb
                 '''
                 )


def do_help():
    show_message('Help',
                 '''
                 Shortcuts:

                 New File: CTRL - O
                 Open File: CTRL - N
                 Save: CTRL - S
                 Quit: CTRL - Q

                 Select All: CTRL - A
                 Deselect: CTRL - D / Escape
                 Go To Line: CTRL - G
                 Find: CTRL - F
                 Find Next: CTRL - F + CTRL - N

                 Undo: CTRL - Z
                 Copy: CTRL - C
                 Cut: CTRL - X
                 Paste: CTRL - V
                 '''
                 )


def show_message(title, text):
    async def coroutine():
        dialog = MessageDialog(title, text)
        await show_dialog_as_float(dialog)

    ensure_future(coroutine())


async def show_dialog_as_float(dialog):
    ' Coroutine. '
    float_ = Float(content=dialog)
    ROOT_CONTAINER.floats.insert(0, float_)

    app = get_app()

    focused_before = app.layout.current_window
    app.layout.focus(dialog)
    result = await dialog.future
    app.layout.focus(focused_before)

    if float_ in ROOT_CONTAINER.floats:
        ROOT_CONTAINER.floats.remove(float_)

    return result


def do_exit():
    get_app().exit()


def do_time_date():
    text = datetime.datetime.now().isoformat()
    TEXT_FIELD.buffer.insert_text(text)


def do_go_to():
    async def coroutine():
        dialog = TextInputDialog(title='Go to line', label_text='Line number:')

        line_number = await show_dialog_as_float(dialog)

        try:
            line_number = int(line_number)
        except ValueError:
            show_message('', 'Invalid line number')
        else:
            TEXT_FIELD.buffer.cursor_position = TEXT_FIELD.buffer.document.translate_row_col_to_index(
                line_number - 1, 0
            )

    ensure_future(coroutine())


def do_undo():
    TEXT_FIELD.buffer.undo()


def do_cut():
    data = TEXT_FIELD.buffer.cut_selection()
    get_app().clipboard.set_data(data)


def do_copy():
    data = TEXT_FIELD.buffer.copy_selection()
    get_app().clipboard.set_data(data)


def do_delete():
    TEXT_FIELD.buffer.cut_selection()


def do_find():
    start_search(TEXT_FIELD.control)


def do_find_next():
    search_state = get_app().current_search_state

    cursor_position = TEXT_FIELD.buffer.get_search_position(
        search_state, include_current_position=False
    )
    TEXT_FIELD.buffer.cursor_position = cursor_position


def do_paste():
    TEXT_FIELD.buffer.paste_clipboard_data(get_app().clipboard.get_data())


def do_select_all():
    TEXT_FIELD.buffer.cursor_position = 0
    TEXT_FIELD.buffer.start_selection()
    TEXT_FIELD.buffer.cursor_position = len(TEXT_FIELD.buffer.text)


def deselect():
    TEXT_FIELD.buffer.exit_selection()


def do_status_bar():
    ApplicationState.show_status_bar = not ApplicationState.show_status_bar


def format_filename(filename):
    return re.sub(r'[/\\:*?"<>|]', '', filename).lstrip('0123456789')



# Components and containers
# -------------------------
BODY = HSplit(
    [
        TITLE,
        TEXT_FIELD,
        SEARCH_TOOLBAR,
        ConditionalContainer(
            content=VSplit(
                [
                    Window(
                        FormattedTextControl(get_statusbar_line),
                        style='class:status',
                        width=10,
                        align=WindowAlign.LEFT,
                    ),
                    Window(
                        FormattedTextControl('Press F1 for Help, F11 for About'),
                        style='class:status.right',
                        align=WindowAlign.RIGHT,
                    ),

                ],
                height=1,
            ),
            filter=Condition(lambda: ApplicationState.show_status_bar),
        ),
    ],
)

ROOT_CONTAINER = FloatContainer(
    content=BODY,
    floats=[
        Float(
            xcursor=True,
            ycursor=True,
            content=CompletionsMenu(max_height=16, scroll_offset=1),
        )
    ],
    key_bindings=BINDINGS
)

STYLE = Style.from_dict({
    'shadow': 'bg:#440044',
})

LAYOUT = Layout(ROOT_CONTAINER, focused_element=TEXT_FIELD)

APPLICATION = Application(
    layout=LAYOUT,
    enable_page_navigation_bindings=True,
    style=STYLE,
    full_screen=True,
)




def main():
    if len(sys.argv) < 2:
        while len(ApplicationState.current_path) < 1:
            filename = input_dialog(
                title='Open or create a file.',
                text='Please enter file name:',
            ).run()
            ApplicationState.current_path = format_filename(filename)
    else:
        ApplicationState.current_path = format_filename(sys.argv[1])

    while len(ApplicationState.user) < 1:
        ApplicationState.user = input_dialog(
            title='User',
            text='Please type your user name:',
        ).run()

    while len(ApplicationState.password) < 8:
        ApplicationState.password = input_dialog(
            title='Password',
            text='Password must be longer than 8 characters\nPlease type your password:',
            password=True,
        ).run()
   


    do_open_file(ApplicationState.current_path)

    APPLICATION.run()

if __name__ == '__main__':
    main()
