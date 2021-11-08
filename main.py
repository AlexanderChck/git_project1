import sys
import datetime as dt

from PyQt5 import uic
from PyQt5.QtWidgets import QApplication, QInputDialog
from PyQt5.QtWidgets import QMainWindow
from EmployeeWnd import *
from DepartamentsWnd import *
from const import *
import xlsxwriter


class ScheduleWnd(QMainWindow):
    def __init__(self):
        super().__init__()
        self.sel_year = dt.datetime.now().year
        self.sel_month = dt.datetime.now().month
        self.sel_dep = 0
        self.search_str = ''
        self.schedule = {}
        self.count_day = {}
        uic.loadUi("main.ui", self)
        self.db_con = sqlite3.connect("schedule_db.sqlite")
        self.cur = self.db_con.cursor()
        self.full_clndr()
        self.fill_deps()
        self.tblw_schedule.itemClicked.connect(self.change_schedule)
        self.fill_schedule()
        self.btn_reftbl.clicked.connect(self.ref_tbl)
        self.btn_editemp.clicked.connect(self.edit_emp_wnd)
        self.btn_addemp.clicked.connect(self.add_emp_wnd)
        self.btn_chngdeps.clicked.connect(self.chng_dep_wnd)
        self.btn_print_table.clicked.connect(self.print_table)

    def full_clndr(self):
        cur_year = self.sel_year
        cur_month = self.sel_month
        # делаем возможным расчёт отпусков за этот год и последующие 4 годв
        for year in range(cur_year, cur_year + 5):
            self.cmb_year.addItem(str(year))
        for i in range(len(MONTH)):
            self.cmb_month.addItem(MONTH[i])
            # устанавливаем в качестве стартового значения нынешний месяц
            if cur_month == i + 1:
                self.cmb_month.setCurrentIndex(i)

    def fill_deps(self):
        self.cbx_dep.addItem(ALL_DEPS, 0)
        result = self.cur.execute(FOUND_DEP_NAME).fetchall()
        if len(result) > 1:
            index = 0
            for row in result:
                self.cbx_dep.addItem(row[1], row[0])
                if row[0] == self.sel_dep:
                    self.cbx_dep.setCurrentIndex(index)

    def clear_schedule(self):
        while self.tblw_schedule.columnCount() > 0:
            self.tblw_schedule.removeColumn(0)
        while self.tblw_schedule.rowCount() > 0:
            self.tblw_schedule.removeRow(0)
        self.schedule = {}
        self.count_day = {}

    def fill_schedule(self):
        # сначала очистим таблицу
        self.clear_schedule()

        # определим кол-во дней в выбранном месяце
        month_start = dt.date(self.sel_year, self.sel_month, 1)
        if self.sel_month != COUNT_MONTH:
            month_stop = dt.date(self.sel_year, self.sel_month + 1, 1)
        else:
            month_stop = dt.date(self.sel_year + 1, 1, 1)
        count_day = (month_stop - month_start).days

        # создаём заглавия для таблицы
        headers = ['Id', 'Фамилия', 'Имя', 'Отчество', 'Должность', 'Дни']
        for i in range(1, count_day + 1):
            headers.append(str(i))
        self.tblw_schedule.setColumnCount(len(headers))
        self.tblw_schedule.setHorizontalHeaderLabels(headers)
        self.tblw_schedule.hideColumn(0)

        que = "SELECT Id, Sname, Name, Patronymic, Post FROM Employees WHERE 1 = 1"
        where = []
        if self.sel_dep != 0:
            que += " AND DepartmentId = ?"
            where.append(self.sel_dep)
        if self.search_str != '':
            que += " AND (Sname like ? OR Name like ? OR Patronymic like ? OR Post like ?)"
            for h in range(4):
                where.append('%' + self.search_str + '%')
        result = self.cur.execute(que, tuple(where)).fetchall()

        for i, row in enumerate(result):
            self.get_schedule_by_emp(row[0], month_start, month_stop)
            self.tblw_schedule.setRowCount(
                self.tblw_schedule.rowCount() + 1)
            self.tblw_schedule.setItem(i, 0, QTableWidgetItem(str(row[0])))
            self.tblw_schedule.setItem(i, 1, QTableWidgetItem(str(row[1])))
            self.tblw_schedule.setItem(i, 2, QTableWidgetItem(str(row[2])))
            self.tblw_schedule.setItem(i, 3, QTableWidgetItem(str(row[3])))
            self.tblw_schedule.setItem(i, 4, QTableWidgetItem(str(row[4])))
            self.tblw_schedule.setItem(i, 5, QTableWidgetItem(str(self.count_day[row[0]])))
            for j in range(COUNT_HEADERS_WOUT_DAYS, count_day + 6):
                self.tblw_schedule.setItem(i, j, QTableWidgetItem(''))
                cur_day = dt.date(self.sel_year, self.sel_month, j - 5)
                self.tblw_schedule.item(i, j).setBackground(self.get_color(cur_day))
                if cur_day.strftime(YEAR_FORMAT) in self.schedule[row[0]]:
                    self.tblw_schedule.setItem(i, j, QTableWidgetItem('x'))
                    self.tblw_schedule.item(i, j).setBackground(GREEN)

        self.tblw_schedule.resizeColumnsToContents()

    def get_color(self, date):
        if date.weekday() >= 5:
            return RED
        return BLUE

    def get_schedule_by_emp(self, emp_id, month_start, month_stop):
        result = self.cur.execute(FOUND_DATE,
                    (emp_id, month_start.strftime(YEAR_FORMAT), month_stop.strftime(YEAR_FORMAT))).fetchall()
        dates = []
        for row in result:
            dates.append(row[0])
        self.schedule[emp_id] = dates

        year_start = dt.date(self.sel_year, 1, 1)
        year_stop = dt.date(self.sel_year + 1, 1, 1)
        result = self.cur.execute("""SELECT COUNT(*) FROM Schedule WHERE EmployeeId = ? AND Date >= ? AND
            Date < ?""", (emp_id, year_start, year_stop)).fetchall()
        self.count_day[emp_id] = result[0][0]

    def change_schedule(self, item):
        # проверяем, не выбран ли день отпуска
        if item.column() > 5:
            id = int(self.tblw_schedule.item(item.row(), 0).text())
            sel_day = item.column() - 5
            sel_date = dt.date(self.sel_year, self.sel_month, sel_day)
            cur = self.db_con.cursor()
            if sel_date.strftime(YEAR_FORMAT) not in self.schedule[id]:
                if self.count_day[id] < 28:
                    cur.execute(ADD_WEEKEND, (id, sel_date.strftime(YEAR_FORMAT))).fetchall()
                    self.db_con.commit()
                    self.tblw_schedule.item(item.row(), item.column()).setText('x')
                    self.tblw_schedule.item(item.row(), item.column()).setBackground(GREEN)
                    self.schedule[id].append(sel_date.strftime(YEAR_FORMAT))
                    self.count_day[id] += 1
            else:
                cur.execute(DELETE_WEEKEND,
                            (id, sel_date.strftime(YEAR_FORMAT))).fetchall()
                self.db_con.commit()
                self.tblw_schedule.item(item.row(), item.column()).setText('')
                self.tblw_schedule.item(item.row(), item.column()).setBackground(self.get_color(sel_date))
                self.schedule[id].remove(sel_date.strftime(YEAR_FORMAT))
                self.count_day[id] -= 1
            self.tblw_schedule.setItem(item.row(), 5, QTableWidgetItem(str(self.count_day[id])))

    def ref_tbl(self):
        self.sel_year = int(self.cmb_year.currentText())
        self.sel_month = self.cmb_month.currentIndex() + 1
        self.sel_dep = int(self.cbx_dep.itemData(self.cbx_dep.currentIndex()))
        self.search_str = self.find_line.text()
        self.fill_schedule()

    def print_table(self):
        name, ok_pressed = QInputDialog.getText(self, "Введите имя файла",
                                                "Сохранить файл как:")
        if ok_pressed:
            workbook = xlsxwriter.Workbook(name)
            worksheet = workbook.add_worksheet()

            for i in range(self.tblw_schedule.columnCount()):
                worksheet.write(0, i, self.tblw_schedule.horizontalHeaderItem(i).text())
            for i in range(self.tblw_schedule.rowCount()):
                for j in range(self.tblw_schedule.columnCount()):
                    worksheet.write(i + 1, j, self.tblw_schedule.item(i, j).text())

            workbook.close()

    def edit_emp_wnd(self):
        rows = list(set([i.row() for i in self.tblw_schedule.selectedItems()]))
        ids = [self.tblw_schedule.item(i, 0).text() for i in rows]
        if len(ids) == 0:
            return
        self.emp_wnd = EmployeeWnd(self, emp_id=ids[0])
        self.emp_wnd.show()
        result = self.emp_wnd.exec()
        if result != 0:
            self.fill_schedule()

    def add_emp_wnd(self):
        self.emp_wnd = EmployeeWnd(self)
        self.emp_wnd.show()
        result = self.emp_wnd.exec()
        if result != 0:
            self.fill_schedule()

    def chng_dep_wnd(self):
        self.dep_wnd = DepartamentsWnd(self)
        self.dep_wnd.show()


def except_hook(cls, exception, traceback):
    sys.__excepthook__(cls, exception, traceback)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    form = ScheduleWnd()
    form.show()
    sys.excepthook = except_hook
    sys.exit(app.exec())