def test_get_task_by_id(client, api_key_headers):
    """Тест получения задачи по ID"""
    # Создаём задачу
    create_response = client.post(
        "/api/v1/tasks",
        json={"title": "Get By ID", "description": "test", "status": "pending", "priority": "medium"},
        headers=api_key_headers
    )
    assert create_response.status_code == 201
    task_id = create_response.json()["id"]
    
    # Получаем по ID
    response = client.get(
        f"/api/v1/tasks/{task_id}",
        headers=api_key_headers
    )
    
    assert response.status_code == 200
    assert response.json()["id"] == task_id


def test_pagination_metadata(client, api_key_headers):
    """Тест метаданных пагинации"""
    # Создаём несколько задач
    for i in range(5):
        resp = client.post(
            "/api/v1/tasks",
            json={"title": f"Pagination Test {i}", "description": "test", "status": "pending", "priority": "medium"},
            headers=api_key_headers
        )
        assert resp.status_code == 201
    
    # Запрашиваем 2-ю страницу
    response = client.get(
        "/api/v1/tasks?skip=2&limit=2",
        headers=api_key_headers
    )
    
    assert response.status_code == 200
    data = response.json()
    meta = data["meta"]
    assert meta["page_size"] == 2
    assert meta["total_count"] == 5
    assert meta["page"] == 2


def test_update_task(client, api_key_headers):
    """Тест обновления задачи"""
    # Создаём
    create_response = client.post(
        "/api/v1/tasks",
        json={"title": "Before Update", "description": "test", "status": "pending", "priority": "low"},
        headers=api_key_headers
    )
    assert create_response.status_code == 201
    task_id = create_response.json()["id"]
    
    # Обновляем
    response = client.put(
        f"/api/v1/tasks/{task_id}",
        json={"title": "After Update", "status": "completed"},
        headers=api_key_headers
    )
    
    assert response.status_code == 200
    assert response.json()["title"] == "After Update"
    assert response.json()["status"] == "completed"


def test_delete_task(client, api_key_headers):
    """Тест удаления задачи"""
    # Создаём
    create_response = client.post(
        "/api/v1/tasks",
        json={"title": "To Delete", "description": "test", "status": "pending", "priority": "low"},
        headers=api_key_headers
    )
    assert create_response.status_code == 201
    task_id = create_response.json()["id"]
    
    # Удаляем
    response = client.delete(
        f"/api/v1/tasks/{task_id}",
        headers=api_key_headers
    )
    
    assert response.status_code == 204
    
    # Проверяем что удалена
    get_response = client.get(
        f"/api/v1/tasks/{task_id}",
        headers=api_key_headers
    )
    assert get_response.status_code == 404