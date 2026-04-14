-- ============================================
-- 1. Создание ENUM типов (соответствуют вашим Enum из models/enums.py)
-- ============================================
DO $$ 
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'task_status') THEN
        CREATE TYPE task_status AS ENUM ('pending', 'in_progress', 'completed');
    END IF;
    
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'task_priority') THEN
        CREATE TYPE task_priority AS ENUM ('low', 'medium', 'high');
    END IF;
END $$;

-- ============================================
-- 2. Создание таблицы задач (исправлено)
-- ============================================
CREATE TABLE IF NOT EXISTS tasks (
    -- UUID идентификатор
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    
    -- Название задачи (обязательное поле, макс 200 символов)
    title VARCHAR(200) NOT NULL,
    
    -- Описание задачи (может быть NULL)
    description TEXT,
    
    -- Статус задачи (использует ENUM)
    status task_status NOT NULL DEFAULT 'pending',
    
    -- Приоритет задачи (использует ENUM)
    priority task_priority NOT NULL DEFAULT 'medium',
    
    -- Временные метки
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMPTZ,
    
    -- Для сортировки задач
    order_index INTEGER DEFAULT 0,
    
    -- Для soft delete (опционально)
    deleted_at TIMESTAMPTZ,
    is_deleted BOOLEAN DEFAULT FALSE,
    
    -- Добавляем CHECK constraints для валидации
    CONSTRAINT title_not_empty CHECK (length(trim(title)) > 0),
    CONSTRAINT valid_dates CHECK (completed_at IS NULL OR completed_at >= created_at)
);

-- Комментарии к таблице и колонкам
COMMENT ON TABLE tasks IS 'Таблица задач с поддержкой статусов и приоритетов';
COMMENT ON COLUMN tasks.id IS 'Уникальный идентификатор задачи (UUID)';
COMMENT ON COLUMN tasks.title IS 'Название задачи (обязательное поле)';
COMMENT ON COLUMN tasks.status IS 'Статус задачи: pending, in_progress, completed';
COMMENT ON COLUMN tasks.priority IS 'Приоритет задачи: low, medium, high';
COMMENT ON COLUMN tasks.completed_at IS 'Дата завершения задачи (автоматически устанавливается)';
COMMENT ON COLUMN tasks.is_deleted IS 'Флаг мягкого удаления';

-- ============================================
-- 3. ОПТИМИЗИРОВАННЫЕ ИНДЕКСЫ (исправлено)
-- ============================================

-- ГЛАВНЫЙ ИНДЕКС: для фильтрации по status (только активные записи)
CREATE INDEX IF NOT EXISTS idx_tasks_status ON tasks(status) 
WHERE is_deleted = FALSE;

-- Составной индекс для частых комбинаций status + priority
CREATE INDEX IF NOT EXISTS idx_tasks_status_priority ON tasks(status, priority) 
WHERE is_deleted = FALSE;

-- Индекс для сортировки по дате создания (DESC для новых задач)
CREATE INDEX IF NOT EXISTS idx_tasks_created_at ON tasks(created_at DESC) 
WHERE is_deleted = FALSE;

-- Индекс для сортировки по updated_at
CREATE INDEX IF NOT EXISTS idx_tasks_updated_at ON tasks(updated_at DESC) 
WHERE is_deleted = FALSE;

-- Частичный индекс для активных задач (исправлен - убрал лишние колонки)
CREATE INDEX IF NOT EXISTS idx_tasks_active ON tasks(status, priority, order_index, created_at)
WHERE status IN ('pending', 'in_progress') AND is_deleted = FALSE;

-- Индекс для поиска по заголовку (для LIKE запросов)
CREATE INDEX IF NOT EXISTS idx_tasks_title ON tasks(title varchar_pattern_ops) 
WHERE is_deleted = FALSE;

-- Индекс для фильтрации по приоритету
CREATE INDEX IF NOT EXISTS idx_tasks_priority ON tasks(priority) 
WHERE is_deleted = FALSE;

-- Индекс для completed_at (для отчетов)
CREATE INDEX IF NOT EXISTS idx_tasks_completed_at ON tasks(completed_at DESC) 
WHERE status = 'completed' AND is_deleted = FALSE;

-- Индекс для soft delete
CREATE INDEX IF NOT EXISTS idx_tasks_deleted ON tasks(is_deleted) 
WHERE is_deleted = TRUE;

