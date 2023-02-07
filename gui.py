import tkinter as tk
from tkinter import ttk

import database


class RecordTable(ttk.Frame):
    def __init__(self, *args, theme, **kwargs):
        super(RecordTable, self).__init__(*args, **kwargs)
        self.theme = theme
        self.tree = ttk.Treeview(self, selectmode="browse")
        self.tree.pack(side="left", expand=True, fill="both")
        scroll_bar = ttk.Scrollbar(self, orient="vertical", command=self.tree.yview)

        scroll_bar.pack(side="right", fill="y")
        self.tree.configure(yscrollcommand=scroll_bar.set)
        self.refresh()

    def refresh(self):
        data = database.view_records(self.theme)
        sample: database.Record = data[0]

        # creating the headings and all that
        headings = tuple(sample.values.keys())
        self.tree["columns"] = ("date", *(str(i) for i in range(len(headings))))
        self.tree["show"] = "headings"
        self.tree.column("date", width=120, anchor="w")
        self.tree.heading("date", text="Date")

        for i, heading in enumerate(headings):
            self.tree.column(str(i), width=90, anchor="c")
            self.tree.heading(str(i), text=heading.capitalize())

        # writing the data
        for record in data:
            date = record.datetime.strftime("%d/%m/%Y %H:%M:%S")
            self.tree.insert("", "end", values=(date, *record.values.values()))


class Page(tk.Frame):
    def __init__(self, *args, theme: str, **kwargs):
        super(Page, self).__init__(*args, **kwargs)
        self.theme = theme
        self.record_table = RecordTable(theme=theme, master=self)
        self.setup_gui()

    def setup_gui(self):
        self.record_table.pack()

    def get_benchmarks(self):
        return database.view_benchmarks(self.theme)

    def get_records(self):
        return database.view_records(self.theme)


class App(tk.Frame):
    def __init__(self, master):
        super(App, self).__init__(master)
        self.note_book = ttk.Notebook(master=self.master)
        for theme in database.view_themes():
            page = Page(master=self.note_book, theme=theme)
            page.pack()
            self.note_book.add(page, text=theme)
        self.note_book.pack()


def main():
    root = tk.Tk()
    root.columnconfigure(0, weight=1)
    my_app = App(root)
    my_app.mainloop()


if __name__ == "__main__":
    main()
