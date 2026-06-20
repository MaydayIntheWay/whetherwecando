-- Active: 1779710770815@@127.0.0.1@5432@whetherwecando
-- Idea可行性验证工具 - 数据库初始化脚本

-- 创建数据库（如果不存在）
-- 注意：需要在PostgreSQL命令行中执行或使用createdb命令

-- 创建表结构

-- 1. 验证任务表
CREATE TABLE IF NOT EXISTS validation_tasks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid (),
    status VARCHAR(50) NOT NULL DEFAULT 'pending',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 2. 产品输入表
CREATE TABLE IF NOT EXISTS product_inputs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid (),
    task_id UUID NOT NULL REFERENCES validation_tasks (id) ON DELETE CASCADE,
    problem TEXT NOT NULL,
    solution TEXT NOT NULL,
    target_user TEXT NOT NULL,
    known_competitors TEXT [],
    business_model VARCHAR(100),
    keywords TEXT [],
    raw_prd TEXT,
    raw_idea TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 3. 爬取结果表
CREATE TABLE IF NOT EXISTS crawl_results (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid (),
    task_id UUID REFERENCES validation_tasks (id) ON DELETE SET NULL,
    platform VARCHAR(50) NOT NULL,
    keyword VARCHAR(255) NOT NULL,
    content TEXT NOT NULL,
    source_url VARCHAR(500) NOT NULL,
    engagement INTEGER DEFAULT 0,
    crawled_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    error_message TEXT
);

-- 4. 验证报告表
CREATE TABLE IF NOT EXISTS validation_reports (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid (),
    task_id UUID NOT NULL REFERENCES validation_tasks (id) ON DELETE CASCADE,
    verdict VARCHAR(50) NOT NULL,
    verdict_reason TEXT NOT NULL,
    demand JSONB,
    feasibility JSONB,
    differentiation JSONB,
    risks JSONB,
    demand_heatmap JSONB,
    data_stats JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 创建索引
CREATE INDEX IF NOT EXISTS idx_crawl_results_task_id ON crawl_results (task_id);

CREATE INDEX IF NOT EXISTS idx_crawl_results_platform ON crawl_results (platform);

CREATE INDEX IF NOT EXISTS idx_product_inputs_task_id ON product_inputs (task_id);

CREATE INDEX IF NOT EXISTS idx_validation_reports_task_id ON validation_reports (task_id);

-- 更新触发器（自动更新updated_at）
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_validation_tasks_updated_at
    BEFORE UPDATE ON validation_tasks
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();