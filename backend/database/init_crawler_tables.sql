-- MediaCrawler集成 - 数据库初始化脚本
-- 执行说明：请在PostgreSQL中执行此脚本
-- 命令示例：psql -U postgres -d whetherwecando -f init_crawler_tables.sql

-- 1. 爬虫登录态配置表
CREATE TABLE IF NOT EXISTS crawler_auth_config (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    platform VARCHAR(50) NOT NULL UNIQUE,
    login_type VARCHAR(20) NOT NULL,
    encrypted_cookie TEXT NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'valid',
    expires_at TIMESTAMP WITH TIME ZONE,
    last_validated_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    CONSTRAINT chk_platform CHECK (platform IN ('xiaohongshu', 'zhihu')),
    CONSTRAINT chk_login_type CHECK (login_type IN ('qrcode', 'cookie')),
    CONSTRAINT chk_status CHECK (status IN ('valid', 'expiring', 'expired', 'invalid'))
);

COMMENT ON TABLE crawler_auth_config IS '爬虫登录态配置表';
COMMENT ON COLUMN crawler_auth_config.platform IS '平台名称：xiaohongshu/zhihu';
COMMENT ON COLUMN crawler_auth_config.login_type IS '登录方式：qrcode扫码/cookie手动配置';
COMMENT ON COLUMN crawler_auth_config.encrypted_cookie IS 'AES-256-GCM加密后的Cookie';
COMMENT ON COLUMN crawler_auth_config.status IS '登录态状态：valid有效/expiring即将过期/expired已过期/invalid无效';
COMMENT ON COLUMN crawler_auth_config.expires_at IS 'Cookie过期时间';

-- 2. 爬取任务表
CREATE TABLE IF NOT EXISTS crawl_task (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    platform VARCHAR(50) NOT NULL,
    keyword VARCHAR(255) NOT NULL,
    max_count INTEGER NOT NULL DEFAULT 50,
    status VARCHAR(20) NOT NULL DEFAULT 'pending',
    total_count INTEGER DEFAULT 0,
    success_count INTEGER DEFAULT 0,
    error_count INTEGER DEFAULT 0,
    error_message TEXT,
    started_at TIMESTAMP WITH TIME ZONE,
    completed_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    CONSTRAINT chk_crawl_platform CHECK (platform IN ('xiaohongshu', 'zhihu')),
    CONSTRAINT chk_crawl_status CHECK (status IN ('pending', 'running', 'completed', 'failed', 'cancelled')),
    CONSTRAINT chk_max_count CHECK (max_count > 0 AND max_count <= 100)
);

COMMENT ON TABLE crawl_task IS '爬取任务表';
COMMENT ON COLUMN crawl_task.platform IS '爬取平台';
COMMENT ON COLUMN crawl_task.keyword IS '搜索关键词';
COMMENT ON COLUMN crawl_task.max_count IS '最大爬取数量（1-100）';
COMMENT ON COLUMN crawl_task.status IS '任务状态';
COMMENT ON COLUMN crawl_task.total_count IS '总爬取数量';
COMMENT ON COLUMN crawl_task.success_count IS '成功数量';
COMMENT ON COLUMN crawl_task.error_count IS '失败数量';

-- 3. 爬取日志表
CREATE TABLE IF NOT EXISTS crawl_log (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    task_id UUID NOT NULL REFERENCES crawl_task(id) ON DELETE CASCADE,
    level VARCHAR(20) NOT NULL,
    message TEXT NOT NULL,
    details JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    CONSTRAINT chk_log_level CHECK (level IN ('info', 'warning', 'error', 'debug'))
);

COMMENT ON TABLE crawl_log IS '爬取日志表';
COMMENT ON COLUMN crawl_log.level IS '日志级别：info/warning/error/debug';
COMMENT ON COLUMN crawl_log.message IS '日志消息';
COMMENT ON COLUMN crawl_log.details IS '详细信息（JSON格式）';

-- 4. 爬取结果表（扩展原有crawl_results表，添加新字段）
-- 注意：crawl_results表已存在，这里添加新字段
ALTER TABLE crawl_results 
ADD COLUMN IF NOT EXISTS emotion_intensity VARCHAR(20),
ADD COLUMN IF NOT EXISTS crawl_task_id UUID REFERENCES crawl_task(id) ON DELETE SET NULL;

COMMENT ON COLUMN crawl_results.emotion_intensity IS '情绪强度：strong/medium/weak';
COMMENT ON COLUMN crawl_results.crawl_task_id IS '关联的爬取任务ID';

-- 创建索引
CREATE INDEX IF NOT EXISTS idx_crawler_auth_platform ON crawler_auth_config(platform);
CREATE INDEX IF NOT EXISTS idx_crawler_auth_status ON crawler_auth_config(status);
CREATE INDEX IF NOT EXISTS idx_crawl_task_platform ON crawl_task(platform);
CREATE INDEX IF NOT EXISTS idx_crawl_task_status ON crawl_task(status);
CREATE INDEX IF NOT EXISTS idx_crawl_task_created ON crawl_task(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_crawl_log_task_id ON crawl_log(task_id);
CREATE INDEX IF NOT EXISTS idx_crawl_log_created ON crawl_log(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_crawl_results_task_id ON crawl_results(crawl_task_id);

-- 更新触发器（自动更新updated_at）
CREATE TRIGGER update_crawler_auth_config_updated_at
    BEFORE UPDATE ON crawler_auth_config
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_crawl_task_updated_at
    BEFORE UPDATE ON crawl_task
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- 插入初始化数据（可选）
-- 注意：实际Cookie需要用户手动配置或扫码登录
-- INSERT INTO crawler_auth_config (platform, login_type, encrypted_cookie, status)
-- VALUES ('xiaohongshu', 'cookie', '', 'invalid');

-- 完成提示
DO $$
BEGIN
    RAISE NOTICE '========================================';
    RAISE NOTICE 'MediaCrawler数据库表创建完成！';
    RAISE NOTICE '========================================';
    RAISE NOTICE '创建的表：';
    RAISE NOTICE '  1. crawler_auth_config (登录态配置)';
    RAISE NOTICE '  2. crawl_task (爬取任务)';
    RAISE NOTICE '  3. crawl_log (爬取日志)';
    RAISE NOTICE '  4. crawl_results (已扩展字段)';
    RAISE NOTICE '========================================';
    RAISE NOTICE '下一步：配置环境变量CRAWLER_ENCRYPTION_KEY';
    RAISE NOTICE '========================================';
END $$;
