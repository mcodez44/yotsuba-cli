import html
import curses
from curses.textpad import Textbox
from html.parser import HTMLParser
from dataclasses import dataclass

LOADING_SCREEN = [
    [('Yotsuba-cli', 'subject')],
    [('', 'default')],
    [('Loading...', 'default')]
]

ERROR_SCREEN = [
    [('Yotsuba-cli', 'subject')],
    [('', 'default')],
    [('Error: could not reach api', 'error')],
    [('', 'default')],
    [('Press q to quit, or try again later.', 'default')]
]

def get_theme():
    themes = {
        '4u': {
            'default': curses.A_NORMAL,
            'post_number': curses.color_pair(2),
            'post_trip': curses.color_pair(1),
            'board_highlight': curses.color_pair(1),
            'timestamp': curses.color_pair(3),
            'divider': curses.color_pair(4) | curses.A_BOLD,
            'name': curses.color_pair(2) | curses.A_BOLD,
            'filename': curses.color_pair(5),
            'subject': curses.color_pair(3) | curses.A_BOLD,
            'greentext': curses.color_pair(1),
            'redtext': curses.color_pair(6),
            'spoiler': curses.A_NORMAL,
            'error': curses.color_pair(6) | curses.A_BOLD
            },

        'space': {
            'default': curses.A_NORMAL,
            'post_number': curses.color_pair(3),
            'post_trip': curses.color_pair(5),
            'board_highlight': curses.color_pair(2) | curses.A_BOLD,
            'timestamp': curses.color_pair(4) | curses.A_DIM,
            'divider': curses.color_pair(4) | curses.A_DIM,
            'name': curses.color_pair(1) | curses.A_BOLD,
            'filename': curses.color_pair(3),
            'subject': curses.color_pair(2) | curses.A_BOLD,
            'greentext': curses.color_pair(1),
            'redtext': curses.color_pair(3),
            'spoiler': curses.color_pair(5),
            'error': curses.color_pair(6) | curses.A_BOLD
            },

        'monochrome': {
            'default': curses.A_NORMAL,
            'post_number': curses.A_NORMAL,
            'post_trip': curses.A_NORMAL,
            'board_highlight': curses.A_BOLD,
            'timestamp': curses.A_DIM,
            'divider': curses.A_DIM,
            'name': curses.A_BOLD,
            'filename': curses.A_NORMAL,
            'subject': curses.A_BOLD,
            'greentext': curses.A_NORMAL,
            'redtext': curses.A_NORMAL,
            'spoiler': curses.A_NORMAL,
            'error': curses.A_BOLD
            }
        }

    return themes

class HTMLFilter(HTMLParser):
    def __init__(self):
        super().__init__()

        self.blocks = []
        self.buffer = ''
        self.attr = 'default'

    def flush_buffer(self):
        if self.buffer:
            self.blocks.append(RawBlock(self.buffer, self.attr, indent=2))
        self.buffer = ''

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)

        if tag == 'span' and attrs.get('class') == 'quote':
            self.flush_buffer()
            self.attr = 'greentext'

        elif tag == 'a' and attrs.get('class') == 'quotelink':
            self.flush_buffer()
            self.attr = 'redtext'

        if tag == 'br':
            if self.buffer:
                self.flush_buffer()
            else:
                self.blocks.append(NewlineBlock())

            self.attr = 'default'

    def handle_endtag(self, tag):
        if tag in ('span', 'a'):
            self.flush_buffer()
            self.attr = 'default'

    def handle_data(self, data):
        self.buffer += data

    def cleanup(self, data, no_rawblock=False):
        self.blocks = []
        self.buffer = ''
        self.attr = 'default'

        if no_rawblock:
            return html.unescape(data)

        data = html.unescape(data)
        self.feed(data)

        self.flush_buffer()

        return BlockGroup(*self.blocks)

class BlockGroup:
    """
    Groups multiple Block objects into a single content group.
    Intended for freeform text composed of multiple styled raw blocks.
    """

    def __init__(self, *blocks):
        self.blocks = blocks

class RawBlock:
    """ Intended for raw text content
    Assembles text attr paits into a single coherent block object.
    """

    __slots__ = ('text', 'attr', 'lines', 'indent')
    # correspond to text, and dict keys to curses color attributes

    def __init__(self, text, attr='default', indent=0):
        self.text = str(text)
        self.attr = attr
        self.lines = str(text).splitlines()
        self.indent = indent

