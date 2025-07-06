import logging
import sys
from pathlib import Path
from typing import Callable, List

try:
    import tkinter as tk  # Python 3.x
    import tkinter.scrolledtext as ScrolledText
    import tkinter.ttk as ttk
    from tkinter import filedialog
except ImportError:
    import Tkinter as tk # Python 2.x
    import ScrolledText
    # TODO python2

import mysql.connector

from fsklib.deueventcsv import DeuMeldeformularCsv
from fsklib.deuxlsxforms import ConvertedOutputType, DEUMeldeformularXLSX
from fsklib.fsm.result import extract
from fsklib.output import (EmptySegmentPdfOutput, OdfParticOutput,
                           ParticipantCsvOutput)
from fsklib.ppc import PdfParser, PdfParserFunctionDeu, PpcOdfUpdater
from fsklib.utils.logging_helper import get_logger


def root_dir() -> Path:
    if getattr(sys, 'frozen', False):
        return Path(sys.executable).parent
    return Path(__file__).resolve().parent.parent


def master_data_dir() -> Path:
    return root_dir() / "masterData"


def file_dialog(file_extensions: List[str], open_mode: str, function: Callable, initial_path: Path):
    # show the open file dialog
    initial_dir = initial_path.resolve()
    if not initial_dir.exists() or initial_dir.is_file():
        initial_dir = initial_dir.parent
    kwargs = {}
    if initial_dir.exists():
        kwargs["initialdir"] = initial_dir

    if open_mode == 'r':
        f = filedialog.askopenfilename(filetypes=file_extensions, **kwargs)
    elif open_mode == 'w':
        f = filedialog.asksaveasfilename(filetypes=file_extensions, **kwargs)
    elif open_mode == 'd':
        f = filedialog.askdirectory(**kwargs)
    function(f)


# Create global logger object and add a file handler
logger = get_logger(__name__, __file__)
logger.setLevel(logging.INFO)

file_handler = logging.FileHandler(filename=f'{logger.name}.log')
file_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
logger.addHandler(file_handler)


class TextHandler(logging.Handler):
    # This class allows you to log to a Tkinter Text or ScrolledText widget
    # Adapted from Moshe Kaplan: https://gist.github.com/moshekaplan/c425f861de7bbf28ef06

    def __init__(self, text):
        # run the regular Handler __init__
        logging.Handler.__init__(self)
        # Store a reference to the Text it will log to
        self.text = text

    def emit(self, record):
        msg = self.format(record)

        def append():
            self.text.insert(tk.END, msg + '\n')
            # Autoscroll to the bottom
            self.text.yview(tk.END)
        # This is necessary because we can't modify the Text from other threads
        self.text.after(0, append)


class XLSXConverterFrame(tk.Frame):
    # This class defines the graphical user interface

    def __init__(self, parent, *args, **kwargs):
        tk.Frame.__init__(self, parent, *args, **kwargs)
        self.input_xlsx_path = Path()
        self.build_gui()

    def open_xlsx(self, file_name):
        self.input.delete(0, tk.END)
        self.input_xlsx_path = Path(file_name)
        self.input.insert(0, self.input_xlsx_path)

    def file_dialog_set_text(self, file_extensions, file_type):
        file_dialog(file_extensions, file_type, self.open_xlsx, self.input_xlsx_path)

    def logic(self):
        if not self.input_xlsx_path:
            logger.error('Meldeformular-Datei auswählen!')
            return

        logger.info("Meldeformular einlesen")
        try:
            deu_xlsx = DEUMeldeformularXLSX(self.input_xlsx_path)
            deu_xlsx.convert()

            deu_event_info_csv = deu_xlsx.get_output_files(ConvertedOutputType.EVENT_INFO)[0]
            deu_persons_csv = deu_xlsx.get_output_files(ConvertedOutputType.EVENT_PERSONS)[0]
            deu_categories_csv = deu_xlsx.get_output_files(ConvertedOutputType.EVENT_CATERGORIES)[0]

            if not deu_event_info_csv or not deu_persons_csv or not deu_categories_csv:
                logger.error("Nicht alle notwendigen Informationen konnten aus dem Meldeformular gelesen werden.")
                return
        except:
            logger.exception("Das Meldeformular konnte nicht korrekt eingelesen werden.")
            return

        logger.info("Generiere ODF-Dateien...")

        output_path = self.input_xlsx_path.parent
        deu_csv = DeuMeldeformularCsv()
        deu_csv.convert(deu_persons_csv,
                        master_data_dir() / "csv" / "clubs-DEU.csv",
                        deu_categories_csv,
                        deu_event_info_csv,
                        [OdfParticOutput(output_path),
                         ParticipantCsvOutput(output_path / "csv" / "participants.csv"),
                         EmptySegmentPdfOutput(output_path / "website", master_data_dir() / "FSM" / "website" / "empty.pdf")]
                       )

        logger.info("Fertig!")
        logger.info("Generierte Dateien befinden sich hier: %s" % str(self.input_xlsx_path.parent))

    def convert_callback(self):
        self.logic()

    def build_gui(self):
        # Build GUI
        self.pack(fill='both', expand=True, padx=10, pady=10)
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1)

        file_extensions = (
            ('Excel-Datei', '*.xlsx'),
            ('All files', '*.*')
        )

        self.input = tk.Entry(self)
        self.input.pack(expand=True)
        self.input.grid(column=0, row=0, sticky='nsew')
        self.input.insert(0, 'DEU Meldeformular (.xlsx)')
        self.open_xlsx(self.input.get())
        button = ttk.Button(self, text="Auswählen", command=lambda: self.file_dialog_set_text(file_extensions, "r"))
        button.grid(column=1, row=0, sticky='nsew', padx=10)

        button_convert = ttk.Button(self, text='Konvertieren', command=self.convert_callback)
        button_convert.grid(column=1, row=1, sticky='se', padx=10, pady=10)


