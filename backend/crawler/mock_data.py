"""
Mock爬虫数据 — 当MediaCrawler不可用时，提供模拟数据用于测试下游Agent分析链路
"""
import random
from models.schemas import CleanedItem

# 按主题分类的mock语料库
MOCK_CORPUS = {
    # 通用痛点抱怨
    "pain_complaints": [
        "用了三个月的{keyword}，体验太差了，界面卡顿不说，客服根本联系不上，想换但市面上好像没人做这个？",
        "真心求推荐好用的{keyword}工具，目前试过的要么功能不全要么价格太贵，有没有性价比高的？",
        "作为一个{target_user}，我找了半年的{keyword}方案都没有满意的，要么太复杂要么太简陋，无语了",
        "大家有没有觉得市面上的{keyword}产品都差不多？完全找不到眼前一亮的东西",
        "{keyword}这个需求我身边至少10个人都有，但就是没人做个好产品出来，真不理解",
        "吐槽一下{keyword}的现状：要么是国外产品水土不服，要么是国内山寨质量堪忧",
        "每次用{keyword}都得打开四五个软件来回切换，效率太低了，有没有一站式解决的？",
        "老板让我找{keyword}的工具，调研了一圈发现全是to C的，to B的基本没有，这是个机会啊",
        "用了XX{keyword}一个月，bug多到怀疑人生，开发团队是不是不维护了？",
        "关于{keyword}，我想说现有的解决方案都是10年前的产品逻辑了，现在的用户习惯已经完全不同",
    ],
    # 需求表达（强需求信号）
    "strong_demand": [
        "我愿意花500块一个月买个靠谱的{keyword}服务，问题是现在有钱都没地方花！",
        "{keyword}是我每天最头疼的事情，如果谁能解决这个问题，我第一个付费",
        "蹲一个{keyword}的好方案，我们公司团队20多个人都需要，预算充足",
        "有没有在做{keyword}创业的？我可以当种子用户，真的需要这个",
        "各位大佬，{keyword}有没有什么好推荐的？我已经踩了太多坑了，求拯救",
        "说实话{keyword}这个赛道我觉得还没人真正做好，谁做出来我就用谁",
        "每天都在被{keyword}折磨，跪求一个解决方案，价格不是问题",
        "看到隔壁部门用了个{keyword}系统，羡慕哭了，为什么我们就没有？",
    ],
    # 竞品相关
    "competitor_mentions": [
        "试过{competitor}，功能确实强但学习成本太高了，对我们这种小团队不友好",
        "{competitor}价格太离谱了，基础版都要299一个月，个人用户根本用不起",
        "{competitor}挺好用的，但就是XX功能一直没做，反馈了半年也没回应",
        "用了两年{competitor}，最近更新越来越慢，感觉团队在躺平",
        "朋友推荐了{competitor}，试了一下发现功能堆砌严重，80%的功能我用不上",
        "{competitor}的用户体验确实不错，但数据安全方面我很担心，毕竟所有数据都存在他们那边",
        "对比了{competitor}和{competitor2}，前者功能全但贵，后者便宜但不稳定，有没有中间选项？",
    ],
    # 知乎风格（更理性分析）
    "zhihu_style": [
        "如何看待{keyword}这个赛道？目前市场上有哪些主要玩家？前景如何？",
        "作为一个产品经理，我认为{keyword}领域最大的痛点是用户体验和成本之间的平衡",
        "分析一下为什么{keyword}在中国市场一直没有出现现象级产品？是需求伪命题还是执行问题？",
        "从技术角度讲，{keyword}的实现难度并不高，关键是如何定义产品边界和核心用户场景",
        "有没有人系统调研过{keyword}的用户画像？我怀疑真实需求被高估了",
        "分享一下我们团队做{keyword}踩过的坑：获客成本远超预期，用户教育不够",
    ],
    # 积极反馈（部分需求已被满足）
    "positive_feedback": [
        "最近发现了一个叫{competitor}的神器，{keyword}体验大幅提升，推荐给大家",
        "用{competitor}半年了，总体来说{keyword}方面做得还行，基本能满足日常需求",
        "{competitor}的新版本解决了我之前吐槽的几个问题，团队还是有在认真做产品的",
        "对比了五六款{keyword}产品，{competitor}算是最能打的了，虽然还有改进空间",
    ],
}


