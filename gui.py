import itertools
import tkinter as tk
from datetime import datetime, timezone
from tkinter import ttk

import database


def delta(date: datetime) -> str:
    # 'x days ago'
    d = abs(datetime.utcnow() - date)
    return (
        f"{d.days} {'days' if d.days != 1 else 'day'} ago"
        if d.days > 0
        else f"{d.total_seconds() / 3600:.2f} hours ago"
    )


def localise(date: datetime):
    return date.replace(tzinfo=timezone.utc).astimezone(tz=None)


class RecordEntry:
    def __init__(self, theme: database.Theme):
        self.root = tk.Toplevel()
        self.root.resizable(False, False)
        self.theme = theme
        self.entries: list[tk.Entry] = []
        self.int_validation = self.root.register(
            lambda x: x.replace(".", "", 1).isdigit() or x == ""
        )
        self.types = self.theme.get_types(display_type="record")
        self.headings = [i.name for i in self.types]
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
        now = datetime.utcnow()
        user_entered_values = map(lambda x: x.get(), self.entries)
        none_for_empty_string = map(
            lambda x: None if x == "" else x, user_entered_values
        )
        for i, val in zip(self.types, none_for_empty_string):
            database.DataPoint(i.id, now, now, val).write()  # second now can change
        self.root.destroy()

    def wait(self):
        self.root.grab_set()
        self.root.wait_window()


class BenchmarkTable(tk.Frame):
    def __init__(self, *args, theme: database.Theme, **kwargs):
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
        self.scroll_bar.configure(command=self.tree.yview)
        self.setup_tree()

    def setup_tree(self):
        self.tree.configure(yscrollcommand=self.scroll_bar.set)
        self.tree["columns"] = ("date", "value")
        self.tree.column("date", width=120, anchor="w")
        self.tree.column("value", width=90, anchor="w")
        self.tree.heading("date", text="Date")
        self.tree.heading("value", text="Value")

    def insert_data(self):
        benchmark_types: list[database.DataType] = self.theme.get_types("benchmark")

        if len(benchmark_types) == 0:
            return

        for activity in benchmark_types:
            datapoints = activity.get_data_points()
            average = sum(bench.val for bench in datapoints) / len(datapoints)
            root_node = self.tree.insert(
                "",
                text=activity.name,
                index="end",
                values=(
                    "Last: " + delta(datapoints[0].timestamp),
                    f"Average: {average:.2f}",
                ),
            )
            for benchmark in datapoints:
                date = localise(benchmark.timestamp).strftime("%d/%m/%Y %H:%M:%S")
                self.tree.insert(
                    root_node,
                    "end",
                    text=activity.name,
                    values=(date, benchmark.val),
                )

    def refresh(self):
        self.clear()
        self.insert_data()


class RecordTable(tk.Frame):
    def __init__(self, *args, theme: database.Theme, **kwargs):
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
        self.scroll_bar.configure(command=self.tree.yview)

    def setup_tree(self, headings):
        self.tree.configure(yscrollcommand=self.scroll_bar.set)
        # creating the headings and all that
        self.tree["columns"] = ("date", *(str(i) for i in range(len(headings))))
        self.tree["show"] = "headings"
        self.tree.column("date", width=120, anchor="w")
        self.tree.heading("date", text="Date")

    def insert_data(self):
        record_types = self.theme.get_types("record")

        if len(record_types) == 0:
            self.tree.insert("", "end", values=("Nothing to show...",))

        headings = [i.name for i in record_types]
        self.setup_tree(headings)

        # adding the headings for Record.values dictionary
        for i, heading in enumerate(headings):
            self.tree.column(str(i), width=90, anchor="c")
            self.tree.heading(str(i), text=heading.capitalize())

        data = itertools.chain.from_iterable(
            [record_type.get_data_points() for record_type in record_types]
        )
        data = sorted(list(data), key=lambda x: x.timestamp)
        data = itertools.groupby(data, key=lambda x: x.timestamp)
        type_ids = [i.id for i in record_types]

        for t, group in data:
            record = []
            datapoints: list[database.DataPoint] = list(group)
            for type_id in type_ids:
                val = next(
                    (data.val or "_" for data in datapoints if data.type_id == type_id),
                    "_",
                )
                record.append(val)

            date = localise(t).strftime("%d/%m/%Y %H:%M:%S")
            self.tree.insert(
                "",
                "end",
                values=(
                    date,
                    *record,
                ),
            )

    def refresh(self):
        self.clear()
        self.insert_data()


class Page(tk.Frame):
    def __init__(self, *args, theme: database.Theme, **kwargs):
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
        now = datetime.utcnow()
        benchmark_type = database.DataType.new(
            created_on=now,
            theme=self.theme,
            name=self.bench_name_entry.get(),
            display_type="benchmark",
        )
        database.DataPoint(
            type_id=benchmark_type.id,
            created_on=now,
            timestamp=now,
            val=float(self.bench_value_entry.get()),
        ).write()
        self.benchmark_table.refresh()

    def wait_for_record_entry(self):
        RecordEntry(self.theme).wait()
        self.record_table.refresh()

    def create_record(self):
        now = datetime.utcnow()
        name = self.record_name_entry.get()
        database.DataType.new(
            created_on=now, theme=self.theme, name=name, display_type="record"
        )
        self.record_table.refresh()


def main():
    root = tk.Tk()
    note_book = ttk.Notebook(master=root)

    themes = database.get_all_themes()
    for theme in themes:
        page = Page(master=note_book, theme=theme)
        page.grid(column=0, row=0, sticky="ew")
        note_book.add(page, text=theme.name.capitalize())

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
        name = contents.get()
        if name.lower() in themes:
            return
        now = datetime.utcnow()
        # register the theme in the database
        requested_theme = database.Theme.new(now, name)

        # add the theme to the list so that it can't be made again
        themes.append(requested_theme)

        # update the notebook with a page for the theme
        theme_page = Page(master=note_book, theme=requested_theme)
        note_book.insert(0, theme_page, text=requested_theme.name.capitalize())

    tk.Button(new_theme_frame, command=make_theme, text="Create").grid(column=3, row=0)
    note_book.add(new_theme_frame, text="+")

    note_book.grid(column=0, row=0, sticky="ew")
    root.resizable(False, False)
    root.mainloop()


if __name__ == "__main__":
    main()
    database.ConnectionPool.close()