class PPCConverterFrame(tk.Frame):
    def __init__(self, parent, *args, **kwargs):
        tk.Frame.__init__(self, parent, *args, **kwargs)
        self.parser = PdfParser(PdfParserFunctionDeu())
        self.build_gui()

    def set_ppc_dir(self, file_name):
        self.input_ppc_dir.delete(0, tk.END)
        self.input_ppc_dir.insert(0, file_name)

    def set_odf_path(self, file_name):
        self.input_odf_path.delete(0, tk.END)
        self.input_odf_path.insert(0, file_name)

    def logic(self):
        ppc_dir = Path(self.input_ppc_dir.get())
        if not ppc_dir.is_dir():
            logger.error("Unable to find PPC files. '%s' is not a directory.", str(ppc_dir))
            return

        odf_path = Path(self.input_odf_path.get())
        if not odf_path.is_file():
            logger.error("Unable to open DT_PARTIC xml file. '%s' is not a file.", str(odf_path))
            return

        try:
            ppcs = self.parser.ppcs_parse_dir(ppc_dir)
            with PpcOdfUpdater(odf_path) as updater:
                updater.update(ppcs)
        except:
            logger.exception("Error in parsing PPC files or updating ODF file.")

    def build_gui(self):
        self.pack(fill='both', expand=True, padx=10, pady=10)
        self.grid_columnconfigure(0, weight=1)

        row_index = 0

        # PPC directory selection
        label_ppc_dir = tk.Label(self, text="PPC-Verzeichnis")
        label_ppc_dir.grid(column=0, row=row_index, sticky='nw', padx=10)

        self.ppc_dir = tk.StringVar(self, "")
        self.input_ppc_dir = tk.Entry(self, textvariable=self.ppc_dir)
        self.input_ppc_dir.grid(column=1, row=row_index, sticky='nsew', padx=10)

        self.button_choose_ppc_dir = ttk.Button(self, text="Auswählen", command=lambda: file_dialog([], "d", self.set_ppc_dir, Path(self.input_ppc_dir.get())))
        self.button_choose_ppc_dir.grid(column=2, row=row_index, sticky='nsew', padx=10)

        row_index += 1

        # ODF file selection
        label_odf_file = tk.Label(self, text="DT_PARTIC XML-Datei")
        label_odf_file.grid(column=0, row=row_index, sticky='nw', padx=10)

        self.input_odf_path = tk.Entry(self)
        self.input_odf_path.grid(column=1, row=row_index, sticky='nsew', padx=10)

        self.button_choose_odf_file = ttk.Button(self, text="Auswählen", command=lambda: file_dialog([('XML-Datei', '*.xml'), ('All files', '*.*')], "r", self.set_odf_path, Path(self.input_odf_path.get())))
        self.button_choose_odf_file.grid(column=2, row=row_index, sticky='nsew', padx=10)

        row_index += 1

        # Convert button
        button_convert = ttk.Button(self, text='Konvertieren', command=self.logic)
        button_convert.grid(column=2, row=row_index, sticky='se', padx=10, pady=10)

        self.grid_rowconfigure(row_index, weight=1)


