import itertools
from datetime import datetime, timezone

import dearpygui.dearpygui as dpg
import dearpygui.demo as demo

import database


def localise(date: datetime):
    return date.replace(tzinfo=timezone.utc).astimezone(tz=None)


class BenchmarkTable:
    def __init__(self, theme: database.Theme, parent):
        self.theme = theme
        self.parent = parent
        self.setup_table()

    def setup_table(self):
        benchmark_types: list[database.DataType] = self.theme.get_types("benchmark")

        if len(benchmark_types) == 0:
            return

        for activity in benchmark_types:
            datapoints = activity.get_data_points()
            average = sum(bench.val for bench in datapoints) / len(datapoints)
            with dpg.tree_node(parent=self.parent, label=activity.name):
                with dpg.table():
                    dpg.add_table_column(label="Date")
                    dpg.add_table_column(label=f"Average: {average:.2f}")
                    for benchmark in datapoints:
                        with dpg.table_row():
                            date = localise(benchmark.timestamp).strftime(
                                "%d/%m/%Y %H:%M:%S"
                            )
                            dpg.add_text(date)
                            dpg.add_text(str(benchmark.val))

    def clear(self):
        pass

    def refresh(self):
        self.clear()
        self.setup_table()


class RecordTable:
    def __init__(self, theme: database.Theme, parent):
        self.theme = theme
        self.parent = parent
        self.setup_table()

    def setup_table(self):
        record_types = self.theme.get_types("record")
        if len(record_types) == 0:
            dpg.add_text("Nothing to show!")
            return

        with dpg.table(parent=self.parent):
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


class ThemeTab:
    def __init__(self, theme: database.Theme, parent):
        self.theme = theme
        with dpg.tab(parent=parent, label=theme.name) as self.tab_id:
            with dpg.table(parent=self.tab_id, header_row=False, resizable=True):
                dpg.add_table_column()
                dpg.add_table_column()
                with dpg.table_row():
                    with dpg.child_window() as record_window:
                        self.record_table = RecordTable(
                            theme=theme, parent=record_window
                        )
                    with dpg.child_window() as benchmark_window:
                        self.benchmark_table = BenchmarkTable(
                            theme=theme, parent=benchmark_window
                        )


def main():
    dpg.create_context()
    dpg.create_viewport(title="MonkeLogger", width=600, height=600)

    with dpg.window(tag="Primary Window"):
        with dpg.menu_bar():
            with dpg.menu(label="Tools"):
                dpg.add_menu_item(
                    label="Show About", callback=lambda: dpg.show_tool(dpg.mvTool_About)
                )
                dpg.add_menu_item(
                    label="Show Metrics",
                    callback=lambda: dpg.show_tool(dpg.mvTool_Metrics),
                )
                dpg.add_menu_item(
                    label="Show Documentation",
                    callback=lambda: dpg.show_tool(dpg.mvTool_Doc),
                )
                dpg.add_menu_item(
                    label="Show Debug", callback=lambda: dpg.show_tool(dpg.mvTool_Debug)
                )
                dpg.add_menu_item(
                    label="Show Style Editor",
                    callback=lambda: dpg.show_tool(dpg.mvTool_Style),
                )
                dpg.add_menu_item(
                    label="Show Font Manager",
                    callback=lambda: dpg.show_tool(dpg.mvTool_Font),
                )
                dpg.add_menu_item(
                    label="Show Item Registry",
                    callback=lambda: dpg.show_tool(dpg.mvTool_ItemRegistry),
                )
                dpg.add_menu_item(label="Show Demo", callback=lambda: demo.show_demo())

        themes = database.get_all_themes()
        with dpg.tab_bar() as tb:
            for theme in themes:
                ThemeTab(theme, parent=tb)

    dpg.setup_dearpygui()
    dpg.show_viewport()
    dpg.set_primary_window("Primary Window", True)
    dpg.start_dearpygui()
    dpg.destroy_context()


if __name__ == "__main__":
    main()
