import sqlite3
import sys
import datetime as dt

from PyQt5 import uic
from PyQt5.QtWidgets import QApplication
from PyQt5.QtWidgets import QMainWindow, QTableWidgetItem, QWidget, QMessageBox
from PyQt5.QtGui import QColor


class ScheduleWnd(QMainWindow):
    def __init__(self):
        super().__init__()
        uic.loadUi("main.ui", self)
        self.full_clndr()
        self.tblw_schedule.itemClicked.connect(self.change_schedule)
        self.db_con = sqlite3.connect("schedule_db.sqlite")
        self.fill_schedule()
        self.btn_editemp.clicked.connect(self.edit_emp_wnd)
        self.btn_addemp.clicked.connect(self.add_emp_wnd)
        self.btn_chngdeps.clicked.connect(self.chng_dep_wnd)

    def full_clndr(self):
        cur_year = dt.datetime.now().year
        cur_month = dt.datetime.now().month
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

    def fill_schedule(self):
        # создаём заглавия для таблицы
        headers = ['Должность', 'Фамилия', 'Имя', 'Отчество']
        for i in range(1, 32):
            headers.append(str(i))
        self.tblw_schedule.setColumnCount(len(headers))
        self.tblw_schedule.setHorizontalHeaderLabels(headers)

        cur = self.db_con.cursor()
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
        # print используется как подсказка, в итоговом коде его не будет
        # print('row: ' + str(item.row()) + ' col: ' + str(item.column()))

        # проверяем, не выбран ли день отпуска
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
        self.con = sqlite3.connect("schedule_db.sqlite")
        self.cur = self.con.cursor()
        self.headers = ['Id', 'Sname', 'Name', 'Patronymic', 'Post', 'INN', 'DepartmentId', 'BDate', 'Gender']
        self.cbx_gender.addItems(['М', 'Ж'])
        self.emp_id = emp_id
        self.fill_cbx_dep()
        # проверяем, какое действие собирается совершить пользователь
        if emp_id == 0:
            self.setWindowTitle('Добавление сотрудника')
            self.btn_addedit.setText('Добавить')
        else:
            self.setWindowTitle('Редактирование сотрудника')
            self.btn_addedit.setText('Изменить')
            self.edit_emp(emp_id)

        self.btn_addedit.clicked.connect(self.addedit)
        self.btn_close.clicked.connect(self.close_wnd)

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

    # проверяем, правильно ли введён ИНН
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
        self.values.insert(0, emp_id)
        for i in range(len(self.headers)):
            self.cur.execute("""UPDATE Employee WHERE Id = ? Set ? = ?""", (emp_id, self.headers[i], self.values[i]))
        self.con.commit()

    def add_emp(self):
        try:
            # в values добавляем индекс добав. сотрудника
            self.values.insert(0, id)
            self.cur.execute("INSERT INTO Employees VALUES (?, ?, ?, ?, ?, ?, ?, ?)", (tuple(self.values,))).fetchall()
            self.con.commit()
        except Exception as e:
            print(f'error: {e}')
            return

    def addedit(self):
        #self.check_inn()
        date = self.Bdate_inpt.date().toString()
        # создаём список значений виджетов employer.ui
        self.values = [self.sname_inpt.text(), self.name_inpt.text(), self.patr_inpt.text(), self.post_inpt.text(),
                  self.inn_inpt.text(), self.cbx_dep.currentText(), date, self.cbx_gender.currentText()]
        try:
            # проверяем, хочет ли пользователь редактировать данные о сотруднике
            if self.emp_id != 0:
                self.edit_emp(self.emp_id)
            else:
                self.add_emp()
        except Exception as e:
            self.error_lbl.setText(f'Произошла ошибка: {e}')

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
        # item - ячейка, которая была изменена
        # item.row() - номер строки
        # item.column() - номер столбца

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
        # код взял из второго урока по SQL и немного изменил
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