class ElementBlock:
    """ Intended for UI Elements
    Takes (text, attr) pairs as arugments. An ElementBlock object groups
    together these pairs as a single block. Thus being a single block, it has
    its own width based on the sum of the width of the combined text.
    """

    __slots__ = ('pairs')

    def __init__(self, *pairs):
        self.pairs = list(pairs)

    def width(self):
        return sum(len(t) for t, _ in self.pairs)

    def output(self):
        return self.pairs

class LinebreakBlock:
    """Only performs linebreaks on the layout.
    Maintains the same block identity
    """

    def __init__(self):
        pass

class NewlineBlock:
    """Solely for newlines.
    Represents a semantic break and advances block identity
    """

    __slots__ = ('count')
    def __init__(self, count=1):
        self.count = count

@dataclass
class Line:
    block_index: int # identifies the logical block
    char_offset: int # identifies where its physical line starts inside that block
    spans: tuple[Span, ...]

@dataclass(frozen=True)
class Span:
    text: str
    attr: str = 'default'

@dataclass(frozen=True)
class WrappedPart:
    text: str
    offset: int

def flatten_blocks(blocks):
    for block in blocks:
        if isinstance(block, BlockGroup):
            yield from flatten_blocks(block.blocks)
        else:
            yield block

def chunks2lines(chunks, width, custom_style=None):
    """
    Core of the renderer.

    Converts block objects into wrapped terminal lines.

    Takes RawBlock, ElementBlock, and NewlineBlock objects and produces a
    list of lines containing (text, attr) pairs. Raw text is wrapped to the
    given width, ElementBlock objects preserve grouped UI elements while
    wrapping, and NewlineBlocks explicitly terminate the current line.
    """

    total_lines = []
    current_line = []
    current_line_start = 0
    index = 0

    # current_line_start must be preserved when LinebreakBlock flushes
    # the pending line or resize anchoring becomes off by one

    for block in flatten_blocks(chunks):
        if isinstance(block, ElementBlock):
            index += 1

            current_width = 0
            current_line = []

            element_pos = 0
            current_line_start = 0

            for element, attr in block.output():
                element_start = element_pos

                # a single element is too wide for the terminal
                if len(element) > width:

                    # flush what's already on the current line first
                    if current_line:
                        total_lines.append(
                            Line(
                                block_index=index, 
                                char_offset=current_line_start,
                                spans=tuple(current_line)
                            )
                        )

                        current_line = []
                        current_width = 0

                    for part in wrap_lines(width, element):
                        total_lines.append(
                            Line(
                                block_index=index, 
                                char_offset=element_start+part.offset,
                                spans=(Span(part.text, attr),)
                            )
                        )

                    element_pos += len(element)
                    current_line_start = element_pos
                    continue # this element is done so move on to the next
                
                # an element that would otherwise fit plus the buffer is too wide for the terminal
                if current_width + len(element) > width:
                    total_lines.append(
                        Line(
                            block_index=index, 
                            char_offset=current_line_start,
                            spans=tuple(current_line),
                        )
                    )
                    current_line = []
                    current_width = 0

                    # this new physical line begins where this element begins
                    current_line_start = element_start

                current_line.append(Span(element, attr))
                current_width += len(element)
                element_pos += len(element)

        elif isinstance(block, RawBlock):
            index += 1
            indent = block.indent * ' '

            for line in block.lines:
                for part in wrap_lines(width, line):
                    current_line.append(Span(indent + part.text, block.attr))

                    total_lines.append(
                        Line(
                            block_index=index, 
                            char_offset=part.offset, 
                            spans=tuple(current_line)
                        )
                    )

                    current_line = [] # flush the finished line

        elif isinstance(block, NewlineBlock):
            # always flushes the line
            index += 1

            total_lines.append(
                Line(
                    block_index=index, 
                    char_offset=current_line_start,
                    spans=tuple(current_line)
                )
            )

            current_line = []
            current_width = 0

        elif isinstance(block, LinebreakBlock):
            # breaks the current line

            if current_line:
                total_lines.append(
                    Line(
                        block_index=index, 
                        # preserve the source position of the pending line
                        # hardcoding zero here breaks resize anchoring for ElementBlocks
                        char_offset=current_line_start,
                        spans=tuple(current_line)
                    )
                )
                current_line = []
                current_width = 0

    return total_lines # list of lines in (text, attr) pairs

