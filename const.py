from PyQt5.QtGui import QColor

COUNT_MONTH = 12
MONTH = ['Январь', 'Февраль', 'Март', 'Апрель', 'Май', 'Июнь', 'Июль', 'Август', 'Сентябрь', 'Октябрь', 'Ноябрь', 'Декабрь']
ALL_DEPS = 'Все отделы'
FOUND_DEP_NAME = """SELECT Id, Name FROM Departments"""
YEAR_FORMAT = '%Y-%m-%d'
FOUND_DATE = """SELECT Date FROM Schedule WHERE EmployeeId = ? AND Date >= ? AND Date < ?"""
COUNT_HEADERS_WOUT_DAYS = 6
ADD_WEEKEND = "INSERT INTO Schedule VALUES (?, ?)"
DELETE_WEEKEND = "DELETE FROM Schedule WHERE EmployeeId = ? AND Date = ?"
RED = QColor(250, 128, 114)
GREEN = QColor(144, 238, 144)
BLUE = QColor(135, 206, 250)
GENDER = ['Мужской', 'Женский']
ADDBTN_NAME = 'Добавление сотрудника'
EDITBTN_DATE = 'Редактирование сотрудника'
FULL_FORM = """SELECT Sname, Name, Patronymic, Post, INN, DepartmentId, BDate, Gender FROM Employees WHERE Id = ?"""
EDIT_EMP = """Update Employees set Sname = ?, Name = ?, Patronymic = ?, Post = ?, INN = ?, DepartmentId = ?, 
            BDate = ?, Gender = ? WHERE Id = ?"""
ADD_EMP = """INSERT INTO Employees(Sname, Name, Patronymic, Post, INN, DepartmentId, BDate, Gender)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)"""
LEN_INN = 12
FST_NUM_LST = [7, 2, 4, 10, 3, 5, 9, 4, 6, 8]
SCD_NUM_LST = [3, 7, 2, 4, 10, 3, 5, 9, 4, 6, 8]
DEP_HEADERS = ['Id', 'Name']
SELECT_DEP_NAME = "SELECT Id, Name FROM Departments"
ADD_DEP = "INSERT INTO Departments (Name) VALUES (?)"
MESSEGE = "Действительно удалить выбранные отделы?"
