CREATE TABLE unity_test_results (
    id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    task_id BIGINT UNSIGNED NOT NULL,
    test_platform VARCHAR(20) NOT NULL,
    result VARCHAR(32) NOT NULL,
    total INT NOT NULL,
    passed INT NOT NULL,
    failed INT NOT NULL,
    skipped INT NOT NULL,
    inconclusive INT NOT NULL,
    duration_seconds DOUBLE NOT NULL,
    engine_version VARCHAR(32) NULL,
    started_at DATETIME NULL,
    finished_at DATETIME NULL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL
        DEFAULT CURRENT_TIMESTAMP
        ON UPDATE CURRENT_TIMESTAMP,

    PRIMARY KEY (id),
    CONSTRAINT fk_unity_test_results_task
        FOREIGN KEY (task_id) REFERENCES test_tasks(id),
    UNIQUE KEY uq_unity_test_results_task_platform(
        task_id,
        test_platform
    ),
    INDEX idx_unity_test_results_task_id(task_id)
);
