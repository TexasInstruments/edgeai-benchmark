import sys
import time
from colorama import Fore
from tqdm.auto import tqdm
from .timer_utils import display_time_bar

__all__ = ['progress_step', 'progress_step_tqdm', 'progress_step_lite']


######################################################################
# utility functions
def _progress_miniters(iterable, total=None):
    iter_length = len(iterable) if hasattr(iterable, '__len__') else total
    miniters = max(iter_length//100, 1) if iter_length is not None else 1
    return miniters


def _progress_format(desc_len=60, colors=None):
    if colors is not None:
        assert len(colors) == 4, f'colors must have length 4'
        colors = (Fore.GREEN, Fore.YELLOW, Fore.BLUE, Fore.CYAN) if colors is None else colors
        format_arg = (colors[0], desc_len, colors[1], colors[2], colors[3], Fore.RESET)
        bar_format = '%s{desc:%s}|%s{percentage:4.0f}%%|%s{bar:10}|%s{r_bar}%s' % format_arg
    else:
        bar_format = '{desc:%s}|{percentage:4.0f}%%|{bar:10}|{r_bar}' % desc_len
    #
    return bar_format


def _progress_desc(desc, desc_len=60):
    desc = desc[:desc_len] if (desc_len is not None and len(desc) > desc_len) else \
        desc + ' '*(desc_len-len(desc))
    return desc


######################################################################
def progress_step_tqdm(iterable, desc, desc_len=60, total=None, miniters=None, maxinterval=10.0, bar_format=None,
                       file=sys.stdout, leave=True, colors=None, **kwargs):
    """
    Uses a tqdm variant that updates only once in miniters steps
    """
    desc = _progress_desc(desc, desc_len)
    miniters = _progress_miniters(iterable, total) if miniters is None else miniters
    bar_format = _progress_format(desc_len, colors) if bar_format is None else bar_format
    return TqdmStep(iterable=iterable, desc=desc, total=total, miniters=miniters, bar_format=bar_format, file=file,
                maxinterval=maxinterval, leave=leave, **kwargs)


class TqdmStep(tqdm):
    """
    A tqdm variant that updates even before the first iteration,
    and also updates only once in miniters
    """
    def __init__(self, iterable, *args, miniters=None, maxinterval=10.0, **kwargs):
        super().__init__(iterable, *args, miniters=miniters, maxinterval=maxinterval, **kwargs)
        assert 'miniters' is not None, 'miniters must be provided'
        self.step_size = miniters
        self.iter_index = 0
        self.num_completed = 0
        # display bar even before the first iteration
        # useful if the first iteration itself  takes some time
        display_time_bar(self.desc, self.num_completed, total=self.total, start_time=0,
                         end_time=0, file=self.fp)


######################################################################
# a lighter version of progress_step that doesn't use tqdm
# this prints the iteration descriptor even before the first iteration

def progress_step_lite(iterable, desc, desc_len=60, total=None, miniters=None, colors=None, **kwargs):
    desc = _progress_desc(desc, desc_len)
    miniters = _progress_miniters(iterable, total) if miniters is None else miniters
    colors = (Fore.GREEN, Fore.YELLOW, Fore.BLUE, Fore.CYAN) if colors is None else colors
    return ProgressStepLite(iterable, desc, miniters=miniters, colors=colors, **kwargs)


class ProgressStepLite:
    """
    A simple progress indicator that can be used instead of tqdm
    This has an advantage that this starts updating the status in the 0th iteration
    (i.e. before even first iteration is complete)
    Author: Manu Mathew
    2021 Feb 16
    """
    def __init__(self, iterable, desc, miniters=1, total=None, file=None,
                 colors=None, position=0, **kwargs):
        super().__init__()
        self.iterable = iterable
        self.desc = desc
        self.step_size = miniters
        self.total = iterable.__len__() if hasattr(iterable, '__len__') else total
        self.file = file if file is not None else sys.stdout
        self.colors = colors
        self.position = position
        self.num_completed = 0
        self.start_time = time.time()
        self.move_up_str = '\033[F' #'\x1b[A'
        self.move_down_str = '\n'

    def __iter__(self):
        self.start_time = time.time()
        self.update(0)
        for item_id, item in enumerate(self.iterable):
            yield item
            # when update is called from within the loop, it will display the bar
            # only at the specified step_size
            self.update(1, force=False)
        #

    # when update is explicitly called, it will display the bar
    def update(self, n, force=True):
        self.num_completed += n
        end_time = time.time()
        if force or (self.num_completed % self.step_size) == 0 or (self.num_completed == self.total):
            self._set_position()
            display_time_bar(self.desc, self.num_completed, total=self.total, start_time=self.start_time,
                             end_time=end_time, file=self.file, colors=self.colors)
            self._reset_position()
        #

    def close(self):
        pass

    def _set_position(self):
        pos_str = self.move_up_str*self.position
        self.file.write(pos_str)
        self.file.flush()

    def _reset_position(self):
        pos_str = self.move_down_str*self.position
        self.file.write(pos_str)
        self.file.flush()


######################################################################
# the default progress_step
progress_step = progress_step_tqdm
