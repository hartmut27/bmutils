#!/usr/bin/env python
# coding=utf-8

# bmutils-repl: Read–eval–print loop for python expressions, using Urwid
#
# Copyright (C) 2014 Hartmut Pfarr
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

# ------------------------------------------------------------------------

# Python 3.4 with "pip install argparse urwid"
# Python 2.7 with "pip install argparse urwid enum34"


import urwid
import urwid.widget
from enum import Enum


class ReplColors(Enum):
    black_on_white = '001'
    black_on_red = '002'
    black_on_lightgrey = '003'
    white_on_blue = '004'
    white_on_grey = '005'
    white_on_black = '006'
    white_on_green = '007'
    white_on_lightgrey = '008'
    grey_on_lightgrey = '009'
    grey_on_darkgrey = '010'
    grey_on_white = '011'


class ReplListbox(urwid.ListBox):
    def __init__(self):
        self.listwalker = urwid.SimpleFocusListWalker([])
        super(ReplListbox, self).__init__(self.listwalker)
        pass


class ReplApp:
    def __init__(self):
        self.palette = [
            (ReplColors.grey_on_darkgrey, 'light gray', 'dark gray'),
            (ReplColors.grey_on_lightgrey, 'dark gray', 'light gray'),
            (ReplColors.grey_on_white, 'dark gray', 'white'),
            (ReplColors.white_on_blue, 'white', 'light blue'),
            (ReplColors.white_on_green, 'white', 'dark green'),
            (ReplColors.white_on_grey, 'white', 'dark gray'),
            (ReplColors.white_on_lightgrey, 'white', 'light gray'),
            (ReplColors.white_on_black, 'white', 'black'),
            (ReplColors.black_on_white, 'black', 'white'),
            (ReplColors.black_on_red, 'black', 'dark red'),
            (ReplColors.black_on_lightgrey, 'black', 'light gray'),
        ]
        self.header_txt = urwid.Text("bmutils-repl: Read–eval–print loop")
        self.header_text_a = urwid.AttrMap(w=self.header_txt, attr_map=ReplColors.white_on_green)
        self.footer_text = urwid.Text("Ins=Insert Python expression  "
                                      "Ctrl-X=Remove expression\n"
                                      "Enter=Evaluate  "
                                      "Scroll with ↑↓ Page↑ Page↓  "
                                      "Ctrl-W=Quit")
        self.footer_text_a = urwid.AttrMap(w=self.footer_text, attr_map=ReplColors.white_on_blue)
        self.repl_items = ReplListbox()
        self.welcome_text = urwid.Text("Welcome to bmutils-repl. Please enter Python expressions.")
        self.repl_items.body.append(self.welcome_text)
        self.initial_question = self.new_entry_field()
        self.repl_items.body.append(self.initial_question)
        self.repl_items_a = urwid.AttrMap(w=self.repl_items, attr_map=ReplColors.grey_on_lightgrey)

    def main(self):
        top = urwid.LineBox(urwid.Frame(body=self.repl_items_a,
                                        header=self.header_text_a,
                                        footer=self.footer_text_a))
        top = urwid.Overlay(top, urwid.SolidFill(u'\N{MEDIUM SHADE}'),
                            align='center', width=('relative', 92),
                            valign='middle', height=('relative', 88),
                            min_width=20, min_height=9)
        loop = urwid.MainLoop(widget=top, palette=self.palette, unhandled_input=self.handle_keypressed)
        loop.run()

    def drop_message(self, s):
        a, _ = self.welcome_text.get_text()
        self.welcome_text.set_text(a + s + ". ")

    @staticmethod
    def new_entry_field():
        edit01 = urwid.Edit((ReplColors.black_on_lightgrey, '> '))
        edit02a = urwid.AttrMap(w=edit01, attr_map=ReplColors.grey_on_white)
        return edit02a

    def move_cursor_to_edit_field(self, direction):
        p, px = self.repl_items.get_focus()
        while True:
            if direction == 'prev':
                p, px = self.repl_items.body.get_prev(px)
            elif direction == 'next':
                p, px = self.repl_items.body.get_next(px)
            else:
                raise Exception("move_cursor_to_edit_field wrong direction")
            if p is None:
                break
            if type(p.base_widget) == urwid.widget.Edit:
                break
        if not p is None:
            self.repl_items.set_focus(position=px)
            return True
        return False

    def handle_keypressed(self, key):
        if key == 'ctrl w':
            self.drop_message('Exit')
            raise urwid.ExitMainLoop

        # remove edit field under caret and its answers (text fields) 
        if key == 'ctrl x':
            w, p = self.repl_items.body.get_focus()
            if w is None:
                return
            self.repl_items.body.remove(w)
            while True:
                w2, p2 = self.repl_items.body.get_focus()
                if w2 is None:
                    return
                if p2 < p:
                    break
                # exit if next edit field is reached                
                if type(w2.base_widget) == urwid.widget.Edit:
                    return
                self.repl_items.body.remove(w2)
            # jump to previous edit field if caret is placed on a text widget
            if type(w2.base_widget) != urwid.widget.Edit:
                self.move_cursor_to_edit_field(direction='prev')
            return

        # insert new edit field under caret
        if key == 'insert':
            w = self.new_entry_field()
            if self.repl_items.focus is None:
                p = 0
            else:
                p = self.repl_items.focus_position
            self.repl_items.body.insert(p, w)
            self.repl_items.set_focus(position=p)

        # evaluate edit field under caret
        if key == 'enter':
            # current entry
            p, px = self.repl_items.get_focus()
            if p is None:
                return
            # must be an edit field
            if type(p.base_widget) != urwid.widget.Edit:
                return
            # no evaluation of nothing
            if p.base_widget.edit_text == '':
                return
            # produce anser
            try:
                eval_result = eval(p.base_widget.edit_text)
                result_str = '{}'.format(eval_result)
            except Exception as e:
                result_str = str(e)
            rslt_w = urwid.Text(result_str)
            rslt_w_a = urwid.AttrMap(w=rslt_w, attr_map=ReplColors.grey_on_lightgrey)
            # put answer one line below
            if p is not None:
                p, px = self.repl_items.body.get_next(px)
            # insert answer
            if p is not None:
                self.repl_items.body.insert(px, rslt_w_a)
            # append answer
            else:
                self.repl_items.body.append(rslt_w_a)
            r = self.move_cursor_to_edit_field(direction='next')
            if not r:
                w = self.new_entry_field()
                self.repl_items.body.append(w)
                self.move_cursor_to_edit_field(direction='next')

def main():
    ReplApp().main()

if '__main__' == __name__:
    main()