def _fill_template(template: str, keyword: str, target_user: str = "普通用户",
                   competitor: str = "某产品", competitor2: str = "另一款产品") -> str:
    return template.format(
        keyword=keyword,
        target_user=target_user,
        competitor=competitor,
        competitor2=competitor2,
    )


def generate_mock_data(keywords: list[str], items_per_keyword: int = 8) -> list[CleanedItem]:
    """
    为给定关键词生成mock爬虫数据

    Args:
        keywords: 关键词列表
        items_per_keyword: 每个关键词生成的数据条数

    Returns:
        List[CleanedItem]: 可直接传入DataCleaner的mock数据
    """
    competitors_pool = ["Notion", "飞书", "钉钉", "语雀", "Confluence", "Trello",
                        "Todoist", "石墨文档", "Wolai", "FlowUs", "Obsidian", "Logseq"]
    xhs_url_tpl = "https://www.xiaohongshu.com/explore/mock_{}"
    zhihu_url_tpl = "https://www.zhihu.com/question/mock_{}"

    all_items = []
    url_counter = 0

    for keyword in keywords:
        for i in range(items_per_keyword):
            url_counter += 1
            competitor = random.choice(competitors_pool)
            competitor2 = random.choice([c for c in competitors_pool if c != competitor])
            target_user = random.choice(["上班族", "创业者", "自由职业者", "学生", "宝妈", "产品经理"])

            # 70% 小红书风格, 30% 知乎风格
            if random.random() < 0.7:
                platform = "xiaohongshu"
                source_url = xhs_url_tpl.format(url_counter)
                # 混合不同情绪维度
                r = random.random()
                if r < 0.25:
                    pool = MOCK_CORPUS["pain_complaints"]
                    emotion = "强烈"
                    engagement_base = random.randint(200, 500)
                elif r < 0.45:
                    pool = MOCK_CORPUS["strong_demand"]
                    emotion = "强烈"
                    engagement_base = random.randint(150, 400)
                elif r < 0.6:
                    pool = MOCK_CORPUS["competitor_mentions"]
                    emotion = "一般"
                    engagement_base = random.randint(50, 200)
                elif r < 0.75:
                    pool = MOCK_CORPUS["positive_feedback"]
                    emotion = "轻微"
                    engagement_base = random.randint(20, 100)
                else:
                    pool = MOCK_CORPUS["pain_complaints"]
                    emotion = "一般"
                    engagement_base = random.randint(30, 150)
            else:
                platform = "zhihu"
                source_url = zhihu_url_tpl.format(url_counter)
                pool = MOCK_CORPUS["zhihu_style"]
                emotion = random.choice(["一般", "轻微"])
                engagement_base = random.randint(50, 300)

            template = random.choice(pool)
            content = _fill_template(template, keyword, target_user, competitor, competitor2)
            engagement = engagement_base + random.randint(0, 100)

            item = CleanedItem(
                content=content,
                source_url=source_url,
                platform=platform,
                engagement=engagement,
                emotion_intensity=emotion,
            )
            all_items.append(item)

    random.shuffle(all_items)
    return all_items


# 预生成的demo数据，开箱即用
DEMO_KEYWORDS = ["AI写作工具", "智能笔记", "知识管理"]
DEMO_PROBLEM = "现有的知识管理工具功能割裂，用户需要在多个工具间频繁切换"
DEMO_SOLUTION = "集成AI写作、智能笔记和知识图谱的一站式知识管理平台"
DEMO_TARGET_USER = "需要大量阅读和写作的知识工作者"
DEMO_COMPETITORS = ["Notion", "飞书文档", "Obsidian"]
DEMO_DATA = generate_mock_data(DEMO_KEYWORDS, items_per_keyword=10)
