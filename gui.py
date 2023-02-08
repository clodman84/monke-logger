import tkinter as tk
from tkinter import ttk

import database


class RecordEntry(tk.Frame):
    def __init__(self, *args, theme, **kwargs):
        super(RecordEntry, self).__init__(*args, **kwargs)
        self.theme = theme


class BenchmarkEntry(tk.Frame):
    def __init__(self, *args, theme, **kwargs):
        super(BenchmarkEntry, self).__init__(*args, **kwargs)
        self.theme = theme


class BenchmarkTable(tk.Frame):
    def __init__(self, *args, theme, **kwargs):
        super(BenchmarkTable, self).__init__(*args, **kwargs)
        self.theme = theme
        self.tree = ttk.Treeview(self)
        self.tree.pack(side="left", expand=True, fill="both")

        scroll_bar = ttk.Scrollbar(self, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scroll_bar.set)
        scroll_bar.pack(side="right", fill="y")

        self.refresh()

    def refresh(self):
        data: list[list[database.Benchmark]] = database.view_benchmarks(self.theme)
        if len(data) == 0:
            return

        self.tree["columns"] = ("date", "value")

        self.tree.column("date", width=120, anchor="w")
        self.tree.column("value", width=90, anchor="w")

        self.tree.heading("date", text="Date")
        self.tree.heading("value", text="Value")

        for activity in data:
            sample = activity[-1]
            average = sum(bench.value for bench in activity) / len(activity)
            # the values here can be something useful, like the average or the last time you did something
            root_node = self.tree.insert(
                "",
                text=sample.name,
                index="end",
                values=(
                    "Last: " + sample.datetime.strftime("%d/%m/%Y"),
                    f"Average: {average}",
                ),
            )
            for benchmark in activity:
                date = benchmark.datetime.strftime("%d/%m/%Y %H:%M:%S")
                self.tree.insert(
                    root_node,
                    "end",
                    text=benchmark.name,
                    values=(date, benchmark.value),
                )


class RecordTable(tk.Frame):
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
        if len(data) == 0:
            return
        sample: database.Record = data[0]

        # creating the headings and all that
        headings = tuple(sample.values.keys())
        self.tree["columns"] = ("date", *(str(i) for i in range(len(headings))))
        self.tree["show"] = "headings"
        self.tree.column("date", width=120, anchor="w")
        self.tree.heading("date", text="Date")

        # adding the headings for Record.values dictionary
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
        self.benchmark_table = BenchmarkTable(theme=theme, master=self)
        self.setup_gui()

    def setup_gui(self):
        self.record_table.grid(column=0, row=0)
        self.benchmark_table.grid(column=1, row=0)


class App(tk.Frame):
    def __init__(self, master):
        super(App, self).__init__(master)


def main():
    root = tk.Tk()
    note_book = ttk.Notebook(master=root)

    themes = database.view_themes()
    for theme in themes:
        page = Page(master=note_book, theme=theme)
        page.grid(column=0, row=0, sticky="ew")
        note_book.add(page, text=theme.capitalize())

    new_theme_frame = tk.Frame(note_book)
    label = tk.Label(new_theme_frame, text="Enter Theme: ")
    text_box = tk.Entry(new_theme_frame)
    text_box.grid(column=1, row=0)
    label.grid(column=0, row=0)

    # Create the application variable.
    contents = tk.StringVar()
    # Tell the entry widget to watch this variable.
    text_box["textvariable"] = contents

    def make_theme():
        requested_theme = contents.get()
        if requested_theme.lower() in themes:
            return
        # register the theme in the database
        database.create_theme(requested_theme)

        # add the theme to the list so that it can't be made again
        themes.append(requested_theme)

        # update the notebook with a page for the theme
        theme_page = Page(master=note_book, theme=requested_theme)
        note_book.insert(0, theme_page, text=requested_theme.capitalize())

    tk.Button(new_theme_frame, command=make_theme, text="Create").grid(column=3, row=0)
    note_book.add(new_theme_frame, text="+")

    note_book.grid(column=0, row=0, sticky="ew")
    root.resizable(False, False)
    root.mainloop()


if __name__ == "__main__":
    main()