class ResultExtractorFrame(tk.Frame):
    # This class defines the graphical user interface

    def __init__(self, parent, *args, **kwargs):
        tk.Frame.__init__(self, parent, *args, **kwargs)
        self.input_xlsx_path = Path()
        self.build_gui()

    def open_xlsx(self, file_name):
        self.input_output_file.delete(0, tk.END)
        self.input_output_file.insert(0, file_name)

    def logic(self):
        try:
            con = self.get_database_connection()
            con.cursor().execute(f"USE `{self.drop_db_selection.get()}`")
            extract(con, self.input_output_file.get(), self.drop_comp_selection.get())
        except:
            logger.exception("Verbindung zur Datenbank kann nicht hergestellt werden. Bitte überprüfen Sie alle Einstellungen.")
            return
        logger.info(f"Ergebnisse nach {Path(self.input_output_file.get()).resolve()} extrahiert!")

    def extract_callback(self):
        self.open_xlsx(self.input_output_file.get())
        self.logic()

    def get_database_connection(self):
        return mysql.connector.connect(user=self.input_user.get(), password=self.input_pw.get(), host=self.input_host.get(), port=int(self.input_port.get()))

    def read_database_names(self) -> list:
        try:
            con = self.get_database_connection()
        except:
            return []

        if con:
            cursor = con.cursor()
            cursor.execute("SHOW DATABASES")
            database_names = [i[0] for i in cursor.fetchall()]
            return database_names
        else:
            return []

    def read_competition_names(self) -> list:
        db_name = self.drop_db_selection.get()
        if not db_name:
            return []

        try:
            con = self.get_database_connection()
            con.cursor().execute(f"USE `{db_name}`")
        except:
            return []

        if con:
            cursor = con.cursor()
            try:
                cursor.execute("SELECT ShortName FROM competition")
                competition_names = [i[0] for i in cursor.fetchall()]
            except:
                return []
            return competition_names
        else:
            return []

    def update_database_names(self):
        l = self.read_database_names()
        if len(l):
            self.drop_db.set_menu(l[0], *l)
        else:
            self.drop_db.set_menu('', *[''])
            self.drop_db_selection.set('')

    def update_competition_names(self, *args):
        l = self.read_competition_names()
        if len(l):
            self.drop_comp.set_menu(l[0], *l)
        else:
            self.drop_comp.set_menu('', *[''])
            self.drop_comp_selection.set('')

    def add_row_to_layout(self, row_index, label, input_default, button=None, **argv):
        label_variable = tk.Label(self, text=label)
        label_variable.grid(column=0, row=row_index, sticky='nw', padx=10)

        input_variable = tk.Entry(self, text=tk.StringVar(self, input_default), **argv)
        input_variable.grid(column=1, row=row_index, sticky='nsew', padx=10)
        if button:
            button.grid(column=2, row=row_index, sticky='nsew', padx=10)

        return input_variable

    def build_gui(self):
        # Build GUI
        self.pack(fill='both', expand=True, padx=10, pady=10)
        self.grid_columnconfigure(0, weight=1)

        row_index = 0
        file_extensions = (
            ('Excel-Datei', '*.xlsx'),
            ('All files', '*.*')
        )

        # restrict port entry to only except integers
        def validate_integer(value: str):
            if value.isdigit():
                return True
            elif value == "":
                return True
            else:
                return False

        validation_cmd = (self.master.master.register(validate_integer), '%P')

        button = ttk.Button(self, text="Auswählen", command=lambda: file_dialog(file_extensions, "w", self.open_xlsx, Path(self.input_output_file.get())))
        self.input_output_file = self.add_row_to_layout(row_index, "Ausgabe-Datei", "Ergebnis.xlsx", button=button)
        self.open_xlsx(self.input_output_file.get())

        row_index += 1  # next row in layout
        self.input_user = self.add_row_to_layout(row_index, "Datenbank-Nutzer", "sa")

        row_index += 1  # next row in layout
        self.input_pw = self.add_row_to_layout(row_index, "Datenbank-Passwort", "fsmanager")

        row_index += 1  # next row in layout
        self.input_host = self.add_row_to_layout(row_index, "Datenbank-Adresse", "127.0.0.1")

        row_index += 1  # next row in layout
        self.input_port = self.add_row_to_layout(row_index, "Datenbank-Port", "3306", validate='key', validatecommand=validation_cmd)

        row_index += 1  # next row in layout
        self.label_database = tk.Label(self, text="Datenbank-Name")
        self.label_database.grid(column=0, row=row_index, sticky="nw", padx=10)

        # Create Dropdown menu for database names
        self.drop_db_selection = tk.StringVar()
        self.drop_db = ttk.OptionMenu(self, self.drop_db_selection, default=None, *[])
        self.update_database_names()
        self.drop_db.grid(column=1, row=row_index, sticky='nw', padx=10)
        self.drop_db_selection.trace_add("write", self.update_competition_names)

        button_update_database_names = ttk.Button(self, text="Aktualisieren", command=lambda: self.update_database_names())
        button_update_database_names.grid(column=2, row=row_index, sticky='nw', padx=10)

        row_index += 1  # next row in layout
        self.label_database = tk.Label(self, text="Competition-Code")
        self.label_database.grid(column=0, row=row_index, sticky="nw", padx=10)

        # Create Dropdown menu for competition names
        self.drop_comp_selection = tk.StringVar()
        self.drop_comp = ttk.OptionMenu(self, self.drop_comp_selection, default=None, *[])
        self.update_competition_names()
        self.drop_comp.grid(column=1, row=row_index, sticky='nw', padx=10)

        row_index += 1  # next row in layout
        button_extract = ttk.Button(self, text='Extrahieren', command=self.extract_callback)
        button_extract.grid(column=2, row=row_index, sticky='se', padx=10, pady=10)

        self.grid_rowconfigure(row_index, weight=1)