-- GIN индекс для полнотекстового поиска (опционально)
CREATE INDEX IF NOT EXISTS idx_tasks_search_gin ON tasks 
USING gin(to_tsvector('russian', coalesce(title, '') || ' ' || coalesce(description, '')))
WHERE is_deleted = FALSE;

-- ============================================
-- 4. Автоматическое обновление updated_at (исправлено)
-- ============================================

-- Функция для обновления временной метки
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Триггер, который вызывает функцию при UPDATE
DROP TRIGGER IF EXISTS update_tasks_updated_at ON tasks;
CREATE TRIGGER update_tasks_updated_at
    BEFORE UPDATE ON tasks
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- ============================================
-- 5. Функция для автоматической установки completed_at (исправлено)
-- ============================================

CREATE OR REPLACE FUNCTION update_completed_at()
RETURNS TRIGGER AS $$
BEGIN
    -- Если статус меняется на 'completed'
    IF NEW.status = 'completed' AND (OLD.status IS DISTINCT FROM 'completed') THEN
        NEW.completed_at = CURRENT_TIMESTAMP;
    -- Если статус меняется с 'completed' на другой
    ELSIF NEW.status != 'completed' AND (OLD.status = 'completed') THEN
        NEW.completed_at = NULL;
    -- Если статус не меняется, но completed_at нужно синхронизировать
    ELSIF NEW.status != 'completed' AND NEW.completed_at IS NOT NULL THEN
        NEW.completed_at = NULL;
    END IF;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS update_tasks_completed_at ON tasks;
CREATE TRIGGER update_tasks_completed_at
    BEFORE UPDATE OF status ON tasks
    FOR EACH ROW
    EXECUTE FUNCTION update_completed_at();

-- ============================================
-- 6. Функция для автоматической установки created_at (для вставок)
-- ============================================

CREATE OR REPLACE FUNCTION set_created_at()
RETURNS TRIGGER AS $$
BEGIN
    IF NEW.created_at IS NULL THEN
        NEW.created_at = CURRENT_TIMESTAMP;
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS set_tasks_created_at ON tasks;
CREATE TRIGGER set_tasks_created_at
    BEFORE INSERT ON tasks
    FOR EACH ROW
    EXECUTE FUNCTION set_created_at();

-- ============================================
-- 7. Функция для валидации переходов статусов
-- ============================================

CREATE OR REPLACE FUNCTION validate_status_transition()
RETURNS TRIGGER AS $$
BEGIN
    -- Разрешенные переходы статусов
    IF OLD.status IS NOT NULL AND NEW.status != OLD.status THEN
        -- Проверка переходов
        IF NOT (
            (OLD.status = 'pending' AND NEW.status IN ('in_progress', 'completed')) OR
            (OLD.status = 'in_progress' AND NEW.status IN ('pending', 'completed')) OR
            (OLD.status = 'completed' AND NEW.status = 'pending')
        ) THEN
            RAISE EXCEPTION 'Invalid status transition from % to %', OLD.status, NEW.status
            USING HINT = 'Allowed transitions: pending->in_progress/completed, in_progress->pending/completed, completed->pending';
        END IF;
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS validate_tasks_status ON tasks;
CREATE TRIGGER validate_tasks_status
    BEFORE UPDATE OF status ON tasks
    FOR EACH ROW
    EXECUTE FUNCTION validate_status_transition();

-- ============================================
-- 8. Функция для мягкого удаления
-- ============================================

CREATE OR REPLACE FUNCTION soft_delete_task()
RETURNS TRIGGER AS $$
BEGIN
    NEW.is_deleted = TRUE;
    NEW.deleted_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Триггер для мягкого удаления (нужно вызывать явно или через UPDATE)
-- Создаем вместо этого функцию для использования в приложении

-- ============================================
-- 9. Полезные функции для работы с задачами
-- ============================================

