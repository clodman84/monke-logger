import itertools
from datetime import datetime, timezone

import dearpygui.dearpygui as dpg

import database


def localise(date: datetime):
    return date.replace(tzinfo=timezone.utc).astimezone(tz=None)


class BenchmarkTable:
    def __init__(self, theme: database.Theme, parent):
        self.theme = theme
        self.parent = parent
        self.tracked_tables = {}
        self.setup_table()

    def setup_table(self):
        benchmark_types: list[database.DataType] = self.theme.get_types("benchmark")

        if len(benchmark_types) == 0:
            return

        for activity in benchmark_types:
            datapoints = activity.get_data_points()
            average = sum(bench.val for bench in datapoints) / len(datapoints)
            with dpg.tree_node(parent=self.parent, label=activity.name):
                with dpg.table(tag=f"{activity.id, activity.theme.id}"):
                    dpg.add_table_column(label="Date")
                    avg_heading = dpg.add_table_column(label=f"Average: {average:.2f}")
                    self.tracked_tables[f"{activity.id, activity.theme.id}"] = (
                        average,
                        len(datapoints),
                        avg_heading,
                    )
                    for benchmark in datapoints:
                        with dpg.table_row():
                            date = localise(benchmark.timestamp).strftime(
                                "%d/%m/%Y %H:%M:%S"
                            )
                            dpg.add_text(date)
                            dpg.add_text(str(benchmark.val))

    def update(self, benchmark: database.DataPoint, datatype: database.DataType):
        table_id = f"{datatype.id, datatype.theme.id}"
        if table_id in self.tracked_tables:
            with dpg.table_row(parent=table_id):
                date = localise(benchmark.timestamp).strftime("%d/%m/%Y %H:%M:%S")
                dpg.add_text(date)
                dpg.add_text(str(benchmark.val))
            average, number_of_datapoints, heading_id = self.tracked_tables[table_id]
            new_average = (average * number_of_datapoints + benchmark.val) / (
                number_of_datapoints + 1
            )
            dpg.configure_item(heading_id, label=f"Average: {new_average:.2f}")
            return

        with dpg.tree_node(parent=self.parent, label=datatype.name):
            with dpg.table(tag=table_id):
                dpg.add_table_column(label="Date")
                avg_heading = dpg.add_table_column(
                    label=f"Average: {benchmark.val:.2f}"
                )
                self.tracked_tables[table_id] = (benchmark.val, 1, avg_heading)
                with dpg.table_row():
                    date = localise(benchmark.timestamp).strftime("%d/%m/%Y %H:%M:%S")
                    dpg.add_text(date)
                    dpg.add_text(str(benchmark.val))


class RecordTable:
    def __init__(self, theme: database.Theme, parent):
        self.theme = theme
        self.parent = parent
        self.setup_table()

    def setup_table(self):
        record_types = self.theme.get_types("record")
        if len(record_types) == 0:
            dpg.add_text("Nothing to show!")
            self.table = None
            return

        with dpg.table(
            parent=self.parent, resizable=True, reorderable=True, hideable=True
        ) as self.table:
            headings = [i.name for i in record_types]
            dpg.add_table_column(label="Date")
            for heading in headings:
                dpg.add_table_column(label=heading)

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
                        (
                            data.val or "_"
                            for data in datapoints
                            if data.type_id == type_id
                        ),
                        "_",
                    )
                    record.append(val)

                with dpg.table_row():
                    date = localise(t).strftime("%d/%m/%Y %H:%M:%S")
                    dpg.add_text(date)
                    for data in record:
                        dpg.add_text(str(data))

    def update(self, datapoints: list[database.DataPoint]):
        if not self.table:
            self.setup_table()
            return

        type_ids = tuple(i.id for i in self.theme.get_types("record"))
        record = []
        for type_id in type_ids:
            val = next(
                (data.val or "_" for data in datapoints if data.type_id == type_id),
                "_",
            )
            record.append(val)

        with dpg.table_row(parent=self.table):
            date = localise(datapoints[0].timestamp).strftime("%d/%m/%Y %H:%M:%S")
            dpg.add_text(date)
            for data in record:
                dpg.add_text(str(data))

    def refresh(self):
        if self.table:
            dpg.delete_item(self.table)
        self.setup_table()


