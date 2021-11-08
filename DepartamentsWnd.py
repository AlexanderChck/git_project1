import sqlite3

from PyQt5 import uic
from PyQt5.QtWidgets import QTableWidgetItem, QWidget, QMessageBox
from const import *


class DepartamentsWnd(QWidget):
    def __init__(self, *args):
        super().__init__()
        self.ignore_change = False
        uic.loadUi("dist/departs.ui", self)
        self.tblw_deps.itemChanged.connect(self.change_table)
        self.btn_add.clicked.connect(self.add_row)
        self.btn_del.clicked.connect(self.del_row)
        self.btn_close.clicked.connect(self.close_wnd)
        self.con = sqlite3.connect("dist/schedule_db.sqlite")
        self.fill_table()

    def fill_table(self):
        self.ignore_change = True
        # заполним заголовки в таблице
        # заголовок с Id мы скроем, пользователю не нужно его показывать
        # а нам он нужен, мы ез него будем вытаскивать Id записи для изменения и удаления в базе
        self.tblw_deps.setColumnCount(len(DEP_HEADERS))
        self.tblw_deps.setHorizontalHeaderLabels(DEP_HEADERS)
        # скроем первый столбец
        self.tblw_deps.hideColumn(0)

        cur = self.con.cursor()
        result = cur.execute(SELECT_DEP_NAME).fetchall()

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
        if self.ignore_change is True:
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
            cur.execute(ADD_WEEKEND, (item.text(),))
            self.con.commit()
            # получим id добавленной записи
            id = cur.lastrowid
            # запишем id в таблицу
            self.tblw_deps.setItem(item.row(), 0, QTableWidgetItem(str(id)))
        # если Id не пустой, нужно отредактировать значение в базе
        else:
            id = int(id)
            cur.execute(SET_NEW_NAME, (item.text(), id))
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
            self, '', MESSEGE,
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