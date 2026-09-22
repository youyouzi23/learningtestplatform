CREATE TABLE IF NOT EXISTS bugsinpy_results (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    task_id BIGINT NOT NULL,
    project VARCHAR(100) NOT NULL,
    bug_id INT NOT NULL,
    trigger_test VARCHAR(255) NOT NULL,
    buggy_outcome VARCHAR(20) NOT NULL,
    fixed_outcome VARCHAR(20) NOT NULL,
    failure_log TEXT NOT NULL,
    category VARCHAR(50) NOT NULL,
    reason VARCHAR(255) NOT NULL,
    suggestion VARCHAR(255) NOT NULL,
    regression_passed BOOLEAN NOT NULL,
    INDEX idx_bugsinpy_results_task_id (task_id),
    CONSTRAINT fk_bugsinpy_results_task
        FOREIGN KEY (task_id) REFERENCES test_tasks(id)
        ON DELETE CASCADE
);
