import sqlite3
import sys
import datetime as dt

from PyQt5 import uic
from PyQt5.QtWidgets import QApplication
from PyQt5.QtWidgets import QMainWindow, QTableWidgetItem, QWidget
from PyQt5.QtGui import QColor


class ScheduleWnd(QMainWindow):
    def __init__(self):
        super().__init__()
        uic.loadUi("main.ui", self)
        self.full_clndr()
        self.tblw_schedule.itemClicked.connect(self.change_schedule)
        self.con = sqlite3.connect("schedule_db.sqlite")
        self.fill_schedule()
        self.btn_editemp.clicked.connect(self.edit_emp_wnd)
        self.btn_addemp.clicked.connect(self.add_emp_wnd)
        self.btn_chngdeps.clicked.connect(self.chng_dep_wnd)

    def full_clndr(self):
        cur_year = dt.datetime.now().year
        cur_month = dt.datetime.now().month
        months = ['Январь', 'Февраль', 'Март', 'Апрель', 'Май', 'Июнь', 'Июль', 'Август', 'Сентябрь', 'Октябрь',
                  'Ноябрь', 'Декабрь']
        for year in range(cur_year, cur_year + 5):
            self.cmb_year.addItem(str(year))
        for i in range(len(months)):
            self.cmb_month.addItem(months[i])
            if cur_month == i + 1:
                self.cmb_month.setCurrentIndex(i)

    def fill_schedule(self):
        headers = []
        headers.append('Фамилия')
        headers.append('Имя')
        headers.append('Отчество')
        headers.append('Должность')
        for i in range(1, 32):
            headers.append(str(i))
        self.tblw_schedule.setColumnCount(len(headers))
        self.tblw_schedule.setHorizontalHeaderLabels(headers)

        cur = self.con.cursor()
        result = cur.execute("SELECT * FROM Employees").fetchall()

        for i, row in enumerate(result):
            self.tblw_schedule.setRowCount(
                self.tblw_schedule.rowCount() + 1)
            self.tblw_schedule.setItem(i, 0, QTableWidgetItem(row[1]))
            self.tblw_schedule.setItem(i, 1, QTableWidgetItem(row[2]))
            self.tblw_schedule.setItem(i, 2, QTableWidgetItem(row[3]))
            self.tblw_schedule.setItem(i, 3, QTableWidgetItem(row[4]))
            for j in range(4, 31 + 4):
                self.tblw_schedule.setItem(i, j, QTableWidgetItem(''))

        self.tblw_schedule.resizeColumnsToContents()

    def change_schedule(self, item):
        print('row: ' + str(item.row()) + ' col: ' + str(item.column()))
        if item.column() > 3:
            self.tblw_schedule.item(item.row(), item.column()).setBackground(QColor(0, 150,  100))

    def edit_emp_wnd(self):
        self.emp_wnd = EmployeeWnd(self, emp_id=1)
        self.emp_wnd.show()

    def add_emp_wnd(self):
        self.emp_wnd = EmployeeWnd(self)
        self.emp_wnd.show()

    def chng_dep_wnd(self):
        self.dep_wnd = DepartamentsWnd(self)
        self.dep_wnd.show()


class EmployeeWnd(QWidget):
    def __init__(self, *args, emp_id=0):
        super().__init__()
        uic.loadUi("employer.ui", self)
        if emp_id == 0:
            self.setWindowTitle('Добавление сотрудника')
            self.btn_addedit.setText('Добавить')
        else:
            self.setWindowTitle('Редактирование сотрудника')
            self.btn_addedit.setText('Изменить')


class DepartamentsWnd(QWidget):
    def __init__(self, *args):
        super().__init__()
        uic.loadUi("departs.ui", self)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = ScheduleWnd()
    ex.show()
    sys.exit(app.exec())