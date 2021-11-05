import sqlite3
import sys
import datetime as dt

from PyQt5 import uic
from PyQt5.QtCore import Qt, QDate
from PyQt5.QtWidgets import QApplication, QInputDialog
from PyQt5.QtWidgets import QMainWindow, QTableWidgetItem, QWidget, QMessageBox
from PyQt5.QtGui import QColor
# import xlsxwriter
from collections import defaultdict
# from PyQt5.uic.properties import QtGui


class ScheduleWnd(QMainWindow):
    def __init__(self):
        super().__init__()
        self.sel_year = dt.datetime.now().year
        self.sel_month = dt.datetime.now().month
        self.sel_dep = 0
        self.search_str = ''
        self.schedule = {}
        # self.count_day = {}
        # defaultdict(lambda: 0, self.count_day)
        uic.loadUi("main.ui", self)
        # self.tblw_schedule.setSelectionMode(QtGui.QAbstractItemView.SingleSelection)
        self.db_con = sqlite3.connect("schedule_db.sqlite")
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
        months = ['Январь', 'Февраль', 'Март', 'Апрель', 'Май', 'Июнь', 'Июль', 'Август', 'Сентябрь', 'Октябрь',
                  'Ноябрь', 'Декабрь']
        # делаем возможным расчёт отпусков за этот год и последующие 4 годв
        for year in range(cur_year, cur_year + 5):
            self.cmb_year.addItem(str(year))
        for i in range(len(months)):
            self.cmb_month.addItem(months[i])
            # устанавливаем в качестве стартового значения нынешний месяц
            if cur_month == i + 1:
                self.cmb_month.setCurrentIndex(i)

    def fill_deps(self):
        self.cbx_dep.addItem('Все отделы', 0)
        cur = self.db_con.cursor()
        result = cur.execute("""SELECT Id, Name FROM Departments""").fetchall()
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
        # self.count_day = {}

    def fill_schedule(self):
        # сначала очистим таблицу
        self.clear_schedule()

        # определим кол-во дней в выбранном месяце
        month_start = dt.date(self.sel_year, self.sel_month, 1)
        if self.sel_month != 12:
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

        cur = self.db_con.cursor()
        que = "SELECT Id, Sname, Name, Patronymic, Post FROM Employees WHERE 1 = 1"
        where = []
        if self.sel_dep != 0:
            que += " AND DepartmentId = ?"
            where.append(self.sel_dep)
        if self.search_str != '':
            que += " AND (Sname like ? OR Name like ? OR Patronymic like ? OR Post like ?)"
            for h in range(4):
                where.append('%' + self.search_str + '%')
        result = cur.execute(que, tuple(where)).fetchall()

        for i, row in enumerate(result):
            self.get_schedule_by_emp(row[0], month_start, month_stop)
            self.tblw_schedule.setRowCount(
                self.tblw_schedule.rowCount() + 1)
            self.tblw_schedule.setItem(i, 0, QTableWidgetItem(str(row[0])))
            self.tblw_schedule.setItem(i, 1, QTableWidgetItem(str(row[1])))
            self.tblw_schedule.setItem(i, 2, QTableWidgetItem(str(row[2])))
            self.tblw_schedule.setItem(i, 3, QTableWidgetItem(str(row[3])))
            self.tblw_schedule.setItem(i, 4, QTableWidgetItem(str(row[4])))
            self.tblw_schedule.setItem(i, 5, QTableWidgetItem('Скоро будет сделано'))
            for j in range(6, count_day + 6):
                self.tblw_schedule.setItem(i, j, QTableWidgetItem(''))
                cur_day = dt.date(self.sel_year, self.sel_month, j - 5)
                self.tblw_schedule.item(i, j).setBackground(self.get_color(cur_day))
                if cur_day.strftime('%Y-%m-%d') in self.schedule[row[0]]:
                    self.tblw_schedule.item(i, j).setBackground(QColor(144, 238, 144))

        self.tblw_schedule.resizeColumnsToContents()

    def get_color(self, date):
        if date.weekday() >= 5:
            return QColor(250, 128, 114)
        return QColor(135, 206, 250)

    def get_schedule_by_emp(self, emp_id, month_start, month_stop):
        cur = self.db_con.cursor()
        result = cur.execute("""SELECT Date FROM Schedule WHERE EmployeeId = ? AND Date >= ? AND Date < ?""",
                             (emp_id, month_start.strftime('%Y-%m-%d'), month_stop.strftime('%Y-%m-%d'))).fetchall()
        dates = []
        for row in result:
            dates.append(row[0])
        self.schedule[emp_id] = dates

    def change_schedule(self, item):
        # print используется как подсказка, в итоговом коде его не будет
        # print('row: ' + str(item.row()) + ' col: ' + str(item.column()))

        # проверяем, не выбран ли день отпуска
        if item.column() > 5:
            id = int(self.tblw_schedule.item(item.row(), 0).text())
            sel_day = item.column() - 5
            sel_date = dt.date(self.sel_year, self.sel_month, sel_day)
            cur = self.db_con.cursor()
            if sel_date.strftime('%Y-%m-%d') not in self.schedule[id]:
                cur.execute("INSERT INTO Schedule VALUES (?, ?)", (id, sel_date.strftime('%Y-%m-%d'))).fetchall()
                self.db_con.commit()
                # self.count_day[sel_day] += 1
                self.tblw_schedule.item(item.row(), item.column()).setBackground(QColor(144, 238, 144))
            else:
                cur.execute("DELETE FROM Schedule WHERE EmployeeId = ? AND Date = ?",
                            (id, sel_date.strftime('%Y-%m-%d'))).fetchall()
                self.db_con.commit()
                # self.count_day[sel_day] -= 1
                self.tblw_schedule.item(item.row(), item.column()).setBackground(self.get_color(sel_date))

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

            for i in range(self.tblw_schedule.rowCount()):
                for j in range(self.tblw_schedule.rowCount()):
                    worksheet.write(i, j, self.tblw_schedule.item(i, j))

            workbook.close()

    def edit_emp_wnd(self):
        rows = list(set([i.row() for i in self.tblw_schedule.selectedItems()]))
        ids = [self.tblw_schedule.item(i, 0).text() for i in rows]
        if len(ids) == 0:
            return
        self.emp_wnd = EmployeeWnd(self, emp_id=ids[0])
        self.emp_wnd.show()

    def add_emp_wnd(self):
        self.emp_wnd = EmployeeWnd(self)
        self.emp_wnd.setWindowFlags(Qt.Dialog)
        self.emp_wnd.windowModality = Qt.WindowModal
        self.emp_wnd.show()

    def chng_dep_wnd(self):
        self.dep_wnd = DepartamentsWnd(self)
        self.dep_wnd.show()


