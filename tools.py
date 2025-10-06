from __future__ import annotations
from typing import Dict, Any
from pydantic import BaseModel, Field
from pathlib import Path
import sqlite3
import requests
from rank_bm25 import BM25Okapi


# ---- Tool Infrastructure ----
class ToolSpec(BaseModel):
    name: str
    description: str
    args_schema: type[BaseModel]


class Tool:
    def __init__(self, spec: ToolSpec, handler):
        self.spec = spec
        self.handler = handler

    def __call__(self, **kwargs):
        return self.handler(**kwargs)


# ---- RAG Tool (BM25-based) ----
class RAGArgs(BaseModel):
    query: str = Field(description="Search query")
    top_k: int = Field(default=3, description="Number of top results to return")


class SimpleRAG:
    def __init__(self, corpus_dir: str = "corpus"):
        texts = []
        for p in Path(corpus_dir).glob("**/*.md"):
            texts.append(p.read_text(encoding="utf-8"))
        self.docs = [t.split() for t in texts] if texts else [[]]
        self.raw_texts = texts
        self.bm25 = BM25Okapi(self.docs) if any(self.docs) else None

    def search(self, query: str, top_k: int = 3):
        if not self.bm25:
            return []
        scores = self.bm25.get_scores(query.split())
        idxs = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)[:top_k]
        return [self.raw_texts[i] for i in idxs]


def rag_tool_factory() -> Tool:
    rag = SimpleRAG()

    def handler(query: str, top_k: int = 3) -> Dict[str, Any]:
        hits = rag.search(query, top_k)
        return {"contexts": hits}

    spec = ToolSpec(
        name="rag_search",
        description="Search internal knowledge base using BM25 and return top contexts",
        args_schema=RAGArgs,
    )
    return Tool(spec, handler)


# ---- Weather API (Open-Meteo – không cần API key) ----
class WeatherArgs(BaseModel):
    city: str = Field(description="City name in Vietnam, e.g., 'Da Nang'")


def _geocode_city(city_name: str) -> tuple[float, float] | None:
    """Get coordinates for a city using Open-Meteo geocoding API"""
    try:
        # Use Open-Meteo geocoding API (free, no API key needed)
        geocode_url = "https://geocoding-api.open-meteo.com/v1/search"
        params = {
            "name": city_name,
            "count": 1,
            "language": "vi",
            "format": "json"
        }
        
        resp = requests.get(geocode_url, params=params, timeout=10)
        data = resp.json()
        
        if data.get("results") and len(data["results"]) > 0:
            result = data["results"][0]
            return (result["latitude"], result["longitude"])
        
        return None
    except Exception as e:
        print(f"Geocoding error for {city_name}: {e}")
        return None


def weather_tool_factory(base_url: str) -> Tool:
    def handler(city: str) -> Dict[str, Any]:
        # Get coordinates dynamically
        coords = _geocode_city(city)
        if not coords:
            return {"error": f"Không tìm thấy tọa độ cho thành phố: {city}"}
        
        lat, lon = coords
        
        try:
            resp = requests.get(
                base_url,
                params={
                    "latitude": lat, 
                    "longitude": lon, 
                    "hourly": "temperature_2m,relative_humidity_2m,weather_code",
                    "current": "temperature_2m,relative_humidity_2m,weather_code",
                    "timezone": "auto"
                },
                timeout=15,
            )
            resp.raise_for_status()
            data = resp.json()
            
            # Format response better
            current = data.get("current", {})
            hourly = data.get("hourly", {})
            
            return {
                "city": city,
                "current": {
                    "temperature": current.get("temperature_2m"),
                    "humidity": current.get("relative_humidity_2m"),
                    "weather_code": current.get("weather_code")
                },
                "hourly": {
                    "times": hourly.get("time", [])[:24],  # Next 24 hours
                    "temperatures": hourly.get("temperature_2m", [])[:24],
                    "humidity": hourly.get("relative_humidity_2m", [])[:24],
                    "weather_codes": hourly.get("weather_code", [])[:24]
                }
            }
        except requests.exceptions.RequestException as e:
            return {"error": f"Lỗi kết nối API thời tiết: {str(e)}"}
        except Exception as e:
            return {"error": f"Lỗi xử lý dữ liệu: {str(e)}"}

    spec = ToolSpec(
        name="get_weather",
        description="Get current weather and hourly forecast for any city in Vietnam using geocoding",
        args_schema=WeatherArgs,
    )
    return Tool(spec, handler)