# ensure that text is not editable, but copyable
def ctrlEvent(event, root):
    if event.state == 4:
        if event.keysym == 'c':
            content = event.widget.selection_get()
            root.clipboard_clear()
            root.clipboard_append(content)
            return
    return "break"


class LogFrame(tk.Frame):
    def __init__(self, parent, *args, **kwargs):
        tk.Frame.__init__(self, parent, *args, padx=10, pady=10, **kwargs)
        self.build_gui()

    def update_log_levels(self, *args):
        is_debug = bool(self.do_debug.get())
        level = logging.DEBUG if is_debug else logging.INFO
        for name in logging.root.manager.loggerDict:
            log = logging.getLogger(name)
            if log.name.startswith(logger.name):
                log.setLevel(level)

    def build_gui(self):
        # self.pack(fill='both', expand=True, padx=10, pady=10)

        self.label = tk.Label(self, text="Log-Ausgabe")
        self.label.pack(side="top")

        # Add text widget to display logging info
        self.text_box = ScrolledText.ScrolledText(self, state='normal')
        self.text_box.pack(fill="both", expand=True)

        # make text copyable
        self.text_box.bind("<Key>", lambda e: ctrlEvent(e, self.master))

        self.text_box.configure(font='TkFixedFont')

        self.do_debug = tk.IntVar()
        self.check_debug = tk.Checkbutton(self, text="debug", variable=self.do_debug)
        self.check_debug.pack(side="right", padx=10)
        self.do_debug.trace_add("write", self.update_log_levels)

        # Create ui text widget Logger
        text_handler = TextHandler(self.text_box)
        text_handler.setFormatter(logging.Formatter('%(levelname)s: %(message)s'))
        logger.addHandler(text_handler)

        self.update_log_levels()


def main():
    # root
    root = tk.Tk()
    ui_name = Path(__file__).stem
    root.title(ui_name)
    root.option_add('*tearOff', 'FALSE')

    # tab control
    tab_control = ttk.Notebook(root)
    tab1 = XLSXConverterFrame(tab_control)
    tab2 = PPCConverterFrame(tab_control)
    tab3 = ResultExtractorFrame(tab_control)
    tab_control.add(tab1, text="Meldelisten-Konverter")
    tab_control.add(tab2, text="PPC-Konverter")
    tab_control.add(tab3, text="Ergebnisse auslesen")

    log_frame = LogFrame(root)
    tab_control.pack(side="top", fill="both", expand=True)
    log_frame.pack(side="top", fill="both", expand=True)

    root.mainloop()


if __name__ == "__main__":
    main()