def wrap_lines(width, data):
    output = []

    for raw in str(data).splitlines():
        if not raw:
            output.append(WrappedPart("", 0))
            continue

        start = 0

        while start < len(raw):
            if start+width >= len(raw):
                end = len(raw)
            else:
                end = start+width

            # break on space
            if end < len(raw):
                space = raw.rfind(' ', start, end + 1)

                if space > start:
                    end = space

            part = raw[start:end]

            output.append(WrappedPart(part, start))

            start = end

            while start < len(raw) and raw[start] == ' ':
                start += 1

    return output

class ThreadRouter:
    """Routes shorthand numbers to their corresponing threads"""

    def __init__(self, board, use_table): # create_table must be True or False
        self.use_table = use_table
        self.board = board
        self.thread = None
        self.table = {}

    def add_route(self, index, thread):
        self.table[str(index)] = thread.strip()

@dataclass
class PostInfo:
    number: int
    time: str
    name: str
    trip: str = ''
    filename: str = ''
    extension: str = ''
    subject: str = ''
    comment: str = ''

@dataclass
class BoardsInfo:
    board: str
    title: str
    worksafe: bool

class YotsubaFormatter:
    """4chan specific formatting routines"""

    @staticmethod
    def post_format(raw_json, location, board=None, use_thread_table=False):

        # No. 1 123456 00:00:00 Anonymous [file.png]
        # ------------------------------------------------------------Subject
        # comment

        formatted = []
        head = []
        border = []

        router = ThreadRouter(board, use_thread_table)

        for index, entry in enumerate(raw_json[location]):
            if router.use_table: # board_index specific
                location = entry['posts'][0]
                thread = str(location['no']) + ' '
                router.add_route(index+1, thread)
            else:
                location = entry

            post = PostInfo(
                        number = index+1,
                        time = location['now'],
                        name = location['name'],
                        trip = location.get('no', ''),
                        filename = location.get('filename', ''),
                        extension = location.get('ext', ''),
                        subject = location.get('sub', ''),
                        comment = location.get('com', '')
                    )

            html = HTMLFilter()
            subject = html.cleanup(post.subject, no_rawblock=True)
            comment = html.cleanup(post.comment)

            # these values are all formatted in text, attr pairs
            # Each args are treated as differnt ui blocks
            # Blocks can be grouped with an ElementBlock object
            head = ElementBlock(
                        ('#' + str(post.number) + ' ', 'post_number'), 
                        (str(post.trip) + ' ', 'post_trip'),
                        (post.time + ' ', 'timestamp'), 
                        (post.name + ' ', 'name'), 
                        ('[' + post.filename if post.filename else '', 'filename'), 
                        (post.extension + ']' if post.filename else '', 'filename')
                    )

            linebreak = LinebreakBlock() # linebreak blocks are specifically for elements
            newline = NewlineBlock() # newline blocks are specifcally for newlines

            border = ElementBlock(
                        ('-'*60 + ' ', 'divider'),
                        (subject, 'subject')
                    )

            # composition of the post/thread
            node = (head, linebreak, border, linebreak, comment, newline)

            for n in node:
                formatted.append(n)

        return formatted, router

    @staticmethod
    def boards_format(raw_json):
        output = []
        linebreak = LinebreakBlock()
        for entry in raw_json['boards']:

            boards = BoardsInfo(
                        board=entry['board'],
                        title=entry['title'],
                        worksafe=True if entry['ws_board'] == 1 else False
                    )

            line = ElementBlock(
                        ('/', 'default'),
                        (boards.board, 'board_highlight'),
                        ('/ - ', 'default'),
                        (boards.title, 'default')
                    )

            output.append(line)
            output.append(linebreak)

        return output

def generic_format(data):
    """Intended for generic structured UI content.
Takes lines containing (text, attr) pairs and groups each line into a single
ElementBlock, followed by a NewlineBlock.
    """

    blocks = []
    newline = NewlineBlock()
    linebreak = LinebreakBlock()

    for line in data:
        blocks.append(ElementBlock(*line))
        blocks.append(linebreak)

    return blocks

def str_format(text): # not used at the moment
    """Solely for raw strings"""

    chunk = [RawBlock(text, 'default')] # a chunk must be enclosed in an array

    return chunk

