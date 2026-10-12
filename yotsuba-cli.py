#!/usr/bin/env python3

import curses
from curses import wrapper
from dataclasses import dataclass

import help
import api
import render

class BadRequest(Exception):
    pass

class InvalidCommand(Exception):
    pass

class InvalidIndexContext(Exception):
    pass

class CommandParse:
    """
    Syntax
    -----------------
    Available commands: thread, board, image, listboards

    /listboards              -> lists all boards
    /board [board] [page]    -> goes to specified board, optionally you can select a page
    /thread [board] [number] -> goes to thread index as specified in [number] of chosen board
    /image [board] [number]  -> works like /thread but instead opens external media in mpv

    Sample commands
    -----------------
    /listboards
    /board v
    /board g 3
    /thread v 8
    /image g 5
    """

    def __init__(self, command):
        if command == None:
            self.args = None
            return
        if command[0] == '/' and len(command) > 1: # confirms the user is in command mode
            self.args = command.lstrip('/').split()
        else:
            self.args = None
            return

    def goto_board(self):
        args = self.args

        if args[0] == 'board':
            if len(args) == 2:
                args.append('1')
                return args

            elif len(args) == 3:
                if args[2].isnumeric():
                    return args
        return

    def goto_thread(self):
        args = self.args

        if len(args) == 3 and args[0] == 'thread':
            if args[2].isnumeric():
                return args
        return

    def show_boards(self):
        args = self.args

        if len(args) == 1 and args[0] == 'listboards':
            return args
        return

    def view_media(self):
        args = self.args

        if len(args) == 3 and args[0] == 'image':
            if args[2].isnumeric():
                return args
        return

    def goto_help(self):
        args = self.args

        if len(args) == 1 and args[0] == 'help':
            return args
        return

class CommandRouter:
    def __init__(self, screen, win, text=None, thread_table=None):
        self.box_text = text
        self.screen = screen
        self.cmd = CommandParse(self.box_text)
        self.win = win
        self.thread_table = thread_table
        self.route = State(screen, thread_table)

    def menu_boards(self):
        return self.route.boards('/listboards')

    def menu_thread(self):
        if self.thread_table is None:
            return

        menu = [
            (
                str(index), 
                lambda i=index: self.route.thread(
                    f'/thread {self.thread_table.board} {i}'
                )
            )
            for index in self.thread_table.table
        ]

        return menu

    def menu_images(self):
        if self.thread_table is None:
            return

        menu = [
            (
                str(index), 
                lambda i=index: self.route.images(
                    f'/image {self.thread_table.board} {i}'
                )
            )
            for index in self.thread_table.table
        ]

        return menu

    def menu_help(self):
        return self.route.get_help('/help')

    @staticmethod
    def bad_command(window, err):
        window.erase()
        window.addstr(err)
        window.refresh()
        curses.napms(1200)
        window.erase()

    def cmd_mode(self, thread_table=None):
        if self.cmd.args:
            try:
                match self.cmd.args[0]:
                    case 'board': 
                        return self.route.index(self.box_text)
                    case 'thread' if self.thread_table and self.thread_table.table: 
                        return self.route.thread(self.box_text)
                    case 'listboards': 
                        return self.route.boards(self.box_text)
                    case 'image' if self.thread_table and self.thread_table.table: 
                        return self.route.images(self.box_text)
                    case 'help': 
                        return self.route.get_help(self.box_text)
                    case _: 
                        raise InvalidCommand

            except InvalidCommand:
                self.bad_command(self.win, 'Invalid Command')

            except BadRequest:
                self.bad_command(self.win, 'No such location')

            except KeyError:
                self.bad_command(self.win, 'No such index')

            except api.MediaError as e:
                self.bad_command(self.win, str(e))

            except api.APIError as e:
                self.bad_command(self.win, str(e))

            except InvalidIndexContext as e:
                self.bad_command(self.win, str(e))