class EmployeeWnd(QWidget):
    def __init__(self, *args, emp_id=0):
        super().__init__()
        uic.loadUi("employer.ui", self)
        # self.con = sqlite3.connect("schedule_db.sqlite", detect_types=sqlite3.PARSE_DECLTYPES | sqlite3.PARSE_COLNAMES)
        self.con = sqlite3.connect("schedule_db.sqlite")
        self.cur = self.con.cursor()
        self.headers = ['Id', 'Sname', 'Name', 'Patronymic', 'Post', 'INN', 'DepartmentId', 'BDate', 'Gender']
        self.cbx_gender.addItems(['Мужской', 'Женский'])
        self.emp_id = emp_id
        self.btn_addedit.clicked.connect(self.addedit)
        self.btn_close.clicked.connect(self.close_wnd)
        # проверяем, какое действие собирается совершить пользователь
        if emp_id == 0:
            self.setWindowTitle('Добавление сотрудника')
            self.btn_addedit.setText('Добавить')
            self.fill_cbx_dep()
        else:
            self.setWindowTitle('Редактирование сотрудника')
            self.btn_addedit.setText('Изменить')
            self.full_form()

    # добавляем в cbx_dep
    def fill_cbx_dep(self, cur_dep_id=-1):
        result = self.cur.execute("""SELECT Id, Name FROM Departments""").fetchall()
        if len(result) > 1:
            index = 0
            for row in result:
                self.cbx_dep.addItem(row[1], row[0])
                if row[0] == cur_dep_id:
                    self.cbx_dep.setCurrentIndex(index)
                    #index++

    def full_form(self):
        result = self.cur.execute("""SELECT Sname, Name, Patronymic, Post, INN, DepartmentId, BDate,
            Gender FROM Employees WHERE Id = ?""", (self.emp_id, )).fetchall()
        row = result[0]
        self.sname_inpt.setText(str(row[0]))
        self.name_inpt.setText(str(row[1]))
        self.patr_inpt.setText(str(row[2]))
        self.post_inpt.setText(str(row[3]))
        self.inn_inpt.setText(str(row[4]))
        self.fill_cbx_dep(row[5])
        self.Bdate_inpt.setDate(QDate.fromString(row[6], Qt.ISODate))
        self.cbx_gender.setCurrentIndex(row[7])

    # проверяем, правильно ли введён ИНН. Временно не работает
    def check_inn(self):
        inn = self.inn_inpt.text()
        if inn.isdigit() is False or len(inn) != 12:
            raise TypeError('Введённый ИНН не соответствует стандартам')
        # Константы позже будут переведены
        FST_NUM_LST = [7, 2, 4, 10, 3, 5, 9, 4, 6, 8]
        SCD_NUM_LST = [3, 7, 2, 4, 10, 3, 5, 9, 4, 6, 8]
        fst_num, scd_num = 0, 0
        for i in range(len(FST_NUM_LST)):
            fst_num += int(inn[i]) * FST_NUM_LST[i]
            scd_num += int(inn[i]) * SCD_NUM_LST[i]
        scd_num += int(inn[-1]) * SCD_NUM_LST[-1]
        if fst_num != int(inn) // 10 % 10 and scd_num != int(inn) % 10:
            raise ValueError('Неправильный ИНН')

    def edit_emp(self, emp_id):
        self.cur.execute("""Update Employees set Sname = ?, Name = ?, Patronymic = ?, Post = ?, INN = ?, DepartmentId = ?,
            BDate = ?, Gender = ? WHERE Id = ?""", (self.values[0], self.values[1], self.values[2], self.values[3],
            self.values[4], self.values[5], self.values[6], self.values[7], emp_id, ))
        self.con.commit()

    def add_emp(self):
        try:
            self.cur.execute("INSERT INTO Employees()"" VALUES (?, ?, ?, ?, ?, ?, ?, ?)", (tuple(self.values,))).fetchall()
            self.con.commit()
        except Exception as e:
            print(f'error: {e}')
            return

    def addedit(self):
        #self.check_inn()
        date = self.Bdate_inpt.date().toString(Qt.ISODate)
        # создаём список значений виджетов employer.ui
        self.values = [self.sname_inpt.text(), self.name_inpt.text(), self.patr_inpt.text(), self.post_inpt.text(),
                  self.inn_inpt.text(), int(self.cbx_dep.itemData(self.cbx_dep.currentIndex())), date,
                       self.cbx_gender.currentIndex()]
        try:
            # проверяем, хочет ли пользователь редактировать данные о сотруднике
            if self.emp_id != 0:
                self.edit_emp(self.emp_id)
            else:
                self.add_emp()
        except Exception as e:
            #self.error_lbl.setText(f'Произошла ошибка: {e}')
            print(e)

    # закрываем окно employer.ui
    def close_wnd(self):
        self.close()


