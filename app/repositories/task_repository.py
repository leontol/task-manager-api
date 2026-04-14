from typing import List, Optional, Dict, Any
from uuid import uuid4
from datetime import datetime
from app.models.schemas import TaskCreate, TaskUpdate, TaskStatusEnum, TaskPriorityEnum

class TaskRepository:
    _tasks_db = {}
    
    @classmethod
    def clear(cls):
        cls._tasks_db = {}
    
    def __init__(self, connection=None):
        self.conn = connection
        self.use_db = connection is not None
    
    async def create(self, task_data: TaskCreate) -> Dict[str, Any]:
        task_id = str(uuid4())
        now = datetime.now()
        completed_at = now if task_data.status == TaskStatusEnum.COMPLETED else None
        
        if self.use_db and self.conn:
            cur = self.conn.cursor()
            cur.execute("""
                INSERT INTO tasks (id, title, description, status, priority, created_at, updated_at, completed_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """, (task_id, task_data.title, task_data.description, task_data.status.value, 
                  task_data.priority.value, now, now, completed_at))
            self.conn.commit()
            cur.close()
            return await self.get(task_id)
        else:
            task = {
                "id": task_id, "title": task_data.title, "description": task_data.description,
                "status": task_data.status.value, "priority": task_data.priority.value,
                "created_at": now, "updated_at": now, "completed_at": completed_at
            }
            self._tasks_db[task_id] = task
            return task
    
    async def get(self, task_id: str) -> Optional[Dict[str, Any]]:
        if self.use_db and self.conn:
            cur = self.conn.cursor()
            cur.execute("SELECT * FROM tasks WHERE id = %s", (task_id,))
            row = cur.fetchone()
            cur.close()
            if row:
                return {
                    "id": row[0], "title": row[1], "description": row[2],
                    "status": row[3], "priority": row[4], "created_at": row[5],
                    "updated_at": row[6], "completed_at": row[7]
                }
            return None
        return self._tasks_db.get(task_id)
    
    async def get_filtered(self, status: Optional[TaskStatusEnum] = None,
                           priority: Optional[TaskPriorityEnum] = None,
                           skip: int = 0, limit: int = 10) -> tuple[List[Dict[str, Any]], int]:
        if self.use_db and self.conn:
            conditions = []
            params = []
            if status:
                conditions.append("status = %s")
                params.append(status.value)
            if priority:
                conditions.append("priority = %s")
                params.append(priority.value)
            
            where_clause = " AND ".join(conditions) if conditions else "1=1"
            
            cur = self.conn.cursor()
            cur.execute(f"SELECT COUNT(*) FROM tasks WHERE {where_clause}", params)
            total = cur.fetchone()[0]
            
            cur.execute(f"""
                SELECT * FROM tasks WHERE {where_clause}
                ORDER BY created_at DESC LIMIT %s OFFSET %s
            """, params + [limit, skip])
            
            rows = cur.fetchall()
            cur.close()
            
            tasks = [{
                "id": r[0], "title": r[1], "description": r[2],
                "status": r[3], "priority": r[4], "created_at": r[5],
                "updated_at": r[6], "completed_at": r[7]
            } for r in rows]
            return tasks, total
        else:
            tasks = list(self._tasks_db.values())
            if status:
                tasks = [t for t in tasks if t["status"] == status.value]
            if priority:
                tasks = [t for t in tasks if t["priority"] == priority.value]
            tasks.sort(key=lambda x: x["created_at"], reverse=True)
            total = len(tasks)
            return tasks[skip:skip+limit], total
    
    async def get_stats_by_status(self) -> Dict[str, int]:
        if self.use_db and self.conn:
            cur = self.conn.cursor()
            cur.execute("SELECT status, COUNT(*) FROM tasks GROUP BY status")
            rows = cur.fetchall()
            cur.close()
            return {row[0]: row[1] for row in rows}
        else:
            stats = {}
            for task in self._tasks_db.values():
                status = task["status"]
                stats[status] = stats.get(status, 0) + 1
            return stats
    
    async def update(self, task_id: str, task_data: TaskUpdate) -> Dict[str, Any]:
        if self.use_db and self.conn:
            current = await self.get(task_id)
            if not current:
                raise ValueError("Задача не найдена")
            
            updates = []
            params = []
            if task_data.title is not None:
                updates.append("title = %s")
                params.append(task_data.title)
            if task_data.description is not None:
                updates.append("description = %s")
                params.append(task_data.description)
            if task_data.status is not None:
                updates.append("status = %s")
                params.append(task_data.status.value)
                if task_data.status == TaskStatusEnum.COMPLETED and not current.get("completed_at"):
                    updates.append("completed_at = %s")
                    params.append(datetime.now())
                elif task_data.status != TaskStatusEnum.COMPLETED:
                    updates.append("completed_at = NULL")
            if task_data.priority is not None:
                updates.append("priority = %s")
                params.append(task_data.priority.value)
            
            updates.append("updated_at = %s")
            params.append(datetime.now())
            params.append(task_id)
            
            cur = self.conn.cursor()
            cur.execute(f"UPDATE tasks SET {', '.join(updates)} WHERE id = %s", params)
            self.conn.commit()
            cur.close()
            return await self.get(task_id)
        else:
            task = self._tasks_db.get(task_id)
            if not task:
                raise ValueError("Задача не найдена")
            now = datetime.now()
            if task_data.title is not None:
                task["title"] = task_data.title
            if task_data.description is not None:
                task["description"] = task_data.description
            if task_data.status is not None:
                task["status"] = task_data.status.value
                if task_data.status == TaskStatusEnum.COMPLETED and not task.get("completed_at"):
                    task["completed_at"] = now
                elif task_data.status != TaskStatusEnum.COMPLETED:
                    task["completed_at"] = None
            if task_data.priority is not None:
                task["priority"] = task_data.priority.value
            task["updated_at"] = now
            return task
    
    async def delete(self, task_id: str) -> bool:
        if self.use_db and self.conn:
            cur = self.conn.cursor()
            cur.execute("DELETE FROM tasks WHERE id = %s", (task_id,))
            deleted = cur.rowcount > 0
            self.conn.commit()
            cur.close()
            return deleted
        if task_id in self._tasks_db:
            del self._tasks_db[task_id]
            return True
        return False