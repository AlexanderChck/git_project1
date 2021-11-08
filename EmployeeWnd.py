import sqlite3

from PyQt5 import uic
from PyQt5.QtCore import Qt, QDate
from PyQt5.QtWidgets import QDialog
from const import *


class EmployeeWnd(QDialog):
    def __init__(self, *args, emp_id=0):
        super().__init__()
        uic.loadUi("employer.ui", self)
        self.con = sqlite3.connect("schedule_db.sqlite")
        self.cur = self.con.cursor()
        self.headers = ['Id', 'Sname', 'Name', 'Patronymic', 'Post', 'INN', 'DepartmentId', 'BDate', 'Gender']
        self.cbx_gender.addItems(GENDER)
        self.emp_id = emp_id
        self.btn_result.accepted.connect(self.addedit)
        # проверяем, какое действие собирается совершить пользователь
        if emp_id == 0:
            self.setWindowTitle(ADDBTN_NAME)
            self.fill_cbx_dep()
        else:
            self.setWindowTitle(EDITBTN_DATE)
            self.full_form()

    # добавляем в cbx_dep
    def fill_cbx_dep(self, cur_dep_id=-1):
        result = self.cur.execute(FOUND_DEP_NAME).fetchall()
        if len(result) > 1:
            index = 0
            for row in result:
                self.cbx_dep.addItem(row[1], row[0])
                if row[0] == cur_dep_id:
                    self.cbx_dep.setCurrentIndex(index)

    def full_form(self):
        result = self.cur.execute(FULL_FORM, (self.emp_id, )).fetchall()
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
        if inn.isdigit() is False or len(inn) != LEN_INN:
            raise TypeError('Введённый ИНН не соответствует стандартам')
        # Константы позже будут переведены
        fst_num, scd_num = 0, 0
        for i in range(len(FST_NUM_LST)):
            fst_num += int(inn[i]) * FST_NUM_LST[i]
            scd_num += int(inn[i]) * SCD_NUM_LST[i]
        scd_num += int(inn[-2]) * SCD_NUM_LST[-1]
        fst_razr = str(fst_num % 11)[-1]
        scd_razr = str(scd_num % 11)[-1]
        if fst_razr != inn[-2] or scd_razr != inn[-1]:
            raise ValueError('Неправильный ИНН')

    def edit_emp(self, emp_id):
        self.cur.execute(EDIT_EMP, (self.values[0], self.values[1], self.values[2], self.values[3],
            self.values[4], self.values[5], self.values[6], self.values[7], emp_id, ))
        self.con.commit()

    def add_emp(self):
        try:
            self.cur.execute(ADD_EMP, (tuple(self.values,))).fetchall()
            self.con.commit()
        except Exception as e:
            print(f'error: {e}')
            return

    def addedit(self):
        try:
            self.check_inn()
        except Exception as e:
            print(f'ошибка {e}')
            return
        date = self.Bdate_inpt.date().toString(Qt.ISODate)
        # создаём список значений виджетов employer.ui
        self.values = [self.sname_inpt.text(), self.name_inpt.text(), self.patr_inpt.text(), self.post_inpt.text(),
                  self.inn_inpt.text(), int(self.cbx_dep.itemData(self.cbx_dep.currentIndex())), date, self.cbx_gender.currentIndex()]
        try:
            # проверяем, хочет ли пользователь редактировать данные о сотруднике
            if self.emp_id != 0:
                self.edit_emp(self.emp_id)
            else:
                self.add_emp()
        except Exception as e:
            print(e)