-- Функция для получения статистики по задачам
CREATE OR REPLACE FUNCTION get_tasks_statistics()
RETURNS TABLE(
    total_tasks BIGINT,
    active_tasks BIGINT,
    completed_tasks BIGINT,
    high_priority_count BIGINT,
    medium_priority_count BIGINT,
    low_priority_count BIGINT,
    avg_completion_time_hours NUMERIC
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        COUNT(*)::BIGINT as total_tasks,
        COUNT(*) FILTER (WHERE status IN ('pending', 'in_progress') AND is_deleted = FALSE)::BIGINT as active_tasks,
        COUNT(*) FILTER (WHERE status = 'completed' AND is_deleted = FALSE)::BIGINT as completed_tasks,
        COUNT(*) FILTER (WHERE priority = 'high' AND is_deleted = FALSE)::BIGINT as high_priority_count,
        COUNT(*) FILTER (WHERE priority = 'medium' AND is_deleted = FALSE)::BIGINT as medium_priority_count,
        COUNT(*) FILTER (WHERE priority = 'low' AND is_deleted = FALSE)::BIGINT as low_priority_count,
        ROUND(AVG(EXTRACT(EPOCH FROM (completed_at - created_at)) / 3600)::NUMERIC, 2) as avg_completion_time_hours
    FROM tasks
    WHERE is_deleted = FALSE;
END;
$$ LANGUAGE plpgsql;

-- Функция для эскалации приоритета просроченных задач
CREATE OR REPLACE FUNCTION escalate_overdue_tasks(hours_threshold INTEGER DEFAULT 24)
RETURNS INTEGER AS $$
DECLARE
    updated_count INTEGER;
BEGIN
    WITH updated AS (
        UPDATE tasks
        SET priority = 'high',
            updated_at = CURRENT_TIMESTAMP
        WHERE status IN ('pending', 'in_progress')
            AND priority IN ('low', 'medium')
            AND created_at <= CURRENT_TIMESTAMP - (hours_threshold || ' hours')::INTERVAL
            AND is_deleted = FALSE
        RETURNING id
    )
    SELECT COUNT(*) INTO updated_count FROM updated;
    
    RETURN updated_count;
END;
$$ LANGUAGE plpgsql;

-- ============================================
-- 10. Вывод информации о созданных индексах (исправлено)
-- ============================================
SELECT
    schemaname,
    tablename,
    indexname,
    indexdef,
    pg_size_pretty(pg_relation_size(indexname::regclass)) as index_size
FROM pg_indexes
WHERE tablename = 'tasks'
ORDER BY indexname;

-- ============================================
-- 11. Вывод информации о триггерах
-- ============================================
SELECT
    trigger_name,
    event_manipulation,
    event_object_table,
    action_statement,
    action_timing
FROM information_schema.triggers
WHERE event_object_table = 'tasks'
ORDER BY trigger_name;

-- ============================================
-- 12. Тестовые данные (опционально)
-- ============================================
DO $$
DECLARE
    i INTEGER;
BEGIN
    -- Проверяем, пустая ли таблица
    IF (SELECT COUNT(*) FROM tasks WHERE is_deleted = FALSE) = 0 THEN
        FOR i IN 1..100 LOOP
            INSERT INTO tasks (title, description, status, priority, order_index)
            VALUES (
                'Тестовая задача ' || i,
                CASE WHEN i % 3 = 0 THEN 'Подробное описание задачи ' || i ELSE NULL END,
                CASE (i % 3)
                    WHEN 0 THEN 'completed'::task_status
                    WHEN 1 THEN 'pending'::task_status
                    ELSE 'in_progress'::task_status
                END,
                CASE (i % 3)
                    WHEN 0 THEN 'low'::task_priority
                    WHEN 1 THEN 'medium'::task_priority
                    ELSE 'high'::task_priority
                END,
                i
            );
        END LOOP;
        
        -- Для некоторых завершенных задач устанавливаем completed_at
        UPDATE tasks 
        SET completed_at = created_at + interval '2 days'
        WHERE status = 'completed' AND completed_at IS NULL;
        
        RAISE NOTICE 'Создано 100 тестовых задач';
    END IF;
END $$;

-- ============================================
-- 13. Проверка работы индексов (после создания тестовых данных)
-- ============================================
EXPLAIN (ANALYZE, BUFFERS, TIMING) 
SELECT * FROM tasks 
WHERE status = 'pending' AND is_deleted = FALSE;

-- ============================================
-- 14. Очистка старых мягко удаленных задач (опционально)
-- ============================================
CREATE OR REPLACE FUNCTION cleanup_soft_deleted_tasks(days_old INTEGER DEFAULT 30)
RETURNS INTEGER AS $$
DECLARE
    deleted_count INTEGER;
BEGIN
    WITH deleted AS (
        DELETE FROM tasks
        WHERE is_deleted = TRUE 
            AND deleted_at <= CURRENT_TIMESTAMP - (days_old || ' days')::INTERVAL
        RETURNING id
    )
    SELECT COUNT(*) INTO deleted_count FROM deleted;
    
    RETURN deleted_count;
END;
$$ LANGUAGE plpgsql;