# ---- SQLite DB (đọc tổng số khách hàng) ----
class DBArgs(BaseModel):
    sql: str = Field(description="Read‑only SELECT statement")


def db_tool_factory(db_path: str = "data.db") -> Tool:
    def handler(sql: str) -> Dict[str, Any]:
        # Create new connection for each request to avoid threading issues
        conn = sqlite3.connect(db_path, check_same_thread=False)
        try:
            cur = conn.cursor()
            
            # bootstrap sample table
            cur.execute("CREATE TABLE IF NOT EXISTS customers (id INTEGER PRIMARY KEY, name TEXT)")
            # seed nếu trống
            cur.execute("SELECT COUNT(1) FROM customers")
            if cur.fetchone()[0] == 0:
                cur.executemany("INSERT INTO customers(name) VALUES (?)", [(f"Customer {i}",) for i in range(1, 51)])
                conn.commit()
            
            if "delete" in sql.lower() or "update" in sql.lower() or "insert" in sql.lower():
                return {"error": "Write operations are not allowed"}
            
            rows = cur.execute(sql).fetchall()
            cols = [d[0] for d in cur.execute(sql).description]
            return {"columns": cols, "rows": rows}
        finally:
            conn.close()

    spec = ToolSpec(
        name="query_db",
        description="Run read‑only SQL on the local SQLite database",
        args_schema=DBArgs,
    )
    return Tool(spec, handler)


# ---- Employee Management ----
class AddEmployeeArgs(BaseModel):
    name: str = Field(description="Employee name")
    birth_year: int = Field(description="Employee birth year")


