E:\Task_manager\
├── app/
│   ├── api/
│   │   ├── dependencies/
│   │   │   ├── auth.py
│   │   │   ├── database.py
│   │   │   └── tasks.py
│   │   └── routes/
│   │       └── tasks.py
│   ├── core/
│   │   ├── config.py
│   │   └── database.py
│   ├── middleware/
│   │   ├── logging_middleware.py
│   │   └── performance_middleware.py
│   ├── models/
│   │   └── schemas.py
│   ├── repositories/
│   │   └── task_repository.py
│   ├── services/
│   │   └── task_service.py
│   └── main.py
├── tests/
│   ├── test_api/
│   │   └── test_tasks.py
│   ├── test_unit/
│   │   └── test_services.py
│   └── conftest.py
├── logs/
│   └── api.log
├── pytest.ini
├── requirements-dev.txt
└── .env