class DepartamentsWnd(QWidget):
    def __init__(self, *args):
        super().__init__()
        self.ignore_change = False
        uic.loadUi("departs.ui", self)
        self.tblw_deps.itemChanged.connect(self.change_table)
        self.btn_add.clicked.connect(self.add_row)
        self.btn_del.clicked.connect(self.del_row)
        self.btn_close.clicked.connect(self.close_wnd)
        self.con = sqlite3.connect("schedule_db.sqlite")
        self.fill_table()

    def fill_table(self):
        self.ignore_change = True
        # заполним заголовки в таблице
        headers = ['Id', 'Name']
        # заголовок с Id мы скроем, пользователю не нужно его показывать
        # а нам он нужен, мы ез него будем вытаскивать Id записи для изменения и удаления в базе
        self.tblw_deps.setColumnCount(len(headers))
        self.tblw_deps.setHorizontalHeaderLabels(headers)
        # скроем первый столбец
        self.tblw_deps.hideColumn(0)

        cur = self.con.cursor()
        result = cur.execute("SELECT Id, Name FROM Departments").fetchall()

        # цикл по записям, которые нам вернул запрос
        for i, row in enumerate(result):
            # мы не знаем сколько у нас будет строк, поэтому будем каждый раз прибавлть одну строку
            self.tblw_deps.setRowCount(self.tblw_deps.rowCount() + 1)
            # выводим первое поле из запроса - Id
            self.tblw_deps.setItem(i, 0, QTableWidgetItem(str(row[0])))
            # теперь второе - Name
            self.tblw_deps.setItem(i, 1, QTableWidgetItem(str(row[1])))
        # возвращаем обработку сигналов на изменение
        self.ignore_change = False