class Interface:
    def __init__(self, screen, mode, command_router, meta):
        self.screen = screen
        self.mode = mode
        self.route = command_router
        self.meta = meta
        self.theme = get_theme()['space']
        self.loading = generic_format(LOADING_SCREEN)
        self.error = generic_format(ERROR_SCREEN)
        self.end_marker = True

        self.cmd_win = None
        self.status_win = None

        self.data = None
        self.rows = None
        self.cols = None

        self.anchor = 0

    def set_content(self, data):
        self.data = data
        curses.curs_set(0)

        self.rows, self.cols = self.screen.getmaxyx()

        content = chunks2lines(self.data, self.cols-3)

        self.end_marker = False

        pad, _ = self.build_pad(content)
        self.init_windows()
        self.redraw(pad, 0)

    def build_pad(self, content):
        width = self.cols

        if self.end_marker:
            index = content[-1].block_index if content else 0
            content.append(
                        Line(
                            index, 
                            0, 
                            (Span(':', 'default'),)
                        )
                    )

        pad = curses.newpad(len(content)+1, width-1)

        for y, line in enumerate(content):
            pad.move(y, 0)

            for span in line.spans:
                attr = self.theme[span.attr]
                text = span.text
                pad.addstr(text, attr)

        return pad, len(content)

    def get_anchor(self, content, i):
        line = content[i]

        return line.block_index, line.char_offset

    def restore_anchor(self, content, block_index, char_offset):
        best = None

        for y, line in enumerate(content):
            if line.block_index != block_index:
                continue

            if line.char_offset <= char_offset:
                best = y
            else:
                break

        if best is not None:
            return best

        # fallback: first line belonging to the block
        for y, line in enumerate(content):
            if line.block_index == block_index:
                return y

        return 0

    def init_windows(self):
        self.cmd_win = curses.newwin(1, self.cols-2, self.rows-1, 2)
        self.status_win = curses.newwin(1, self.cols, self.rows-2, 0)

        self.status_win.bkgd(' ', curses.A_REVERSE)

    def redraw(self, pad, i, scroll_status=0):
        if self.meta:
            status_info = self.meta.controls
        else:
            status_info = ''

        self.screen.erase()
        self.screen.addstr(self.rows-1, 0, '>>')
        self.screen.noutrefresh()

        pad.noutrefresh(i, 0, 0, 0, self.rows-2, self.cols-1)

        percent = f'{scroll_status}%'
        x = max(0, self.cols - len(percent)-1)

        self.status_win.erase()

        self.status_win.addnstr(0, 0, status_info, max(self.cols-1, 0)) # left adjust
        self.status_win.addnstr(0, x, percent, max(self.cols - x - 1, 0)) # right adjust

        self.status_win.noutrefresh()
        self.cmd_win.noutrefresh()

        curses.doupdate()

    def scroll(self, thread_table=None, main=False, end_marker=True):
        curses.curs_set(0)

        self.end_marker=end_marker

        self.rows, self.cols = self.screen.getmaxyx()

        content = chunks2lines(self.data, self.cols-3)

        pad, content_size = self.build_pad(content)
        self.init_windows()

        i = 0
        header = 0

        self.redraw(pad, i)

        while True:
            if curses.is_term_resized(self.rows, self.cols):
                anchor_block, anchor_offset = self.get_anchor(content, i)

                self.rows, self.cols = self.screen.getmaxyx()

                curses.resizeterm(self.rows, self.cols)

                content = chunks2lines(self.data, self.cols-3)

                i = self.restore_anchor(content, anchor_block, anchor_offset)

                pad, content_size = self.build_pad(content)
                self.init_windows()

                visible_rows = self.rows - 2

                footer = max(0, content_size - visible_rows)
                i = min(i, footer)

            footer = max(header, content_size - (self.rows-2))
            scroll_status = round(i / footer * 100) if footer != 0 else 0

            self.redraw(pad, i, scroll_status)

            try:
                key = self.screen.getch()
            except KeyboardInterrupt:
                return "quit"


            if key in {ord('j'), curses.KEY_DOWN}: # Scroll down
                i = min(i + 1, footer)
            elif key in {ord('k'), curses.KEY_UP}: # Scroll up
                i = max(i - 1, header)
            elif key in {ord('J'), curses.KEY_NPAGE}: # Scroll page down
                i = min(i + self.rows-3, footer)
            elif key in {ord('K'), curses.KEY_PPAGE}: # Scroll page up
                i = max(i - self.rows+3, header)
            elif key in {ord('G'), curses.KEY_END}: # Jump to bottom
                i = footer
            elif key in {ord('g'), curses.KEY_HOME}: # Jump to bottom
                i = header

            elif key == ord('\t'): # Open quick menu
                menu_router = self.route(self.screen, self.cmd_win, thread_table=thread_table)

                def redraw_background():
                    self.redraw(pad, i, scroll_status)

                parent_menu = QuickMenu(
                                self.screen,
                                [
                                    ('boards', menu_router.menu_boards),
                                    ('thread', SubMenu(menu_router.menu_thread)),
                                    ('images', SubMenu(menu_router.menu_images)),
                                    ('help', menu_router.menu_help)
                                ], redraw_background
                            )

                result = parent_menu.run()

                if result == "quit":
                    return "quit"

            elif key == ord('/'): # Command mode
                curses.curs_set(1)

                text = self.reset_textbox()
                router = self.route(self.screen, self.cmd_win, text, thread_table)
                result = router.cmd_mode()

                curses.curs_set(0)

                if result == "quit":
                    return "quit"

            elif key == ord('?'): # Help menu shortcut
                router = self.route(self.screen, self.cmd_win, '/help', thread_table)
                result = router.cmd_mode()

                curses.curs_set(0)

                if result == "quit":
                    return "quit"

            elif key == ord('b'): # back
                if not main:
                    return "back"
            elif key == ord('q'): # Quit
                return "quit"

    def reset_textbox(self):
        state = {'resized': False}

        @staticmethod
        def textbox_input(key):
            if key == curses.KEY_RESIZE:
                state['resized'] = True

                return 7 # ctrl-g: tells the textbox to stop editing

            return key

        self.cmd_win.addstr('/')

        tb = Textbox(self.cmd_win)
        self.screen.refresh()
        tb.edit(textbox_input)

        if state['resized']:
            self.cmd_win.erase()
            return '/'

        tb_text = '/' + tb.gather()

        self.cmd_win.erase()
        self.cmd_win.refresh()

        return tb_text

