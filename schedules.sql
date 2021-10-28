--
-- Файл сгенерирован с помощью SQLiteStudio v3.3.3 в Чт окт 28 23:52:09 2021
--
-- Использованная кодировка текста: System
--
PRAGMA foreign_keys = off;
BEGIN TRANSACTION;

-- Таблица: Departments
CREATE TABLE Departments (Id INTEGER PRIMARY KEY AUTOINCREMENT UNIQUE NOT NULL, Name STRING NOT NULL);

-- Таблица: Employees
CREATE TABLE Employees (Id INTEGER PRIMARY KEY AUTOINCREMENT UNIQUE NOT NULL, INN STRING NOT NULL DEFAULT (''), Sname STRING NOT NULL, Name STRING NOT NULL, Patronymic STRING NOT NULL, Post STRING NOT NULL, DepartmentId INT REFERENCES Departments (Id) ON DELETE SET NULL ON UPDATE CASCADE, BDate DATE, Gender BOOLEAN NOT NULL DEFAULT (False));

-- Таблица: Schedules
CREATE TABLE Schedules (EmployeeId INT NOT NULL REFERENCES Employees (Id) ON DELETE CASCADE ON UPDATE CASCADE, Date DATE NOT NULL);

COMMIT TRANSACTION;
PRAGMA foreign_keys = on;
