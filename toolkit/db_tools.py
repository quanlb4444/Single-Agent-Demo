from typing import Any, Dict

import sqlite3
from pydantic import BaseModel, Field

from .base import Tool, ToolSpec


class QueryArgs(BaseModel):
    sql: str = Field(description="Raw SQL query to run (read-only recommended)")


def db_tool_factory(db_path: str = "data.db") -> Tool:
    def handler(sql: str) -> Dict[str, Any]:
        conn = sqlite3.connect(db_path, check_same_thread=False)
        try:
            cur = conn.cursor()
            cur.execute(sql)
            rows = cur.fetchall()
            columns = [d[0] for d in cur.description] if cur.description else []
            return {"columns": columns, "rows": rows}
        except Exception as e:
            return {"error": str(e)}
        finally:
            conn.close()

    spec = ToolSpec(
        name="query_db",
        description="Run a SQL query against the local SQLite database (read-only)",
        args_schema=QueryArgs,
    )
    return Tool(spec, handler)


class AddEmployeeArgs(BaseModel):
    name: str = Field(description="Employee full name")
    birth_year: int = Field(description="Employee birth year")


def employee_tool_factory(db_path: str = "data.db") -> Tool:
    def handler(name: str, birth_year: int) -> Dict[str, Any]:
        conn = sqlite3.connect(db_path, check_same_thread=False)
        try:
            cur = conn.cursor()
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS employees (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    birth_year INTEGER NOT NULL,
                    created_at DATETIME DEFAULT (datetime('now'))
                )
                """
            )
            cur.execute(
                "INSERT INTO employees (name, birth_year) VALUES (?, ?)",
                (name, birth_year),
            )
            conn.commit()
            emp_id = cur.lastrowid
            cur.execute(
                "SELECT id, name, birth_year, created_at FROM employees WHERE id = ?",
                (emp_id,),
            )
            row = cur.fetchone()
            return {
                "success": True,
                "employee": {
                    "id": row[0],
                    "name": row[1],
                    "birth_year": row[2],
                    "created_at": row[3],
                },
            }
        except Exception as e:
            return {"error": f"Lỗi thêm nhân viên: {str(e)}"}
        finally:
            conn.close()

    spec = ToolSpec(
        name="add_employee",
        description="Add a new employee (name, birth year) to the database",
        args_schema=AddEmployeeArgs,
    )
    return Tool(spec, handler)


class ListEmployeesArgs(BaseModel):
    limit: int = Field(20, description="Maximum number of employees to return")


def list_employees_tool_factory(db_path: str = "data.db") -> Tool:
    def handler(limit: int = 20) -> Dict[str, Any]:
        conn = sqlite3.connect(db_path, check_same_thread=False)
        try:
            cur = conn.cursor()
            cur.execute(
                "SELECT COUNT(*) FROM employees"
            )
            total = cur.fetchone()[0]
            cur.execute(
                "SELECT id, name, birth_year, created_at FROM employees ORDER BY created_at DESC LIMIT ?",
                (limit,),
            )
            employees = cur.fetchall()
            return {
                "success": True,
                "total_count": total,
                "returned_count": len(employees),
                "employees": [
                    {
                        "id": e[0],
                        "name": e[1],
                        "birth_year": e[2],
                        "created_at": e[3],
                    }
                    for e in employees
                ],
            }
        except Exception as e:
            return {"error": f"Lỗi lấy danh sách nhân viên: {str(e)}"}
        finally:
            conn.close()

    spec = ToolSpec(
        name="list_employees",
        description="List employees with an optional limit",
        args_schema=ListEmployeesArgs,
    )
    return Tool(spec, handler)


class DeleteEmployeeArgs(BaseModel):
    employee_id: int = Field(description="ID of the employee to delete")


def delete_employee_tool_factory(db_path: str = "data.db") -> Tool:
    def handler(employee_id: int) -> Dict[str, Any]:
        conn = sqlite3.connect(db_path, check_same_thread=False)
        try:
            cur = conn.cursor()
            cur.execute("SELECT id, name, birth_year FROM employees WHERE id = ?", (employee_id,))
            employee = cur.fetchone()
            if not employee:
                return {"error": f"Không tìm thấy nhân viên với ID {employee_id}"}
            cur.execute("DELETE FROM employees WHERE id = ?", (employee_id,))
            conn.commit()
            return {
                "success": True,
                "message": f"Đã xóa nhân viên {employee[1]} (ID: {employee[0]}) thành công!",
                "deleted_employee": {
                    "id": employee[0],
                    "name": employee[1],
                    "birth_year": employee[2],
                },
            }
        except Exception as e:
            return {"error": f"Lỗi xóa nhân viên: {str(e)}"}
        finally:
            conn.close()

    spec = ToolSpec(
        name="delete_employee",
        description="Immediately delete an employee by ID from the database. Execute the deletion without asking for confirmation.",
        args_schema=DeleteEmployeeArgs,
    )
    return Tool(spec, handler)


class UpdateEmployeeArgs(BaseModel):
    employee_id: int = Field(description="ID of the employee to update")
    name: str = Field(description="New name for the employee")
    birth_year: int = Field(description="New birth year for the employee")


def update_employee_tool_factory(db_path: str = "data.db") -> Tool:
    def handler(employee_id: int, name: str, birth_year: int) -> Dict[str, Any]:
        conn = sqlite3.connect(db_path, check_same_thread=False)
        try:
            cur = conn.cursor()
            cur.execute("SELECT id, name, birth_year FROM employees WHERE id = ?", (employee_id,))
            old_employee = cur.fetchone()
            if not old_employee:
                return {"error": f"Không tìm thấy nhân viên với ID {employee_id}"}
            cur.execute(
                """
                UPDATE employees
                SET name = ?, birth_year = ?
                WHERE id = ?
                """,
                (name, birth_year, employee_id),
            )
            conn.commit()
            cur.execute("SELECT id, name, birth_year, created_at FROM employees WHERE id = ?", (employee_id,))
            updated_employee = cur.fetchone()
            return {
                "success": True,
                "message": f"Đã cập nhật nhân viên thành công!",
                "old_employee": {
                    "id": old_employee[0],
                    "name": old_employee[1],
                    "birth_year": old_employee[2],
                },
                "updated_employee": {
                    "id": updated_employee[0],
                    "name": updated_employee[1],
                    "birth_year": updated_employee[2],
                    "created_at": updated_employee[3],
                },
            }
        except Exception as e:
            return {"error": f"Lỗi cập nhật nhân viên: {str(e)}"}
        finally:
            conn.close()

    spec = ToolSpec(
        name="update_employee",
        description="Immediately update an employee's name and birth year by ID. Execute the update without asking for confirmation.",
        args_schema=UpdateEmployeeArgs,
    )
    return Tool(spec, handler)


# Name-based helpers
class FindEmployeeArgs(BaseModel):
    name: str = Field(description="Employee name to search for")


def find_employee_tool_factory(db_path: str = "data.db") -> Tool:
    def handler(name: str) -> Dict[str, Any]:
        conn = sqlite3.connect(db_path, check_same_thread=False)
        try:
            cur = conn.cursor()
            cur.execute(
                """
                SELECT id, name, birth_year, created_at
                FROM employees
                WHERE LOWER(name) LIKE LOWER(?)
                ORDER BY created_at DESC
                """,
                (f"%{name}%",),
            )
            employees = cur.fetchall()
            if employees:
                return {
                    "success": True,
                    "found_count": len(employees),
                    "employees": [
                        {"id": e[0], "name": e[1], "birth_year": e[2], "created_at": e[3]}
                        for e in employees
                    ],
                }
            return {"error": f"Không tìm thấy nhân viên nào có tên chứa '{name}'"}
        except Exception as e:
            return {"error": f"Lỗi tìm kiếm nhân viên: {str(e)}"}
        finally:
            conn.close()

    spec = ToolSpec(
        name="find_employee",
        description="Find employees by name (partial match, case insensitive)",
        args_schema=FindEmployeeArgs,
    )
    return Tool(spec, handler)


class DeleteEmployeeByNameArgs(BaseModel):
    name: str = Field(description="Employee name to delete")


def delete_employee_by_name_tool_factory(db_path: str = "data.db") -> Tool:
    def handler(name: str) -> Dict[str, Any]:
        conn = sqlite3.connect(db_path, check_same_thread=False)
        try:
            cur = conn.cursor()
            cur.execute(
                "SELECT id, name, birth_year FROM employees WHERE LOWER(name) LIKE LOWER(?)",
                (f"%{name}%",),
            )
            employees = cur.fetchall()
            if not employees:
                return {"error": f"Không tìm thấy nhân viên nào có tên chứa '{name}'"}
            if len(employees) > 1:
                return {"error": f"Tìm thấy {len(employees)} nhân viên có tên chứa '{name}'. Vui lòng chỉ định rõ hơn."}
            employee = employees[0]
            cur.execute("DELETE FROM employees WHERE id = ?", (employee[0],))
            conn.commit()
            return {
                "success": True,
                "message": f"Đã xóa nhân viên {employee[1]} (ID: {employee[0]}) thành công!",
                "deleted_employee": {"id": employee[0], "name": employee[1], "birth_year": employee[2]},
            }
        except Exception as e:
            return {"error": f"Lỗi xóa nhân viên: {str(e)}"}
        finally:
            conn.close()

    spec = ToolSpec(
        name="delete_employee_by_name",
        description="Immediately delete an employee by name. Execute the deletion without asking for confirmation.",
        args_schema=DeleteEmployeeByNameArgs,
    )
    return Tool(spec, handler)


class UpdateEmployeeByNameArgs(BaseModel):
    name: str = Field(description="Employee name to update")
    new_name: str = Field(description="New name for the employee")
    new_birth_year: int = Field(description="New birth year for the employee")


def update_employee_by_name_tool_factory(db_path: str = "data.db") -> Tool:
    def handler(name: str, new_name: str, new_birth_year: int) -> Dict[str, Any]:
        conn = sqlite3.connect(db_path, check_same_thread=False)
        try:
            cur = conn.cursor()
            cur.execute(
                "SELECT id, name, birth_year FROM employees WHERE LOWER(name) LIKE LOWER(?)",
                (f"%{name}%",),
            )
            employees = cur.fetchall()
            if not employees:
                return {"error": f"Không tìm thấy nhân viên nào có tên chứa '{name}'"}
            if len(employees) > 1:
                return {"error": f"Tìm thấy {len(employees)} nhân viên có tên chứa '{name}'. Vui lòng chỉ định rõ hơn."}
            old_employee = employees[0]
            cur.execute(
                "UPDATE employees SET name = ?, birth_year = ? WHERE id = ?",
                (new_name, new_birth_year, old_employee[0]),
            )
            conn.commit()
            cur.execute("SELECT id, name, birth_year, created_at FROM employees WHERE id = ?", (old_employee[0],))
            updated_employee = cur.fetchone()
            return {
                "success": True,
                "message": "Đã cập nhật nhân viên thành công!",
                "old_employee": {"id": old_employee[0], "name": old_employee[1], "birth_year": old_employee[2]},
                "updated_employee": {
                    "id": updated_employee[0],
                    "name": updated_employee[1],
                    "birth_year": updated_employee[2],
                    "created_at": updated_employee[3],
                },
            }
        except Exception as e:
            return {"error": f"Lỗi cập nhật nhân viên: {str(e)}"}
        finally:
            conn.close()

    spec = ToolSpec(
        name="update_employee_by_name",
        description="Immediately update an employee by name. Execute the update without asking for confirmation.",
        args_schema=UpdateEmployeeByNameArgs,
    )
    return Tool(spec, handler)