def employee_tool_factory(db_path: str = "data.db") -> Tool:
    def handler(name: str, birth_year: int) -> Dict[str, Any]:
        # Create new connection for each request to avoid threading issues
        conn = sqlite3.connect(db_path, check_same_thread=False)
        try:
            cur = conn.cursor()
            
            # Create table if not exists
            cur.execute("""
                CREATE TABLE IF NOT EXISTS employees (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    birth_year INTEGER NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            conn.commit()
            
            # Insert employee
            cur.execute("""
                INSERT INTO employees (name, birth_year)
                VALUES (?, ?)
            """, (name, birth_year))
            conn.commit()
            
            # Get the inserted employee
            employee_id = cur.lastrowid
            cur.execute("SELECT * FROM employees WHERE id = ?", (employee_id,))
            employee = cur.fetchone()
            
            return {
                "success": True,
                "message": f"Đã thêm nhân viên {name} thành công!",
                "employee": {
                    "id": employee[0],
                    "name": employee[1],
                    "birth_year": employee[2],
                    "created_at": employee[3]
                }
            }
        except Exception as e:
            return {"error": f"Lỗi thêm nhân viên: {str(e)}"}
        finally:
            conn.close()

    spec = ToolSpec(
        name="add_employee",
        description="Add a new employee with name and birth year to the database",
        args_schema=AddEmployeeArgs,
    )
    return Tool(spec, handler)


# ---- List All Employees ----
class ListEmployeesArgs(BaseModel):
    limit: int = Field(default=100, description="Maximum number of employees to return")


def list_employees_tool_factory(db_path: str = "data.db") -> Tool:
    def handler(limit: int = 100) -> Dict[str, Any]:
        # Create new connection for each request to avoid threading issues
        conn = sqlite3.connect(db_path, check_same_thread=False)
        try:
            cur = conn.cursor()
            
            # Get total count
            cur.execute("SELECT COUNT(*) FROM employees")
            total_count = cur.fetchone()[0]
            
            # Get employees with limit
            cur.execute("""
                SELECT id, name, birth_year, created_at 
                FROM employees 
                ORDER BY created_at DESC 
                LIMIT ?
            """, (limit,))
            employees = cur.fetchall()
            
            return {
                "success": True,
                "total_count": total_count,
                "returned_count": len(employees),
                "employees": [
                    {
                        "id": emp[0],
                        "name": emp[1],
                        "birth_year": emp[2],
                        "created_at": emp[3]
                    }
                    for emp in employees
                ]
            }
        except Exception as e:
            return {"error": f"Lỗi lấy danh sách nhân viên: {str(e)}"}
        finally:
            conn.close()

    spec = ToolSpec(
        name="list_employees",
        description="Get list of all employees from the database",
        args_schema=ListEmployeesArgs,
    )
    return Tool(spec, handler)


# ---- Delete Employee ----
class DeleteEmployeeArgs(BaseModel):
    employee_id: int = Field(description="ID of the employee to delete")


def delete_employee_tool_factory(db_path: str = "data.db") -> Tool:
    def handler(employee_id: int) -> Dict[str, Any]:
        # Create new connection for each request to avoid threading issues
        conn = sqlite3.connect(db_path, check_same_thread=False)
        try:
            cur = conn.cursor()
            
            # First check if employee exists
            cur.execute("SELECT id, name, birth_year FROM employees WHERE id = ?", (employee_id,))
            employee = cur.fetchone()
            
            if not employee:
                return {"error": f"Không tìm thấy nhân viên với ID {employee_id}"}
            
            # Delete the employee
            cur.execute("DELETE FROM employees WHERE id = ?", (employee_id,))
            conn.commit()
            
            return {
                "success": True,
                "message": f"Đã xóa nhân viên {employee[1]} (ID: {employee[0]}) thành công!",
                "deleted_employee": {
                    "id": employee[0],
                    "name": employee[1],
                    "birth_year": employee[2]
                }
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


# ---- Update Employee ----
class UpdateEmployeeArgs(BaseModel):
    employee_id: int = Field(description="ID of the employee to update")
    name: str = Field(description="New name for the employee")
    birth_year: int = Field(description="New birth year for the employee")


def update_employee_tool_factory(db_path: str = "data.db") -> Tool:
    def handler(employee_id: int, name: str, birth_year: int) -> Dict[str, Any]:
        # Create new connection for each request to avoid threading issues
        conn = sqlite3.connect(db_path, check_same_thread=False)
        try:
            cur = conn.cursor()
            
            # First check if employee exists
            cur.execute("SELECT id, name, birth_year FROM employees WHERE id = ?", (employee_id,))
            old_employee = cur.fetchone()
            
            if not old_employee:
                return {"error": f"Không tìm thấy nhân viên với ID {employee_id}"}
            
            # Update the employee
            cur.execute("""
                UPDATE employees 
                SET name = ?, birth_year = ? 
                WHERE id = ?
            """, (name, birth_year, employee_id))
            conn.commit()
            
            # Get updated employee
            cur.execute("SELECT id, name, birth_year, created_at FROM employees WHERE id = ?", (employee_id,))
            updated_employee = cur.fetchone()
            
            return {
                "success": True,
                "message": f"Đã cập nhật nhân viên thành công!",
                "old_employee": {
                    "id": old_employee[0],
                    "name": old_employee[1],
                    "birth_year": old_employee[2]
                },
                "updated_employee": {
                    "id": updated_employee[0],
                    "name": updated_employee[1],
                    "birth_year": updated_employee[2],
                    "created_at": updated_employee[3]
                }
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


# ---- Find Employee by Name ----
class FindEmployeeArgs(BaseModel):
    name: str = Field(description="Employee name to search for")


def find_employee_tool_factory(db_path: str = "data.db") -> Tool:
    def handler(name: str) -> Dict[str, Any]:
        # Create new connection for each request to avoid threading issues
        conn = sqlite3.connect(db_path, check_same_thread=False)
        try:
            cur = conn.cursor()
            
            # Search for employees by name (case insensitive, partial match)
            cur.execute("""
                SELECT id, name, birth_year, created_at 
                FROM employees 
                WHERE LOWER(name) LIKE LOWER(?) 
                ORDER BY created_at DESC
            """, (f"%{name}%",))
            employees = cur.fetchall()
            
            if employees:
                return {
                    "success": True,
                    "found_count": len(employees),
                    "employees": [
                        {
                            "id": emp[0],
                            "name": emp[1],
                            "birth_year": emp[2],
                            "created_at": emp[3]
                        }
                        for emp in employees
                    ]
                }
            else:
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


# ---- Delete Employee by Name ----
class DeleteEmployeeByNameArgs(BaseModel):
    name: str = Field(description="Employee name to delete")


def delete_employee_by_name_tool_factory(db_path: str = "data.db") -> Tool:
    def handler(name: str) -> Dict[str, Any]:
        # Create new connection for each request to avoid threading issues
        conn = sqlite3.connect(db_path, check_same_thread=False)
        try:
            cur = conn.cursor()
            
            # First find employees by name
            cur.execute("""
                SELECT id, name, birth_year 
                FROM employees 
                WHERE LOWER(name) LIKE LOWER(?)
            """, (f"%{name}%",))
            employees = cur.fetchall()
            
            if not employees:
                return {"error": f"Không tìm thấy nhân viên nào có tên chứa '{name}'"}
            
            if len(employees) > 1:
                return {"error": f"Tìm thấy {len(employees)} nhân viên có tên chứa '{name}'. Vui lòng chỉ định rõ hơn."}
            
            # Delete the employee
            employee = employees[0]
            cur.execute("DELETE FROM employees WHERE id = ?", (employee[0],))
            conn.commit()
            
            return {
                "success": True,
                "message": f"Đã xóa nhân viên {employee[1]} (ID: {employee[0]}) thành công!",
                "deleted_employee": {
                    "id": employee[0],
                    "name": employee[1],
                    "birth_year": employee[2]
                }
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


# ---- Update Employee by Name ----
class UpdateEmployeeByNameArgs(BaseModel):
    name: str = Field(description="Employee name to update")
    new_name: str = Field(description="New name for the employee")
    new_birth_year: int = Field(description="New birth year for the employee")


def update_employee_by_name_tool_factory(db_path: str = "data.db") -> Tool:
    def handler(name: str, new_name: str, new_birth_year: int) -> Dict[str, Any]:
        # Create new connection for each request to avoid threading issues
        conn = sqlite3.connect(db_path, check_same_thread=False)
        try:
            cur = conn.cursor()
            
            # First find employee by name
            cur.execute("""
                SELECT id, name, birth_year 
                FROM employees 
                WHERE LOWER(name) LIKE LOWER(?)
            """, (f"%{name}%",))
            employees = cur.fetchall()
            
            if not employees:
                return {"error": f"Không tìm thấy nhân viên nào có tên chứa '{name}'"}
            
            if len(employees) > 1:
                return {"error": f"Tìm thấy {len(employees)} nhân viên có tên chứa '{name}'. Vui lòng chỉ định rõ hơn."}
            
            # Update the employee
            old_employee = employees[0]
            cur.execute("""
                UPDATE employees 
                SET name = ?, birth_year = ? 
                WHERE id = ?
            """, (new_name, new_birth_year, old_employee[0]))
            conn.commit()
            
            # Get updated employee
            cur.execute("SELECT id, name, birth_year, created_at FROM employees WHERE id = ?", (old_employee[0],))
            updated_employee = cur.fetchone()
            
            return {
                "success": True,
                "message": f"Đã cập nhật nhân viên thành công!",
                "old_employee": {
                    "id": old_employee[0],
                    "name": old_employee[1],
                    "birth_year": old_employee[2]
                },
                "updated_employee": {
                    "id": updated_employee[0],
                    "name": updated_employee[1],
                    "birth_year": updated_employee[2],
                    "created_at": updated_employee[3]
                }
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