@dataclass
class Metadata:
    title: str = 'Welcome to yotsuba-cli!'
    controls: str = '(j k, ↑ ↓) scroll (b) back (q) quit) (/) command (?) help'

class State:
    def __init__(self, screen, thread_table=None):
        self.screen = screen
        self.meta = Metadata()
        self.thread_table = thread_table
        self.view_function = None
        self.format_function = None
        self.location = None
        self.board = None
        self.use_thread_table = False
        self.local = False
        self.main_screen = False

    def view(self, *args):
        viewer = render.Interface(self.screen, self, CommandRouter, self.meta)
        loading_screen = viewer.loading
        error_screen = viewer.error
        viewer.set_content(loading_screen)

        try:
            data = self.view_function(*args)
        except api.APIError:
            viewer.set_content(error_screen)
            return viewer.scroll(end_marker=False)

        if self.format_function == render.YotsubaFormatter.post_format:
            content, self.thread_table = self.format_function(data, self.location, self.board, self.use_thread_table)
        else:
            content = self.format_function(data)
        
        viewer.set_content(content)

        return viewer.scroll(thread_table=self.thread_table, main=self.main_screen)

    def boards(self, command, main=False):
        cmd = CommandParse(command)
        args = cmd.show_boards()

        if not args:
            raise InvalidCommand

        self.view_function = api.get_boards
        self.format_function = render.YotsubaFormatter.boards_format
        self.main_screen = main

        return self.view()

    def index(self, command):
        cmd = CommandParse(command)
        args = cmd.goto_board()
        
        if not args:
            raise InvalidCommand

        self.use_thread_table = True
        self.view_function = api.get_index 
        self.format_function = render.YotsubaFormatter.post_format
        self.location = 'threads' # json location
        self.board = args[1]

        return self.view(self.board, args[2])

    def thread(self, command):
        cmd = CommandParse(command)
        args = cmd.goto_thread()

        if not args:
            raise InvalidCommand

        self.view_function = api.get_thread 
        self.format_function = render.YotsubaFormatter.post_format
        self.location = 'posts'
        self.board = args[1]

        if self.board != self.thread_table.board:
            err = f'Index belongs to /{self.thread_table.board}/ not /{self.board}/'
            raise InvalidIndexContext(err)

        return self.view(self.board, self.thread_table.table[args[2]])

    def images(self, command):
        cmd = CommandParse(command)
        args = cmd.view_media()

        if not args:
            raise InvalidCommand

        try:
            thread = self.thread_table.table[args[2]]
        except KeyError:
            raise InvalidCommand

        self.board = args[1]

        if self.board != self.thread_table.board:
            err = f'Index belongs to /{self.thread_table.board}/ not /{self.board}/'
            raise InvalidIndexContext(err)

        api.get_media(self.board, thread)

    def get_help(self, command):
        cmd = CommandParse(command)
        args = cmd.goto_help()

        if not args:
            raise InvalidCommand

        self.view_function = help.get
        self.format_function = render.generic_format
        self.local = True

        return self.view()

def main(screen):
    screen.erase()
    screen.addstr(0, 0, "loading...")
    screen.refresh()

    current_view = 'boards'

    curses.init_pair(1, curses.COLOR_GREEN, curses.COLOR_BLACK)
    curses.init_pair(2, curses.COLOR_YELLOW, curses.COLOR_BLACK)
    curses.init_pair(3, curses.COLOR_CYAN, curses.COLOR_BLACK)
    curses.init_pair(4, curses.COLOR_BLUE, curses.COLOR_BLACK)
    curses.init_pair(5, curses.COLOR_MAGENTA, curses.COLOR_BLACK)
    curses.init_pair(6, curses.COLOR_RED, curses.COLOR_BLACK)

    if current_view == 'boards':
        main = State(screen)
        main.boards('/listboards', main=True)

if __name__ == "__main__":
    wrapper(main)
