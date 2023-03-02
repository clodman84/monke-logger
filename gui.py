import tkinter as tk
from datetime import datetime
from tkinter import ttk

import database


def delta(date: datetime) -> str:
    # 'x days ago'
    delta = abs(datetime.utcnow() - date)
    d = delta.days
    stringify = f"{int(d)} {'days' if d != 1 else 'day'} ago" if d > 0 else "Today"
    return stringify


class RecordEntry:
    def __init__(self, theme):
        self.root = tk.Toplevel()
        self.root.resizable(False, False)
        self.theme = theme
        self.entries: list[tk.Entry] = []
        self.int_validation = self.root.register(
            lambda x: x.replace(".", "", 1).isdigit() or x == ""
        )
        self.headings = database.view_record_types(self.theme)
        self.setup_gui()

    def setup_gui(self):
        for i, heading in enumerate(self.headings):
            tk.Label(self.root, text=heading).grid(column=0, row=i)
            entry = tk.Entry(
                self.root, validate="all", validatecommand=(self.int_validation, "%P")
            )
            entry.grid(column=1, row=i)
            self.entries.append(entry)
        tk.Button(self.root, text="Add Record", command=self.add_record).grid(
            row=len(self.headings), column=1, sticky="ew"
        )
        tk.Button(self.root, text="Cancel", command=lambda: self.root.destroy()).grid(
            row=len(self.headings), column=0
        )

    def add_record(self):
        user_entered_values = map(lambda x: x.get(), self.entries)
        none_for_empty_string = map(
            lambda x: None if x == "" else x, user_entered_values
        )
        values = {x: val for x, val in zip(self.headings, none_for_empty_string)}
        database.Record(self.theme, datetime.now(), values).write_record()
        self.root.destroy()

    def wait(self):
        self.root.grab_set()
        self.root.wait_window()


class BenchmarkTable(tk.Frame):
    def __init__(self, *args, theme, **kwargs):
        super(BenchmarkTable, self).__init__(*args, **kwargs)
        self.theme = theme
        self.tree = ttk.Treeview(self)
        self.tree.pack(side="left", expand=True, fill="both")
        self.scroll_bar = ttk.Scrollbar(
            self, orient="vertical", command=self.tree.yview
        )
        self.scroll_bar.pack(side="right", fill="y")
        self.setup_tree()
        self.insert_data()

    def clear(self):
        self.tree.delete(*self.tree.get_children())
        self.tree.destroy()
        self.tree = ttk.Treeview(self)
        self.tree.pack(side="left", expand=True, fill="both")
        self.setup_tree()

    def setup_tree(self):
        self.tree.configure(yscrollcommand=self.scroll_bar.set)
        self.tree["columns"] = ("date", "value")
        self.tree.column("date", width=120, anchor="w")
        self.tree.column("value", width=90, anchor="w")
        self.tree.heading("date", text="Date")
        self.tree.heading("value", text="Value")

    def insert_data(self):
        data: list[list[database.Benchmark]] = database.view_benchmarks(self.theme)

        if len(data) == 0:
            return

        for activity in data:
            sample = activity[0]
            average = sum(bench.value for bench in activity) / len(activity)
            root_node = self.tree.insert(
                "",
                text=sample.name,
                index="end",
                values=(
                    "Last: " + delta(sample.datetime),
                    f"Average: {average:.2f}",
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

    def refresh(self):
        self.clear()
        self.insert_data()


class RecordTable(tk.Frame):
    def __init__(self, *args, theme, **kwargs):
        super(RecordTable, self).__init__(*args, **kwargs)
        self.theme = theme
        self.tree = ttk.Treeview(self, selectmode="browse")
        self.tree.pack(side="left", expand=True, fill="both")
        self.scroll_bar = ttk.Scrollbar(
            self, orient="vertical", command=self.tree.yview
        )
        self.scroll_bar.pack(side="right", fill="y")
        self.insert_data()

    def clear(self):
        self.tree.destroy()
        self.tree = ttk.Treeview(self, selectmode="browse")
        self.tree.pack(side="left", expand=True, fill="both")

    def setup_tree(self, headings):
        self.tree.configure(yscrollcommand=self.scroll_bar.set)
        # creating the headings and all that
        self.tree["columns"] = ("date", *(str(i) for i in range(len(headings))))
        self.tree["show"] = "headings"
        self.tree.column("date", width=120, anchor="w")
        self.tree.heading("date", text="Date")

    def insert_data(self):
        data = database.view_records(self.theme)
        if len(data) == 0:
            self.tree.insert("", "end", values=("Nothing to show...",))
        headings = database.view_record_types(self.theme)
        self.setup_tree(headings)
        # adding the headings for Record.values dictionary
        for i, heading in enumerate(headings):
            self.tree.column(str(i), width=90, anchor="c")
            self.tree.heading(str(i), text=heading.capitalize())

        # writing the data
        for record in data:
            date = record.datetime.strftime("%d/%m/%Y %H:%M:%S")

            self.tree.insert(
                "",
                "end",
                values=(
                    date,
                    *map(
                        lambda x: "_" if x is None else x,
                        (record.values.get(key) for key in headings),
                    ),
                ),
            )

    def refresh(self):
        self.clear()
        self.insert_data()


class Page(tk.Frame):
    def __init__(self, *args, theme: str, **kwargs):
        super(Page, self).__init__(*args, **kwargs)
        self.theme = theme
        self.record_table = RecordTable(theme=theme, master=self)
        self.benchmark_table = BenchmarkTable(theme=theme, master=self)

        self.int_validation = self.register(
            lambda x: x.replace(".", "", 1).isdigit() or x == ""
        )

        self.bench_name_entry = tk.Entry(self)
        self.bench_value_entry = tk.Entry(
            self, validate="all", validatecommand=(self.int_validation, "%P")
        )
        self.record_name_entry = tk.Entry(self)
        self.setup_gui()

    def setup_gui(self):
        self.record_table.grid(column=0, row=0, columnspan=3)
        self.benchmark_table.grid(column=4, row=0, columnspan=5)

        self.record_name_entry.grid(column=0, row=1, sticky="ew")
        tk.Button(self, command=self.create_record, text="Create Record").grid(
            column=1, row=1, sticky="w"
        )
        tk.Button(self, command=self.wait_for_record_entry, text="Add").grid(
            column=2, row=1, sticky="w"
        )

        tk.Label(self, text="Name: ").grid(column=4, row=1)
        self.bench_name_entry.grid(column=5, row=1)
        tk.Label(self, text="Value: ").grid(column=6, row=1)
        self.bench_value_entry.grid(column=7, row=1)
        tk.Button(self, command=self.add_benchmark, text="Add").grid(column=8, row=1)

    def add_benchmark(self):
        database.Benchmark(
            datetime.now(),
            self.theme,
            self.bench_name_entry.get(),
            float(self.bench_value_entry.get()),
        ).write_benchmark()
        self.benchmark_table.refresh()

    def wait_for_record_entry(self):
        RecordEntry(self.theme).wait()
        self.record_table.refresh()

    def create_record(self):
        name = self.record_name_entry.get()
        database.create_record(self.theme, name)
        self.record_table.refresh()


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