# этот метод будет вызываться при изменении любой ячейки
    def change_table(self, item):
        if self.ignore_change == True:
            # игнорируем изменения
            return
        if item.column() == 0:
            # изменилось значения ячейки с Id, мы только сами меняем это значение
            # игнорируем
            return

        # для работы с БД
        cur = self.con.cursor()

        # сначала определим Id записи в базе, Id хранится в первом столбце
        # сначала получим саму ячейку с Id, а после значение Id (посредством text())
        id = QTableWidgetItem(self.tblw_deps.item(item.row(), 0)).text()

        # если в Id пустая строка, значит нужно добавить новую запись в базу
        if len(id) == 0:
            cur.execute("INSERT INTO Departments (Name) VALUES (?)", (item.text(),))
            self.con.commit()
            # получим id добавленной записи
            id = cur.lastrowid
            # запишем id в таблицу
            self.tblw_deps.setItem(item.row(), 0, QTableWidgetItem(str(id)))
        # если Id не пустой, нужно отредактировать значение в базе
        else:
            id = int(id)
            cur.execute("UPDATE Departments SET Name = ? WHERE Id = ?", (item.text(), id))
            self.con.commit()

    def add_row(self):
        # добавим в таблицу еще одну строку
        self.tblw_deps.setRowCount(self.tblw_deps.rowCount() + 1)

    def del_row(self):
        # Получаем список элементов без повторов и их id
        rows = list(set([i.row() for i in self.tblw_deps.selectedItems()]))
        ids = [self.tblw_deps.item(i, 0).text() for i in rows]
        if len(ids) == 0:
            return
        # Спрашиваем у пользователя подтверждение на удаление элементов
        valid = QMessageBox.question(
            self, '', "Действительно удалить выбранные отделы?",
            QMessageBox.Yes, QMessageBox.No)
        # Если пользователь ответил утвердительно, удаляем элементы.
        # Не забываем зафиксировать изменения
        if valid == QMessageBox.Yes:
            cur = self.con.cursor()
            cur.execute("DELETE FROM Departments WHERE id IN (" + ", ".join(
                '?' * len(ids)) + ")", ids)
            self.con.commit()
        # теперь удалим из таблицы строки
        # сначала отсортируй по убыванию
        rows.sort(reverse=True)
        for row in rows:
            self.tblw_deps.removeRow(row)

    # закрываем окно departs.ui
    def close_wnd(self):
        self.close()


def except_hook(cls, exception, traceback):
    sys.__excepthook__(cls, exception, traceback)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    form = ScheduleWnd()
    form.show()
    sys.excepthook = except_hook
    sys.exit(app.exec())