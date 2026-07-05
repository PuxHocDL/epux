from __future__ import annotations

from textual import on
from textual.app import App, ComposeResult
from textual.containers import Horizontal, Vertical
from textual.widgets import Button, DataTable, Footer, Header, Input, Label, Static, TabPane, TabbedContent, TextArea

from .config import AppConfig, default_config_path, default_db_path
from .db import Database, VocabItem
from .notifications import send_review_reminder
from .sample_data import SAMPLE_WORDS


class EPuxApp(App[None]):
    CSS = """
    Screen {
        background: #121017;
        color: #f4ecd8;
    }

    Header, Footer {
        background: #19141f;
        color: #f1d08a;
        text-style: bold;
    }

    TabbedContent {
        background: #121017;
    }

    Tabs {
        background: #18131d;
        color: #91806b;
    }

    Tab {
        padding: 0 2;
        margin: 0 1 0 0;
    }

    Tab.-active {
        background: #2a1f14;
        color: #f6df9e;
        text-style: bold;
    }

    TabPane {
        padding: 1 1;
        height: 1fr;
    }

    .hero {
        border: round #d7b46a;
        background: #1a1520;
        color: #f4ecd8;
        padding: 1 2;
        margin: 0 0 1 0;
        min-height: 8;
    }

    .split_screen {
        height: 1fr;
    }

    .work_side {
        width: 1fr;
        height: 1fr;
        margin: 0 1 0 0;
    }

    .guide_side {
        width: 1fr;
        height: 1fr;
        border: round #4fb7ae;
        background: #121820;
        color: #f4ecd8;
        padding: 1 2;
        margin: 0;
    }

    .panel {
        border: round #9f8150;
        background: #17131b;
        color: #f4ecd8;
        padding: 1 1;
        margin: 0 0 1 0;
    }

    .game_card {
        border: tall #d7b46a;
        background: #16111b;
        color: #f4ecd8;
        padding: 2 4;
        margin: 0 0 1 0;
        height: 1fr;
        min-height: 24;
        content-align: center middle;
    }

    .game_toolbar {
        border: tall #6a5537;
        background: #17131b;
        padding: 0 1;
        margin: 0 0 1 0;
        min-height: 4;
    }

    .panel_alt {
        border: round #4fb7ae;
        background: #14171d;
    }

    .toolbar {
        border: round #6a5537;
        background: #17131b;
        padding: 0 1;
        margin: 0 0 1 0;
        min-height: 4;
    }

    .inline_actions {
        background: #17131b;
        margin: 0 0 1 0;
        min-height: 3;
    }

    .title {
        color: #f1d08a;
        text-style: bold;
        margin-bottom: 1;
    }

    .hint {
        color: #8ecfca;
    }

    .subtle {
        color: #a49889;
    }

    Button {
        margin-right: 1;
        min-width: 12;
        height: 3;
        content-align: center middle;
        border: round #7d6541;
        background: #241a13;
        color: #f4ecd8;
    }

    Button:hover {
        background: #322519;
        color: #ffe4a8;
    }

    Button.-primary {
        border: round #d7b46a;
        background: #3a2815;
        color: #ffeab7;
    }

    Button.-success {
        border: round #59b7a6;
        background: #18312d;
        color: #d7fff7;
    }

    Button.-warning {
        border: round #c58d6e;
        background: #352118;
        color: #ffe2d2;
    }

    Button.-error {
        border: round #cc7070;
        background: #371d22;
        color: #ffe1e1;
    }

    Input {
        border: round #6a5537;
        background: #151118;
        color: #f4ecd8;
        margin-bottom: 1;
        height: 3;
    }

    Input:focus {
        border: round #d7b46a;
        background: #19141d;
    }

    DataTable {
        height: 1fr;
        border: round #6a5537;
        background: #151118;
        color: #f4ecd8;
    }

    TextArea {
        height: 10;
        border: round #6a5537;
        background: #151118;
        color: #f4ecd8;
        margin-bottom: 1;
    }

    TextArea:focus {
        border: round #d7b46a;
    }

    #stats {
        min-height: 9;
    }

    #library_detail, #add_preview, #batch_status, #settings_text {
        min-height: 14;
    }

    #library_panel {
        height: 1fr;
    }

    #quiz_tab, #review_tab {
        height: 1fr;
    }

    #due_table {
        height: 1fr;
    }

    #suggestion_table {
        height: 10;
    }

    #library_table {
        height: 1fr;
    }

    .guide_toggle {
        min-width: 10;
    }
    """

    BINDINGS = [
        ("q", "quit", "Thoat"),
        ("r", "start_review", "On tap"),
        ("t", "start_quiz", "Kiem tra"),
        ("a", "focus_add_term", "Them the"),
        ("l", "open_library", "Kho tu"),
        ("ctrl+s", "save_context", "Luu theo o dang chon"),
        ("s", "save_settings", "Luu"),
        ("h", "toggle_guides", "Huong dan"),
        ("space", "game_primary", "Action"),
        ("1", "answer_quiz_1", "A/Again"),
        ("2", "answer_quiz_2", "B/Hard"),
        ("3", "answer_quiz_3", "C/Good"),
        ("4", "answer_quiz_4", "D/Easy"),
    ]

    def __init__(
        self,
        db: Database,
        config: AppConfig,
        *,
        launch_tab: str = "dashboard_tab",
        launch_review: bool = False,
        launch_quiz: bool = False,
    ) -> None:
        super().__init__()
        self.db = db
        self.config = config
        self.launch_tab = launch_tab
        self.launch_review = launch_review
        self.launch_quiz = launch_quiz
        self.guides_visible = True
        self.editing_word_id: int | None = None
        self.current_review_word: VocabItem | None = None
        self.review_show_answer = False
        self.selected_library_word: VocabItem | None = None
        self.quiz_word: VocabItem | None = None
        self.quiz_prompt = ""
        self.quiz_options: list[str] = []
        self.quiz_correct_answer = ""
        self.quiz_mode = "mixed"
        self.quiz_mode_used = "term_to_meaning"
        self.quiz_answered = False
        self.quiz_score = 0
        self.quiz_total = 0
        self.quiz_streak = 0
        self.quiz_feedback = ""

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        with TabbedContent(initial="dashboard_tab", id="main_tabs"):
            with TabPane("HOME", id="dashboard_tab"):
                with Horizontal(classes="split_screen"):
                    with Vertical(classes="work_side"):
                        yield Static("", id="stats", classes="hero")
                        with Horizontal(classes="toolbar"):
                            yield Button("REVIEW NOW", id="start_review", variant="primary")
                            yield Button("QUIZ NOW", id="start_quiz", variant="success")
                            yield Button("ADD CARD", id="go_add")
                            yield Button("SEED SAMPLE", id="seed_sample")
                            yield Button("GUIDE", classes="guide_toggle")
                        yield Label("DUE DECK", classes="title")
                        yield DataTable(id="due_table")
                    yield Static(
                        "[b #f6df9e]HOME GUIDE[/]\n\n"
                        "[#8ecfca]REVIEW NOW[/] opens the due queue as a game card.\n\n"
                        "[#8ecfca]QUIZ NOW[/] starts fast multiple-choice drills.\n\n"
                        "[#8ecfca]ADD CARD[/] is for one card or batch import.\n\n"
                        "[#a49889]Press h to hide/show this guide column.[/]",
                        classes="guide_side",
                    )

            with TabPane("ADD CARD", id="add_tab"):
                with Horizontal(classes="split_screen"):
                    with Vertical(classes="work_side"):
                        with Vertical(classes="panel"):
                            yield Label("CARD FORGE", classes="title")
                            yield Input(placeholder="English word / phrase", id="add_term")
                            yield DataTable(id="suggestion_table")
                            yield Input(placeholder="Vietnamese meaning", id="add_meaning")
                            yield Input(placeholder="Example sentence", id="add_example")
                            yield Input(placeholder="Notes / pattern / collocation", id="add_notes")
                            yield Input(placeholder="Tags: work, travel, B1", id="add_tags")
                            with Horizontal(classes="inline_actions"):
                                yield Button("SAVE CARD  Ctrl+S", id="add_save", variant="primary")
                                yield Button("CLEAR", id="add_clear")
                                yield Button("OPEN LIBRARY", id="go_library")
                                yield Button("GUIDE", classes="guide_toggle")
                        yield Static("", id="add_preview", classes="panel panel_alt")
                        with Vertical(classes="panel"):
                            yield Label("BATCH IMPORT", classes="title")
                            yield TextArea(id="batch_text")
                            with Horizontal(classes="inline_actions"):
                                yield Button("IMPORT BATCH  Ctrl+S", id="batch_import", variant="success")
                                yield Button("CLEAR BATCH", id="batch_clear")
                            yield Static(
                                "[#a49889]Paste one card per line, keep the | separators, then press Ctrl+S while the batch box is focused.[/]",
                                id="batch_status",
                                classes="panel_alt",
                            )
                    yield Static(
                        "[b #f6df9e]ADD GUIDE[/]\n\n"
                        "[#8ecfca]Single card[/]\n"
                        "Fill term, meaning, example, notes, tags, then press Ctrl+S or SAVE CARD.\n\n"
                        "[#8ecfca]Edit old card[/]\n"
                        "Go to LIBRARY, select a row, LOAD TO EDIT, then save.\n\n"
                        "[#8ecfca]Batch format[/]\n"
                        "term | meaning | example | notes | tags\n\n"
                        "[#8ecfca]Batch save[/]\n"
                        "Click inside the batch box, paste your lines, then press Ctrl+S to import.\n\n"
                        "[#a49889]Lines starting with # are ignored. Example and later fields may be empty.[/]\n\n"
                        "[#a49889]Press h to hide/show this guide column.[/]",
                        classes="guide_side",
                    )

            with TabPane("QUIZ", id="quiz_tab"):
                with Horizontal(classes="split_screen"):
                    with Vertical(classes="work_side"):
                        yield Static("", id="quiz_card", classes="game_card")
                        with Horizontal(classes="game_toolbar"):
                            yield Button("A", id="quiz_a", variant="primary")
                            yield Button("B", id="quiz_b", variant="primary")
                            yield Button("C", id="quiz_c", variant="primary")
                            yield Button("D", id="quiz_d", variant="primary")
                        with Horizontal(classes="game_toolbar"):
                            yield Button("NEXT", id="quiz_next", variant="success")
                            yield Button("REVEAL", id="quiz_reveal", variant="warning")
                            yield Button("MODE", id="quiz_mode")
                            yield Button("GUIDE", classes="guide_toggle")
                    yield Static(
                        "[b #f6df9e]QUIZ GUIDE[/]\n\n"
                        "[#8ecfca]Goal[/]\n"
                        "Pick the correct answer before revealing.\n\n"
                        "[#8ecfca]Keys[/]\n"
                        "1-4 = choose answer\n"
                        "SPACE = reveal or next card\n"
                        "MODE = Mixed / EN->VI / VI->EN\n\n"
                        "[#a49889]Hide this column with h when you want the quiz card to fill the arena.[/]",
                        classes="guide_side",
                    )

            with TabPane("REVIEW", id="review_tab"):
                with Horizontal(classes="split_screen"):
                    with Vertical(classes="work_side"):
                        yield Static("", id="review_card", classes="game_card")
                        with Horizontal(classes="game_toolbar"):
                            yield Button("SHOW", id="show_answer", variant="primary")
                            yield Button("NEXT DUE", id="review_next")
                            yield Button("GUIDE", classes="guide_toggle")
                        with Horizontal(classes="game_toolbar"):
                            yield Button("AGAIN", id="rate_again", variant="error")
                            yield Button("HARD", id="rate_hard", variant="warning")
                            yield Button("GOOD", id="rate_good", variant="success")
                            yield Button("EASY", id="rate_easy", variant="success")
                    yield Static(
                        "[b #f6df9e]REVIEW GUIDE[/]\n\n"
                        "[#8ecfca]Flow[/]\n"
                        "Look at the English card, recall meaning, then SHOW.\n\n"
                        "[#8ecfca]Rating keys[/]\n"
                        "1 Again = forgot\n"
                        "2 Hard = remembered slowly\n"
                        "3 Good = remembered\n"
                        "4 Easy = instant\n\n"
                        "[#a49889]Press h to hide this column and let the card take the full width.[/]",
                        classes="guide_side",
                    )

            with TabPane("LIBRARY", id="library_tab"):
                with Horizontal(classes="split_screen"):
                    with Vertical(classes="work_side"):
                        with Vertical(id="library_panel", classes="panel"):
                            yield Label("CARD LIBRARY", classes="title")
                            yield Input(placeholder="Search term / meaning / tag", id="library_query")
                            yield DataTable(id="library_table")
                        with Horizontal(classes="toolbar"):
                            yield Button("LOAD TO EDIT", id="library_edit", variant="primary")
                            yield Button("REVIEW THIS", id="library_review", variant="success")
                            yield Button("DELETE CARD", id="library_delete", variant="error")
                            yield Button("REFRESH", id="library_refresh")
                            yield Button("GUIDE", classes="guide_toggle")
                    yield Static("", id="library_detail", classes="guide_side")

            with TabPane("SETTINGS", id="settings_tab"):
                with Horizontal(classes="split_screen"):
                    with Vertical(classes="work_side"):
                        with Vertical(classes="panel"):
                            yield Label("LOCAL SETTINGS", classes="title")
                            yield Input(value=str(self.config.daily_new_words), placeholder="Daily new cards", id="setting_daily_new_words")
                            yield Input(value=str(self.config.reminder_minutes), placeholder="Reminder minutes", id="setting_reminder_minutes")
                            with Horizontal(classes="inline_actions"):
                                yield Button("SAVE SETTINGS", id="settings_save", variant="primary")
                                yield Button("TEST REMINDER", id="test_reminder", variant="success")
                                yield Button("GUIDE", classes="guide_toggle")
                        yield Static("", id="settings_text", classes="panel panel_alt")
                    yield Static(
                        "[b #f6df9e]SETTINGS GUIDE[/]\n\n"
                        "[#8ecfca]Daily new cards[/]\n"
                        "A target number for how many new words you want to add per day.\n\n"
                        "[#8ecfca]Reminder minutes[/]\n"
                        "How often the background reminder checks due cards.\n\n"
                        "[#a49889]Press h to hide/show this guide column.[/]",
                        classes="guide_side",
                    )
        yield Footer()

    def on_mount(self) -> None:
        self.title = "EPux - English Card Arena"
        self.sub_title = "Local vocabulary trainer"
        self._setup_tables()
        self._set_border_titles()
        self.refresh_all()
        self.apply_guide_visibility()
        self.open_tab(self.launch_tab)
        if self.launch_quiz:
            self.start_quiz()
        elif self.launch_review:
            self.start_next_review()

    def on_unmount(self) -> None:
        self.db.close()

    def action_start_review(self) -> None:
        self.open_tab("review_tab")
        self.start_next_review()

    def action_start_quiz(self) -> None:
        self.open_tab("quiz_tab")
        self.start_quiz()

    def action_focus_add_term(self) -> None:
        self.open_tab("add_tab")
        self.call_after_refresh(lambda: self.query_one("#add_term", Input).focus())

    def action_open_library(self) -> None:
        self.open_tab("library_tab")
        self.call_after_refresh(lambda: self.query_one("#library_query", Input).focus())

    def action_save_context(self) -> None:
        active = self.query_one("#main_tabs", TabbedContent).active
        if active == "add_tab":
            if self.query_one("#batch_text", TextArea).has_focus:
                self.import_batch_cards()
            else:
                self.save_add_card()
            return
        if active == "settings_tab":
            self.save_settings()
            return
        self.notify("Ctrl+S works in ADD CARD and SETTINGS.", severity="information")

    def action_save_settings(self) -> None:
        self.save_settings()

    def action_toggle_guides(self) -> None:
        self.guides_visible = not self.guides_visible
        self.apply_guide_visibility()
        state = "shown" if self.guides_visible else "hidden"
        self.notify(f"Guide column {state}.", severity="information")

    def action_game_primary(self) -> None:
        active = self.query_one("#main_tabs", TabbedContent).active
        if active == "review_tab":
            if self.current_review_word is None:
                self.start_next_review()
            else:
                self.review_show_answer = not self.review_show_answer
                self.render_review_card()
        elif active == "quiz_tab":
            if self.quiz_word is None or self.quiz_answered:
                self.start_quiz()
            else:
                self.quiz_reveal_pressed()

    def action_answer_quiz_1(self) -> None:
        self._handle_game_number(0)

    def action_answer_quiz_2(self) -> None:
        self._handle_game_number(1)

    def action_answer_quiz_3(self) -> None:
        self._handle_game_number(2)

    def action_answer_quiz_4(self) -> None:
        self._handle_game_number(3)

    def open_tab(self, tab_id: str) -> None:
        self.query_one("#main_tabs", TabbedContent).active = tab_id

    def apply_guide_visibility(self) -> None:
        for guide in self.query(".guide_side"):
            guide.display = self.guides_visible

    def _handle_game_number(self, index: int) -> None:
        active = self.query_one("#main_tabs", TabbedContent).active
        if active == "quiz_tab":
            self.answer_quiz(index)
        elif active == "review_tab":
            self.rate_current_word(index)

    @on(TabbedContent.TabActivated, "#main_tabs")
    def tab_activated(self, event: TabbedContent.TabActivated) -> None:
        active = event.tabbed_content.active
        if active == "quiz_tab" and self.quiz_word is None:
            self.start_quiz()
        elif active == "review_tab" and self.current_review_word is None:
            self.start_next_review()
        elif active == "library_tab":
            self.refresh_library_table(self.query_one("#library_query", Input).value)

    @on(Input.Changed)
    def handle_input_changed(self, event: Input.Changed) -> None:
        input_id = event.input.id or ""
        if input_id == "add_term":
            self.refresh_suggestion_table(event.value)
            self.render_add_preview()
        elif input_id in {"add_meaning", "add_example", "add_notes", "add_tags"}:
            self.render_add_preview()
        elif input_id == "library_query":
            self.refresh_library_table(event.value)

    @on(Button.Pressed, "#start_review")
    def start_review_pressed(self) -> None:
        self.action_start_review()

    @on(Button.Pressed, "#start_quiz")
    def start_quiz_pressed(self) -> None:
        self.action_start_quiz()

    @on(Button.Pressed, "#go_add")
    def go_add_pressed(self) -> None:
        self.action_focus_add_term()

    @on(Button.Pressed, "#go_library")
    def go_library_pressed(self) -> None:
        self.action_open_library()

    @on(Button.Pressed, ".guide_toggle")
    def guide_toggle_pressed(self) -> None:
        self.action_toggle_guides()

    @on(Button.Pressed, "#seed_sample")
    def seed_sample(self) -> None:
        count = self.db.add_words(SAMPLE_WORDS)
        self.notify(f"Loaded {count} sample cards.", severity="information")
        self.refresh_all()

    @on(Button.Pressed, "#add_save")
    def add_save_pressed(self) -> None:
        self.save_add_card()

    def save_add_card(self) -> None:
        term = self.query_one("#add_term", Input).value.strip()
        if not term:
            self.notify("Enter a word or phrase first.", severity="warning")
            return

        meaning = self.query_one("#add_meaning", Input).value
        example = self.query_one("#add_example", Input).value
        notes = self.query_one("#add_notes", Input).value
        tags = self.query_one("#add_tags", Input).value
        try:
            if self.editing_word_id is not None and self.db.get_word(self.editing_word_id) is not None:
                item = self.db.update_word(self.editing_word_id, term, meaning, example, notes, tags)
                action = "Updated"
            else:
                existing = self.db.get_word_by_term(term)
                item = self.db.add_word(term, meaning, example, notes, tags)
                action = "Updated" if existing else "Saved"
        except Exception as exc:
            self.notify(str(exc), severity="error")
            self.render_add_preview()
            return

        self.notify(f"{action} card #{item.id}: {item.term}", severity="information")
        self.clear_add_form()
        self.selected_library_word = item
        self.refresh_all()

    @on(Button.Pressed, "#add_clear")
    def add_clear_pressed(self) -> None:
        self.clear_add_form()

    @on(Button.Pressed, "#batch_import")
    def batch_import_pressed(self) -> None:
        self.import_batch_cards()

    def import_batch_cards(self) -> None:
        text = self.query_one("#batch_text", TextArea).text
        try:
            rows, warnings = _parse_batch_cards(text)
        except ValueError as exc:
            self.query_one("#batch_status", Static).update(f"[#cc7070]{exc}[/]")
            self.notify(str(exc), severity="error")
            return

        saved = 0
        for row in rows:
            self.db.add_word(*row)
            saved += 1

        warning_text = "\n".join(f"[#c58d6e]{warning}[/]" for warning in warnings[:6])
        suffix = f"\n{warning_text}" if warning_text else ""
        self.query_one("#batch_status", Static).update(f"[#59b7a6]Imported {saved} cards.[/]{suffix}")
        self.notify(f"Imported {saved} cards.", severity="information")
        self.query_one("#batch_text", TextArea).load_text("")
        self.refresh_all()

    @on(Button.Pressed, "#batch_clear")
    def batch_clear_pressed(self) -> None:
        self.query_one("#batch_text", TextArea).load_text("")
        self.query_one("#batch_status", Static).update("")

    @on(Button.Pressed, "#quiz_next")
    def quiz_next_pressed(self) -> None:
        self.start_quiz()

    @on(Button.Pressed, "#quiz_reveal")
    def quiz_reveal_pressed(self) -> None:
        if not self.quiz_word:
            self.start_quiz()
            return
        if not self.quiz_answered:
            self.quiz_answered = True
            self.quiz_feedback = f"Correct answer: {self.quiz_correct_answer}"
            self.quiz_streak = 0
            self.render_quiz_card()

    @on(Button.Pressed, "#quiz_mode")
    def quiz_mode_pressed(self) -> None:
        order = ["mixed", "term_to_meaning", "meaning_to_term"]
        self.quiz_mode = order[(order.index(self.quiz_mode) + 1) % len(order)]
        self.start_quiz()

    @on(Button.Pressed, "#quiz_a")
    def quiz_a_pressed(self) -> None:
        self.answer_quiz(0)

    @on(Button.Pressed, "#quiz_b")
    def quiz_b_pressed(self) -> None:
        self.answer_quiz(1)

    @on(Button.Pressed, "#quiz_c")
    def quiz_c_pressed(self) -> None:
        self.answer_quiz(2)

    @on(Button.Pressed, "#quiz_d")
    def quiz_d_pressed(self) -> None:
        self.answer_quiz(3)

    @on(Button.Pressed, "#show_answer")
    def show_answer_pressed(self) -> None:
        if not self.current_review_word:
            self.start_next_review()
            return
        self.review_show_answer = not self.review_show_answer
        self.render_review_card()

    @on(Button.Pressed, "#review_next")
    def review_next_pressed(self) -> None:
        self.start_next_review()

    @on(Button.Pressed, "#rate_again")
    def rate_again_pressed(self) -> None:
        self.rate_current_word(0)

    @on(Button.Pressed, "#rate_hard")
    def rate_hard_pressed(self) -> None:
        self.rate_current_word(1)

    @on(Button.Pressed, "#rate_good")
    def rate_good_pressed(self) -> None:
        self.rate_current_word(2)

    @on(Button.Pressed, "#rate_easy")
    def rate_easy_pressed(self) -> None:
        self.rate_current_word(3)

    @on(Button.Pressed, "#library_refresh")
    def library_refresh_pressed(self) -> None:
        self.refresh_library_table(self.query_one("#library_query", Input).value)

    @on(Button.Pressed, "#library_edit")
    def library_edit_pressed(self) -> None:
        if not self.selected_library_word:
            self.notify("Select a card in the library first.", severity="warning")
            return
        item = self.selected_library_word
        self.editing_word_id = item.id
        self.fill_add_form(item.term, item.meaning, item.example, item.notes, item.tags)
        self.open_tab("add_tab")
        self.call_after_refresh(lambda: self.query_one("#add_meaning", Input).focus())

    @on(Button.Pressed, "#library_review")
    def library_review_pressed(self) -> None:
        if not self.selected_library_word:
            self.notify("Select a card in the library first.", severity="warning")
            return
        self.current_review_word = self.selected_library_word
        self.review_show_answer = False
        self.open_tab("review_tab")
        self.render_review_card()

    @on(Button.Pressed, "#library_delete")
    def library_delete_pressed(self) -> None:
        if not self.selected_library_word:
            self.notify("Select a card in the library first.", severity="warning")
            return
        item = self.selected_library_word
        deleted = self.db.delete_word(item.id)
        if deleted:
            if self.current_review_word and self.current_review_word.id == item.id:
                self.current_review_word = None
                self.review_show_answer = False
            if self.quiz_word and self.quiz_word.id == item.id:
                self.quiz_word = None
            if self.editing_word_id == item.id:
                self.clear_add_form()
            self.selected_library_word = None
            self.notify(f"Deleted card #{item.id}: {item.term}", severity="information")
        else:
            self.notify("That card was already gone.", severity="warning")
        self.refresh_all()

    @on(Button.Pressed, "#settings_save")
    def settings_save_pressed(self) -> None:
        self.save_settings()

    @on(Button.Pressed, "#test_reminder")
    def test_reminder_pressed(self) -> None:
        due = max(1, self.db.stats()["due"])
        sent = send_review_reminder(due, mode="window")
        if sent:
            self.notify("Reminder window sent.", severity="information")
        else:
            self.notify("Could not open reminder window on this machine.", severity="warning")

    @on(DataTable.RowSelected, "#due_table")
    def due_row_selected(self, event: DataTable.RowSelected) -> None:
        item = self._word_from_row_key(event.row_key.value)
        if item is None:
            return
        self.current_review_word = item
        self.review_show_answer = False
        self.open_tab("review_tab")
        self.render_review_card()

    @on(DataTable.RowSelected, "#suggestion_table")
    def suggestion_row_selected(self, event: DataTable.RowSelected) -> None:
        item = self._word_from_row_key(event.row_key.value)
        if item is None:
            return
        self.editing_word_id = item.id
        self.fill_add_form(item.term, item.meaning, item.example, item.notes, item.tags)

    @on(DataTable.RowSelected, "#library_table")
    def library_row_selected(self, event: DataTable.RowSelected) -> None:
        item = self._word_from_row_key(event.row_key.value)
        if item is None:
            return
        self.selected_library_word = item
        self.render_library_detail()

    def _setup_tables(self) -> None:
        due_table = self.query_one("#due_table", DataTable)
        due_table.cursor_type = "row"
        due_table.add_columns("Term", "Meaning", "Reps", "Due")

        suggestion_table = self.query_one("#suggestion_table", DataTable)
        suggestion_table.cursor_type = "row"
        suggestion_table.add_columns("Card", "Meaning", "Due")

        library_table = self.query_one("#library_table", DataTable)
        library_table.cursor_type = "row"
        library_table.add_columns("Term", "Meaning", "Tags", "Due")

    def _set_border_titles(self) -> None:
        titles = {
            "#stats": "[ CARD BANNER ]",
            "#due_table": "[ DUE NOW ]",
            "#suggestion_table": "[ MATCHING CARDS ]",
            "#add_preview": "[ CARD PREVIEW ]",
            "#batch_status": "[ IMPORT RESULT ]",
            "#quiz_card": "[ QUIZ BOARD ]",
            "#review_card": "[ REVIEW CARD ]",
            "#library_table": "[ FULL LIBRARY ]",
            "#library_detail": "[ SELECTED CARD ]",
            "#settings_text": "[ LOCAL ROUTES ]",
        }
        for selector, title in titles.items():
            try:
                self.query_one(selector).border_title = title
            except Exception:
                continue

    def refresh_all(self) -> None:
        library_query = self.query_one("#library_query", Input).value
        self.refresh_stats()
        self.refresh_due_table()
        self.refresh_library_table(library_query)
        self.render_add_preview()
        self.render_review_card()
        self.render_quiz_card()
        self.render_library_detail()
        self.render_settings()

    def refresh_stats(self) -> None:
        stats = self.db.stats()
        due_rows = self.db.due_words(3)
        next_due = "No cards are due right now."
        if due_rows:
            preview = ", ".join(item.term for item in due_rows[:3])
            next_due = f"Next up: {preview}"
        text = (
            "[b #f6df9e]EPux[/] [#8ecfca]Local English Card Arena[/]\n"
            f"[#d7b46a]Cards[/] [b]{stats['total']}[/]    "
            f"[#59b7a6]Due[/] [b]{stats['due']}[/]    "
            f"[#c58d6e]Reviews[/] [b]{stats['reviews']}[/]    "
            f"[#b58df2]Quiz[/] [b]{stats['quiz']}[/]\n"
            f"[#a49889]{next_due}[/]\n"
            "[#8ecfca]Hotkeys:[/] r review   t quiz   a add   l library   Ctrl+S save/import   s settings   q quit"
        )
        self.query_one("#stats", Static).update(text)

    def refresh_due_table(self) -> None:
        table = self.query_one("#due_table", DataTable)
        table.clear(columns=False)
        for item in self.db.due_words(100):
            table.add_row(
                item.term,
                _short(item.meaning, 42),
                str(item.repetitions),
                _short(item.due_at.replace("T", " "), 19),
                key=str(item.id),
            )

    def refresh_suggestion_table(self, prefix: str) -> None:
        table = self.query_one("#suggestion_table", DataTable)
        table.clear(columns=False)
        prefix = prefix.strip()
        if not prefix:
            return
        for item in self.db.suggest_words_by_prefix(prefix, 8):
            table.add_row(
                item.term,
                _short(item.meaning, 40),
                _short(item.due_at.replace("T", " "), 16),
                key=str(item.id),
            )

    def refresh_library_table(self, query: str) -> None:
        table = self.query_one("#library_table", DataTable)
        table.clear(columns=False)
        for item in self.db.list_words(limit=200, query=query.strip()):
            table.add_row(
                item.term,
                _short(item.meaning, 38),
                _short(item.tags, 20),
                _short(item.due_at.replace("T", " "), 16),
                key=str(item.id),
            )
        if self.selected_library_word:
            fresh = self.db.get_word(self.selected_library_word.id)
            self.selected_library_word = fresh

    def start_next_review(self) -> None:
        due = self.db.due_words(1)
        if not due:
            self.current_review_word = None
            self.review_show_answer = False
            self.render_review_card()
            self.notify("No due cards right now. Add a few more or jump into quiz mode.", severity="information")
            return
        self.current_review_word = due[0]
        self.review_show_answer = False
        self.render_review_card()

    def render_review_card(self) -> None:
        card = self.query_one("#review_card", Static)
        item = self.current_review_word
        if not item:
            card.update(
                "[b #f6df9e]REVIEW ARENA[/]\n\n"
                "[#a49889]No card is on the board yet.[/]\n\n"
                "[#8ecfca]Press SPACE or NEXT DUE to draw the next due card.[/]"
            )
            return

        answer_block = (
            f"\n[#59b7a6]MEANING[/]\n[b]{item.meaning or '(empty)'}[/]\n\n"
            f"[#d7b46a]EXAMPLE[/]\n{item.example or '(empty)'}\n\n"
            f"[#c58d6e]NOTES[/]\n{item.notes or '(empty)'}\n\n"
            f"[#b58df2]TAGS[/] {item.tags or '(none)'}"
            if self.review_show_answer
            else "\n[#a49889]Recall the meaning first. Press SPACE or SHOW to reveal.[/]"
        )
        card.update(
            f"[#a49889]REVIEW CARD #{item.id}     REP {item.repetitions}     EASE {item.ease:.2f}     MISS {item.lapses}[/]\n\n"
            f"[b #f6df9e]{_banner(item.term)}[/]\n"
            f"{answer_block}"
            "\n\n[#8ecfca]1 Again    2 Hard    3 Good    4 Easy[/]"
        )

    def rate_current_word(self, rating: int) -> None:
        if not self.current_review_word:
            self.start_next_review()
            return
        self.db.review_word(self.current_review_word.id, rating)
        self.refresh_stats()
        self.refresh_due_table()
        self.refresh_library_table(self.query_one("#library_query", Input).value)
        self.start_next_review()

    def start_quiz(self) -> None:
        try:
            (
                self.quiz_word,
                self.quiz_prompt,
                self.quiz_options,
                self.quiz_correct_answer,
                self.quiz_mode_used,
            ) = self.db.build_quiz_question(self.quiz_mode)
        except Exception as exc:
            self.quiz_word = None
            self.quiz_prompt = ""
            self.quiz_options = []
            self.quiz_correct_answer = ""
            self.quiz_feedback = str(exc)
            self.render_quiz_card()
            return
        self.quiz_answered = False
        self.quiz_feedback = ""
        self.render_quiz_card()

    def answer_quiz(self, option_index: int) -> None:
        if not self.quiz_word or not self.quiz_options:
            self.start_quiz()
            return
        if self.quiz_answered or option_index >= len(self.quiz_options):
            return
        selected = self.quiz_options[option_index]
        correct = selected == self.quiz_correct_answer
        self.quiz_answered = True
        self.quiz_total += 1
        if correct:
            self.quiz_score += 1
            self.quiz_streak += 1
            self.db.review_word(self.quiz_word.id, 2)
            self.quiz_feedback = "Nice. This card moves forward in the schedule."
        else:
            self.quiz_streak = 0
            self.db.review_word(self.quiz_word.id, 0)
            self.quiz_feedback = f"Not quite. Correct answer: {self.quiz_correct_answer}"

        self.db.log_quiz_answer(
            word_id=self.quiz_word.id,
            prompt=self.quiz_prompt,
            selected_answer=selected,
            correct_answer=self.quiz_correct_answer,
            is_correct=correct,
        )
        self.refresh_stats()
        self.refresh_due_table()
        self.refresh_library_table(self.query_one("#library_query", Input).value)
        self.render_quiz_card()

    def render_quiz_card(self) -> None:
        card = self.query_one("#quiz_card", Static)
        mode_label = {
            "mixed": "Mixed",
            "term_to_meaning": "EN -> VI",
            "meaning_to_term": "VI -> EN",
        }[self.quiz_mode]
        self.query_one("#quiz_mode", Button).label = f"MODE: {mode_label}"
        if not self.quiz_word:
            suffix = f"\n[#c58d6e]{self.quiz_feedback}[/]" if self.quiz_feedback else ""
            card.update(
                "[b #f6df9e]QUIZ ARENA[/]\n\n"
                f"[#a49889]Current mode: {mode_label}[/]\n\n"
                "[#8ecfca]Press SPACE or NEXT to draw a question.[/]"
                f"{suffix}"
            )
            return

        prompt_label = "Pick the meaning" if self.quiz_mode_used == "term_to_meaning" else "Pick the English term"
        lines = [
            f"[#a49889]QUIZ CARD #{self.quiz_word.id}     MODE {mode_label}     SCORE {self.quiz_score}/{self.quiz_total}     STREAK {self.quiz_streak}[/]",
            "",
            f"[b #f6df9e]{_banner(self.quiz_prompt)}[/]",
            "",
            f"[#8ecfca]{prompt_label}[/]",
            "",
        ]
        labels = ["A", "B", "C", "D"]
        for index, option in enumerate(self.quiz_options):
            lines.append(f"[b #d7b46a]{index + 1}. {labels[index]}[/]  {option}")
        lines.append("")
        lines.append("[#8ecfca]Press 1-4 to lock answer. SPACE reveals / deals next.[/]")
        if self.quiz_answered:
            lines.append("")
            lines.append(f"[#c58d6e]{self.quiz_feedback}[/]")
            if self.quiz_word.example:
                lines.append(f"[#d7b46a]Example[/] {self.quiz_word.example}")
            if self.quiz_word.notes:
                lines.append(f"[#8ecfca]Notes[/] {self.quiz_word.notes}")
        card.update("\n".join(lines))

    def clear_add_form(self) -> None:
        self.editing_word_id = None
        for selector in ("#add_term", "#add_meaning", "#add_example", "#add_notes", "#add_tags"):
            self.query_one(selector, Input).value = ""
        self.refresh_suggestion_table("")
        self.render_add_preview()

    def fill_add_form(self, term: str, meaning: str, example: str, notes: str, tags: str) -> None:
        self.query_one("#add_term", Input).value = term
        self.query_one("#add_meaning", Input).value = meaning
        self.query_one("#add_example", Input).value = example
        self.query_one("#add_notes", Input).value = notes
        self.query_one("#add_tags", Input).value = tags
        self.refresh_suggestion_table(term)
        self.render_add_preview()

    def render_add_preview(self) -> None:
        term = self.query_one("#add_term", Input).value.strip()
        meaning = self.query_one("#add_meaning", Input).value.strip()
        example = self.query_one("#add_example", Input).value.strip()
        notes = self.query_one("#add_notes", Input).value.strip()
        tags = self.query_one("#add_tags", Input).value.strip()
        editing_item = self.db.get_word(self.editing_word_id) if self.editing_word_id is not None else None
        existing = self.db.get_word_by_term(term) if term else None

        status = "[#8ecfca]Forge mode[/] Fill the fields and save a clean study card."
        if editing_item:
            status = (
                f"[#d7b46a]Editing card[/] #{editing_item.id}  "
                f"[#a49889]Original: {editing_item.term}  Reps {editing_item.repetitions}[/]"
            )
        elif existing:
            status = (
                f"[#d7b46a]Existing card[/] #{existing.id}  "
                f"[#a49889]Reps {existing.repetitions}  Due {existing.due_at.replace('T', ' ')}[/]"
            )
        elif term:
            status = "[#59b7a6]New card[/] This will be added to your library and due queue."

        preview = (
            f"{status}\n\n"
            f"[b #f6df9e]{term or 'Your word will appear here'}[/]\n"
            f"[#59b7a6]Meaning[/]  {meaning or '(add a meaning)'}\n"
            f"[#d7b46a]Example[/]  {example or '(add an example)'}\n"
            f"[#c58d6e]Notes[/]    {notes or '(add a note or pattern)'}\n"
            f"[#b58df2]Tags[/]     {tags or '(optional)'}"
        )
        self.query_one("#add_preview", Static).update(preview)

    def render_library_detail(self) -> None:
        card = self.query_one("#library_detail", Static)
        item = self.selected_library_word
        if not item:
            card.update(
                "[b #f6df9e]LIBRARY[/]\n\n"
                "[#8ecfca]Search[/]\n"
                "Type part of a term, meaning, or tag.\n\n"
                "[#8ecfca]Select a row[/]\n"
                "The card detail will appear here.\n\n"
                "[#8ecfca]Actions[/]\n"
                "LOAD TO EDIT sends it to the editor.\n"
                "REVIEW THIS opens it in review mode.\n"
                "DELETE CARD removes it.\n\n"
                "[#a49889]Press h to hide this side and make the table wider.[/]"
            )
            return
        card.update(
            f"[b #f6df9e]{item.term}[/]\n\n"
            f"[#59b7a6]Meaning[/]\n{item.meaning or '(empty)'}\n\n"
            f"[#d7b46a]Example[/]\n{item.example or '(empty)'}\n\n"
            f"[#c58d6e]Notes[/]\n{item.notes or '(empty)'}\n\n"
            f"[#b58df2]Tags[/] {item.tags or '(none)'}\n\n"
            f"[#a49889]ID {item.id}   Reps {item.repetitions}   Ease {item.ease:.2f}   Lapses {item.lapses}\n"
            f"Due {item.due_at.replace('T', ' ')}[/]\n\n"
            "[#8ecfca]LOAD TO EDIT[/] updates this exact card, even if you rename the term."
        )

    def save_settings(self) -> None:
        try:
            self.config.daily_new_words = max(1, int(self.query_one("#setting_daily_new_words", Input).value.strip()))
        except ValueError:
            pass
        try:
            self.config.reminder_minutes = max(5, int(self.query_one("#setting_reminder_minutes", Input).value.strip()))
        except ValueError:
            pass
        self.config.save()
        self.render_settings()
        self.notify("Settings saved.", severity="information")

    def render_settings(self) -> None:
        text = (
            f"[#f6df9e]Config[/]      {default_config_path()}\n"
            f"[#59b7a6]Database[/]    {default_db_path()}\n"
            f"[#d7b46a]New cards[/]   {self.config.daily_new_words} / day\n"
            f"[#c58d6e]Reminder[/]    every {self.config.reminder_minutes} minutes\n\n"
            "[#a49889]This TUI now focuses on the core loop: add cards, review due cards, quiz fast, manage library.[/]\n"
            "[#8ecfca]Reminder popup buttons now jump straight into REVIEW or QUIZ in a fresh console window.[/]"
        )
        self.query_one("#settings_text", Static).update(text)

    def _word_from_row_key(self, value: object) -> VocabItem | None:
        try:
            return self.db.get_word(int(str(value)))
        except Exception:
            return None


def _short(value: str, limit: int) -> str:
    value = value.replace("\n", " ").strip()
    if len(value) <= limit:
        return value
    return value[: max(0, limit - 3)] + "..."


def _banner(value: str) -> str:
    value = value.strip()
    if len(value) <= 44:
        return f"= {value} ="
    return value


def _parse_batch_cards(text: str) -> tuple[list[tuple[str, str, str, str, str]], list[str]]:
    rows: list[tuple[str, str, str, str, str]] = []
    warnings: list[str] = []
    for line_number, raw_line in enumerate(text.splitlines(), start=1):
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        parts = [part.strip() for part in line.split("|")]
        if len(parts) < 2:
            warnings.append(f"Line {line_number} skipped: expected term | meaning | example | notes | tags.")
            continue
        parts = (parts + ["", "", "", ""])[:5]
        term, meaning, example, notes, tags = parts
        if not term:
            warnings.append(f"Line {line_number} skipped: term is empty.")
            continue
        rows.append((term, meaning, example, notes, tags))
    if not rows:
        raise ValueError("No valid batch cards found.")
    return rows, warnings
