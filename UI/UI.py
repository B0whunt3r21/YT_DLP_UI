from textual.app import App, ComposeResult
from textual.widgets import (
    Header,
    Footer,
    Button,
    Input,
    Label,
    Static,
    SelectionList,
    DirectoryTree,
    Switch,
    RadioButton,
    RadioSet
)
from textual.containers import Container, Horizontal, Vertical, VerticalScroll, Grid
from textual.widgets import Static, Select
from textual.reactive import reactive
from textual import on, work

from rich.text import Text

from pathlib import Path

from API.API import API

class DirTree(DirectoryTree):
    def __init__(self, path, selectors=None, **kwargs):
        super().__init__(path, **kwargs)
        self.__selectors = selectors

    @property
    def selectors(self):
        return self.__selectors
    
    @selectors.setter
    def selectors(self, selectors):
        self.__selectors = selectors

    #Auto call on create and update DirectoryTree (Polymorphism form Parent)
    def filter_paths(self, paths):
        filtered = [
            path for path in paths
            if not path.name.startswith(".")
            ]

        if self.selectors == []: 
            return [p for p in filtered if p.is_dir()]
        if not self.selectors or self.selectors == "dir":
            return filtered
        else:
            return [
                p for p in filtered
                if p.is_dir() or p.suffix.lower() in self.selectors
            ]



class FileSelect(Static):
    def __init__(self, path, title, filter=None, **kwargs):
        super().__init__(**kwargs)
        self.__path = Path(path).resolve()
        self.__title = title
        self.__selected_file: Path | None = None
        self.__filter = filter
        self.__replacing = False


    @property
    def path(self):
        return self.__path
    
    @path.setter
    def path(self, path):
        self.__path = Path(path).resolve()
    
    @property
    def title(self):
        return self.__title
    
    @title.setter
    def title(self, title):
        self.__title = title

    @property
    def selected_file(self):
        return self.__selected_file
    
    @selected_file.setter
    def selected_file(self, selected_file):
        self.__selected_file = selected_file

    @property
    def filter(self):
        return self.__filter
    
    @filter.setter
    def filter(self, filter):
        self.__filter = filter


    BINDINGS = [
        ("backspace", "go_up", "Go Up")
        ,("u", "rootPath", "User Root")
        ,("p", "projPath", "Project Root")
    ]

    
    def action_rootPath(self):
        root = Path.home()
        if not root.exists():
            root = Path('./in/').resolve()
        self.replaceTree(root)


    def action_projPath(self):
        root = Path('.').resolve()
        self.replaceTree(root)

    
    def action_go_up(self):
        tree = self.query_one("#tree", DirectoryTree)
        current = tree.path
        parent = current.parent

        if parent == current:
            return

        self.replaceTree(parent)


    def replaceTree(self, new_path: Path):
        if self.__replacing:
            pass

        self._replacing = True

        old = self.query_one("#tree", DirectoryTree)
        parent = old.parent
        old.remove()

        def mount_new():
            new = DirTree(new_path, self.filter, id="tree")
            parent.mount(new)
            self.path = new_path
            self.update_breadcrumb(new_path)
            self.refresh(layout=True)

            self.__replacing = False

        self.call_after_refresh(mount_new)


    def update_breadcrumb(self, path: Path):
        self.query_one("#breadcrumb", Label).update(path.as_posix())


    def compose(self) -> ComposeResult:
        with Vertical(id="fileSelect"):
            yield Label(self.title, id="lbl_img")

            with Horizontal(id='toolbar'):
                yield Button("↑", id="btn_up")
                yield Label(self.path.as_posix(), id="breadcrumb")

            yield DirTree(self.path, self.filter, id="tree")


    @on(DirectoryTree.NodeExpanded)
    def update_on_dir_enter(self, event: DirectoryTree.NodeExpanded):
        self.path = event.node.path
        self.update_breadcrumb(self.path)

    @on(DirectoryTree.FileSelected)
    def file_selected(self, event: DirectoryTree.FileSelected):
        self.selected_file = event.path

    @on(DirectoryTree.DirectorySelected)
    def directory_selected(self, event: DirectoryTree.DirectorySelected):
        self.path = event.path
        self.selected_file = event.path
        self.update_breadcrumb(self.path)

    @on(DirectoryTree.NodeExpanded)
    @on(DirectoryTree.NodeCollapsed)
    def resize_tree(self):
        self.refresh(layout=True)

    @on(Button.Pressed, "#btn_up")
    def up_pressed(self):
        self.action_go_up()


    @property
    def value(self):
        return self.selected_file or self.path



class UI(App):
    CSS_PATH = "UI.css"


    toggleFormat = reactive(0) #0: audio; 1: video


    BINDINGS = [
        ("q", "quit", "Quit")
        ,("a", "audio", "Audio")
        ,("v", "video", "Video")
    ]


    def action_reload(self):
        outSel = self.query_one('#out_sel', FileSelect)
        urlField = self.query_one('#url_fld', Input)

        outSel.replaceTree(outSel.path)
        urlField.value = ''


    def action_audio(self):
        self.toggleFormat = 0
        btn_audio = self.query_one("#mp3_btn", RadioButton)
        btn_audio.value = True


    def action_video(self):
        self.toggleFormat = 1
        btn_video = self.query_one("#mp4_btn", RadioButton)
        btn_video.value = True


    def watch_toggleFormat(self, toggleFormat: int):
        btn_audio = self.query_one("#mp3_btn", RadioButton)
        btn_video = self.query_one("#mp4_btn", RadioButton)

        if toggleFormat == 0: #audio
            btn_audio = True
        else: #video
            btn_video = True


    @on(RadioSet.Changed, "#formats_sel")
    def format_selected(self, event: RadioSet.Changed) -> None:
        buttons = self.query_one("#formats_sel", RadioSet)
        idx = buttons.pressed_index
        self.format_selected = idx

    @on(Button.Pressed, "#run_btn")
    def execute(self):
        url = self.query_one("#url_fld", Input).value
        mode = self.format_selected
        outFolder = self.query_one("#out_sel", FileSelect).value

        if url.strip():
            self.run_API(url, mode, outFolder)

    @work(thread=True)
    def run_API(self, url, mode, outFolder):
        try:
            yt_dlp = API()
            url = yt_dlp.sanitizeYoutubeURL(url)
            yt_dlp.download(url, mode, outFolder)

            self.notify("Download completed successfully!", title="Success")
            
        except Exception as e:
            self.notify(f"Download failed: {e}", title="Error", severity="error")



    def compose(self) -> ComposeResult:
        yield Header()

        with VerticalScroll(id="body"):

            #Title
            with Horizontal(id="header"):
                yield Static("YT-DLP UI", id="title")

            #URL
            with Horizontal(id="url"):
                yield Static("URL:", id="url_lbl")
                yield Input(placeholder="https//:", id="url_fld")

            #Formats
            with Horizontal(id="formats"):
                with RadioSet(id="formats_sel"):
                    yield RadioButton("mp3", id="mp3_btn", value=True)
                    yield RadioButton("mp4", id="mp4_btn")
                
            #OutFolder
            yield FileSelect("./out/", "Select output Folder", [], id="out_sel")

            #Run
            with Horizontal(id="run"):
                yield Static("Run YT-DLP:", id="run_lbl")
                yield Button("Run", id="run_btn")

        yield Footer()