class SubMenu:
    def __init__(self, function):
        self.function = function

class QuickMenu:
    def __init__(self, screen, items, redraw_background):
        self.screen = screen
        self.win = None
        self.items = items
        self.width = max(len(name) for name, _ in self.items) + 3
        self.stack = []
        self.selected = 0
        self.redraw_background = redraw_background
        self.offset = 0

    def open_submenu(self, items, offset):
        self.stack.append((self.items, self.selected))
        self.items = items
        self.selected = 0
        self.offset = offset

    def go_back(self):
        # determines whether or not the user can go back menus
        if not self.stack:
            return False

        self.items, self.selected = self.stack.pop() # last submenu in the stack

        return True

    def clear(self):
        if self.win:
            self.win.erase()
            self.win.noutrefresh()
            curses.doupdate()

    def draw(self):
        rows, cols = self.screen.getmaxyx()

        width = max(len(name) for name, _ in self.items) + 3
        height = len(self.items)

        start_y = max(0, rows-height-2)
        start_x = 2 + self.offset 

        self.win = curses.newwin(height, width, start_y, start_x)
        self.win.erase()

        for i, (name, _) in enumerate(self.items):
            attr = curses.A_REVERSE if i == self.selected else curses.A_NORMAL
            rjust = width - len(name)
            self.win.addnstr(i, 0, ' ' + name + ' ' * rjust, width-1, attr)

        self.win.noutrefresh()
        curses.doupdate()

    def run(self):
        while True:
            self.draw()
            key = self.win.getch()

            if key == curses.KEY_RESIZE:
                return

            if key in {ord('j'), curses.KEY_DOWN, ord('\t')}:
                self.selected = (self.selected + 1) % len(self.items)

            elif key in {ord('k'), curses.KEY_UP, curses.KEY_BTAB}:
                self.selected = (self.selected - 1) % len(self.items)

            elif key in {10, 13, curses.KEY_ENTER}:
                _, target = self.items[self.selected]

                if isinstance(target, SubMenu):
                    items = target.function()
                    offset = self.width
                    if items:
                        self.open_submenu(items, offset-1)

                elif callable(target):
                    return target()

            elif key == 27: # Escape key
                if self.go_back():
                    self.offset = 0
                    self.clear()
                    self.redraw_background()
                    self.draw()
                    continue

                # closes the root quick menu
                self.redraw_background()
                return

            elif key == ord('q'):
                return "quit"