class ThemeTab:
    def __init__(self, theme: database.Theme, parent):
        self.theme = theme
        with dpg.tab(parent=parent, label=theme.name) as self.tab_id:
            with dpg.table(
                parent=self.tab_id, resizable=True, reorderable=True, hideable=True
            ):
                dpg.add_table_column(label="Records")
                dpg.add_table_column(label="Benchmarks")
                with dpg.table_row():
                    with dpg.child_window() as record_window:
                        with dpg.group(horizontal=True):
                            dpg.add_button(label="New", callback=self.create_record)
                            dpg.add_button(label="Add", callback=self.add_record)
                        dpg.add_separator()
                        self.record_table = RecordTable(
                            theme=theme, parent=record_window
                        )
                    with dpg.child_window() as benchmark_window:
                        with dpg.group(horizontal=True):
                            dpg.add_text("Name")
                            self.bench_name_input = dpg.add_input_text(width=200)
                            dpg.add_text("Value")
                            self.bench_val_input = dpg.add_input_text(
                                width=100, decimal=True
                            )
                            dpg.add_button(label="Add", callback=self.add_benchmark)
                        dpg.add_separator()
                        self.benchmark_table = BenchmarkTable(
                            theme=theme, parent=benchmark_window
                        )

    def add_benchmark(self):
        name = dpg.get_value(self.bench_name_input)
        val = dpg.get_value(self.bench_val_input)
        now = datetime.utcnow()
        benchmark_type = database.DataType.new(
            created_on=now,
            theme=self.theme,
            name=name,
            display_type="benchmark",
        )
        benchmark = database.DataPoint(
            type_id=benchmark_type.id, created_on=now, timestamp=now, val=float(val)
        )
        benchmark.write()
        self.benchmark_table.update(benchmark, benchmark_type)

    def add_record(self):
        types = self.theme.get_types("record")

        def create(textboxes: list[int | str]):
            now = datetime.utcnow()
            user_entered_values = dpg.get_values(textboxes)
            none_for_empty_string = map(
                lambda x: None if x == "" else x, user_entered_values
            )
            datapoints = []
            for i, val in zip(types, none_for_empty_string):
                p = database.DataPoint(i.id, now, now, val)
                p.write()
                datapoints.append(p)

            self.record_table.update(datapoints)
            dpg.delete_item("create_record_popup")

        with dpg.window(
            label="Enter Details",
            modal=True,
            tag="create_record_popup",
            no_close=True,
            width=200,
        ):
            boxes = []
            with dpg.table(header_row=False):
                dpg.add_table_column()
                dpg.add_table_column()
                for ty in types:
                    with dpg.table_row():
                        dpg.add_text(ty.name)
                        t = dpg.add_input_text(decimal=True)
                        boxes.append(t)

            dpg.add_separator()
            with dpg.group(horizontal=True):
                dpg.add_button(label="Create", callback=lambda: create(boxes))
                dpg.add_button(
                    label="Cancel",
                    callback=lambda: dpg.delete_item("create_record_popup"),
                )

    def create_record(self):
        def create(textbox):
            name = dpg.get_value(textbox)
            now = datetime.utcnow()
            database.DataType.new(
                created_on=now, theme=self.theme, name=name, display_type="record"
            )
            dpg.delete_item("create_record_popup")
            self.record_table.refresh()

        with dpg.window(
            label="Enter Details",
            modal=True,
            tag="create_record_popup",
            no_close=True,
            no_resize=True,
            width=200,
            height=50,
        ):
            with dpg.group(horizontal=True):
                dpg.add_text("Name")
                t = dpg.add_input_text()
            dpg.add_separator()
            with dpg.group(horizontal=True):
                dpg.add_button(label="Create", callback=lambda: create(t))
                dpg.add_button(
                    label="Cancel",
                    callback=lambda: dpg.delete_item("create_record_popup"),
                )


def main():
    dpg.create_context()
    dpg.create_viewport(title="MonkeLogger", width=600, height=600)

    themes = database.get_all_themes()

    def make_theme():
        name = dpg.get_value("new_theme_input")
        if name.lower() in (t.name.lower() for t in themes):
            return
        now = datetime.utcnow()
        # register the theme in the database
        requested_theme = database.Theme.new(now, name)
        # add the theme to the list so that it can't be made again
        themes.append(requested_theme)
        # update the notebook with a page for the theme
        ThemeTab(theme=requested_theme, parent="theme_tab")

    with dpg.window(tag="Primary Window"):
        with dpg.tab_bar(tag="theme_tab"):
            for theme in themes:
                ThemeTab(theme, parent="theme_tab")
            with dpg.tab(label="+", order_mode=dpg.mvTabOrder_Trailing):
                with dpg.child_window():
                    with dpg.group(horizontal=True):
                        dpg.add_text("Name")
                        dpg.add_input_text(tag="new_theme_input")
                        dpg.add_button(label="Create", callback=make_theme)

    dpg.setup_dearpygui()
    dpg.show_viewport()
    dpg.set_primary_window("Primary Window", True)
    dpg.start_dearpygui()
    dpg.destroy_context()


if __name__ == "__main__":
    main()
