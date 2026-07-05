"""
星羽创媒 CMS — 前端数据 API
"""
from flask import Blueprint, jsonify, request
from models import Case, ContentBlock, TeamMember, TrainingCard, Inquiry, EventCard, AgentCard, StudioCard, PlatformCard
from models import db

api = Blueprint('api', __name__, url_prefix='/api')


@api.route('/cases')
def get_cases():
    """获取案例列表"""
    category = request.args.get('category', 'ai-production')
    limit = request.args.get('limit', 50, type=int)
    show_on_home = request.args.get('show_on_home')

    query = Case.query.filter_by(is_published=True)
    if category != 'all':
        query = query.filter_by(category=category)
    if show_on_home == 'true':
        query = query.filter_by(show_on_home=True)
    elif show_on_home == 'false':
        query = query.filter_by(show_on_home=False)
    cases = query.order_by(Case.sort_order.desc()).limit(limit).all()

    return jsonify([{
        'id': c.id,
        'title': c.title,
        'description': c.description,
        'video_file': c.video_file,
        'thumbnail': c.thumbnail,
        'tags': c.get_tags_list(),
        'category': c.category,
        'show_on_home': c.show_on_home,
        'sort_order': c.sort_order,
        'en_name': c.en_name or '',
    } for c in cases])


@api.route('/cases/<int:case_id>/toggle-home', methods=['POST'])
def toggle_home(case_id):
    """切换案例的首页展示状态，最多4条"""
    case = Case.query.get_or_404(case_id)
    if case.show_on_home:
        case.show_on_home = False
        db.session.commit()
        return jsonify({'ok': True, 'show_on_home': False, 'msg': '已从首页移除'})
    else:
        count = Case.query.filter_by(show_on_home=True).count()
        if count >= 4:
            return jsonify({'ok': False, 'msg': '首页最多展示 4 个案例，请先取消一个'}), 400
        case.show_on_home = True
        db.session.commit()
        return jsonify({'ok': True, 'show_on_home': True, 'msg': '已添加到首页'})


@api.route('/cases/<int:case_id>/move', methods=['POST'])
def move_case(case_id):
    """调整案例排位：direction=up 或 down"""
    case = Case.query.get_or_404(case_id)
    direction = request.json.get('direction', 'up')

    # 获取同分类的所有案例，按 sort_order 降序
    siblings = Case.query.filter_by(category=case.category).order_by(Case.sort_order.desc()).all()
    idx = next((i for i, c in enumerate(siblings) if c.id == case_id), None)
    if idx is None:
        return jsonify({'ok': False, 'msg': '案例未找到'}), 404

    if direction == 'up' and idx == 0:
        return jsonify({'ok': False, 'msg': '已经是第一个了'})
    if direction == 'down' and idx == len(siblings) - 1:
        return jsonify({'ok': False, 'msg': '已经是最后一个了'})

    # 交换 sort_order
    if direction == 'up':
        other = siblings[idx - 1]
    else:
        other = siblings[idx + 1]

    case.sort_order, other.sort_order = other.sort_order, case.sort_order
    db.session.commit()
    return jsonify({'ok': True, 'msg': f'已{"上移" if direction == "up" else "下移"}'})


@api.route('/content')
def get_content():
    """获取页面文案"""
    page = request.args.get('page', 'index')
    blocks = ContentBlock.query.filter_by(page=page).all()

    # 按 section 分组
    result = {}
    for b in blocks:
        if b.section not in result:
            result[b.section] = {}
        result[b.section][b.key] = b.value

    return jsonify(result)


@api.route('/content/<page>/<section>')
def get_section_content(page, section):
    """获取某个区块的文案"""
    blocks = ContentBlock.query.filter_by(page=page, section=section).all()
    return jsonify({b.key: b.value for b in blocks})


@api.route('/team')
def get_team():
    """获取团队信息"""
    members = TeamMember.query.order_by(TeamMember.sort_order.desc()).all()
    return jsonify([{
        'id': m.id,
        'name': m.name,
        'role': m.role,
        'bio': m.bio,
        'photo': m.photo,
        'is_founder': m.is_founder,
    } for m in members])


@api.route('/team/<int:member_id>/move', methods=['POST'])
def move_team(member_id):
    """调整团队成员排位"""
    member = TeamMember.query.get_or_404(member_id)
    direction = request.json.get('direction', 'up')

    siblings = TeamMember.query.order_by(TeamMember.sort_order.desc()).all()
    idx = next((i for i, m in enumerate(siblings) if m.id == member_id), None)
    if idx is None:
        return jsonify({'ok': False, 'msg': '成员未找到'}), 404

    if direction == 'up' and idx == 0:
        return jsonify({'ok': False, 'msg': '已经是第一个了'})
    if direction == 'down' and idx == len(siblings) - 1:
        return jsonify({'ok': False, 'msg': '已经是最后一个了'})

    if direction == 'up':
        other = siblings[idx - 1]
    else:
        other = siblings[idx + 1]

    member.sort_order, other.sort_order = other.sort_order, member.sort_order
    db.session.commit()
    return jsonify({'ok': True, 'msg': f'已{"上移" if direction == "up" else "下移"}'})


@api.route('/stats')
def get_stats():
    """获取统计数据（快捷接口）"""
    blocks = ContentBlock.query.filter(
        ContentBlock.page == 'index',
        ContentBlock.section == 'hero',
        ContentBlock.key.like('stat_%')
    ).all()

    data = {b.key: b.value for b in blocks}
    return jsonify({
        'stat_1': {'num': data.get('stat_1_num', '100+'), 'label': data.get('stat_1_label', '完成项目')},
        'stat_2': {'num': data.get('stat_2_num', '50+'), 'label': data.get('stat_2_label', '合作品牌')},
        'stat_3': {'num': data.get('stat_3_num', '70%'), 'label': data.get('stat_3_label', '效率提升')},
        'stat_4': {'num': data.get('stat_4_num', '98%'), 'label': data.get('stat_4_label', '客户满意度')},
    })


@api.route('/training-cards')
def get_training_cards():
    """获取培训卡片列表"""
    limit = request.args.get('limit', 10, type=int)
    cards = TrainingCard.query.filter_by(is_published=True)\
        .order_by(TrainingCard.sort_order.desc()).limit(limit).all()

    return jsonify([{
        'id': c.id,
        'title': c.title,
        'description': c.description,
        'image': c.image,
        'tags': c.get_tags_list(),
        'sort_order': c.sort_order,
    } for c in cards])


@api.route('/training-cards/<int:card_id>/move', methods=['POST'])
def move_training_card(card_id):
    """调整培训卡片排位"""
    card = TrainingCard.query.get_or_404(card_id)
    direction = request.json.get('direction', 'up')

    siblings = TrainingCard.query.order_by(TrainingCard.sort_order.desc()).all()
    idx = next((i for i, c in enumerate(siblings) if c.id == card_id), None)
    if idx is None:
        return jsonify({'ok': False, 'msg': '卡片未找到'}), 404

    if direction == 'up' and idx == 0:
        return jsonify({'ok': False, 'msg': '已经是第一个了'})
    if direction == 'down' and idx == len(siblings) - 1:
        return jsonify({'ok': False, 'msg': '已经是最后一个了'})

    if direction == 'up':
        other = siblings[idx - 1]
    else:
        other = siblings[idx + 1]

    card.sort_order, other.sort_order = other.sort_order, card.sort_order
    db.session.commit()
    return jsonify({'ok': True, 'msg': f'已{"上移" if direction == "up" else "下移"}'})


@api.route('/inquiries', methods=['POST'])
def create_inquiry():
    """提交咨询"""
    data = request.get_json()
    if not data:
        return jsonify({'ok': False, 'msg': '请提供数据'}), 400

    name = data.get('name', '').strip()
    phone = data.get('phone', '').strip()
    if not name or not phone:
        return jsonify({'ok': False, 'msg': '姓名和电话必填'}), 400

    inquiry = Inquiry(
        name=name,
        company=data.get('company', '').strip(),
        phone=phone,
        service_type=data.get('service_type', '').strip(),
        message=data.get('message', '').strip(),
    )
    db.session.add(inquiry)
    db.session.commit()

    return jsonify({'ok': True, 'msg': '提交成功，我们会尽快联系您！'})


@api.route('/event-cards')
def get_event_cards():
    """获取文旅IP卡片列表"""
    cards = EventCard.query.filter_by(is_published=True)\
        .order_by(EventCard.sort_order.desc()).all()
    return jsonify([{
        'id': c.id,
        'title': c.title,
        'description': c.description,
        'image': c.image,
        'tags': c.get_tags_list(),
        'badge': c.badge,
        'badge_color': c.badge_color,
        'sort_order': c.sort_order,
    } for c in cards])


@api.route('/event-cards/<int:card_id>/move', methods=['POST'])
def move_event_card(card_id):
    """调整文旅IP卡片排位"""
    card = EventCard.query.get_or_404(card_id)
    direction = request.json.get('direction', 'up')
    siblings = EventCard.query.order_by(EventCard.sort_order.desc()).all()
    idx = next((i for i, c in enumerate(siblings) if c.id == card_id), None)
    if idx is None:
        return jsonify({'ok': False, 'msg': '卡片未找到'}), 404
    if direction == 'up' and idx == 0:
        return jsonify({'ok': False, 'msg': '已经是第一个了'})
    if direction == 'down' and idx == len(siblings) - 1:
        return jsonify({'ok': False, 'msg': '已经是最后一个了'})
    other = siblings[idx - 1] if direction == 'up' else siblings[idx + 1]
    card.sort_order, other.sort_order = other.sort_order, card.sort_order
    db.session.commit()
    return jsonify({'ok': True, 'msg': f'已{"上移" if direction == "up" else "下移"}'})


@api.route('/agent-cards')
def get_agent_cards():
    """获取企业AI Agent卡片列表"""
    cards = AgentCard.query.filter_by(is_published=True)\
        .order_by(AgentCard.sort_order.desc()).all()
    return jsonify([{
        'id': c.id,
        'title': c.title,
        'description': c.description,
        'image': c.image,
        'tags': c.get_tags_list(),
        'sort_order': c.sort_order,
    } for c in cards])


@api.route('/agent-cards/<int:card_id>/move', methods=['POST'])
def move_agent_card(card_id):
    """调整企业AI Agent卡片排位"""
    card = AgentCard.query.get_or_404(card_id)
    direction = request.json.get('direction', 'up')
    siblings = AgentCard.query.order_by(AgentCard.sort_order.desc()).all()
    idx = next((i for i, c in enumerate(siblings) if c.id == card_id), None)
    if idx is None:
        return jsonify({'ok': False, 'msg': '卡片未找到'}), 404
    if direction == 'up' and idx == 0:
        return jsonify({'ok': False, 'msg': '已经是第一个了'})
    if direction == 'down' and idx == len(siblings) - 1:
        return jsonify({'ok': False, 'msg': '已经是最后一个了'})
    other = siblings[idx - 1] if direction == 'up' else siblings[idx + 1]
    card.sort_order, other.sort_order = other.sort_order, card.sort_order
    db.session.commit()
    return jsonify({'ok': True, 'msg': f'已{"上移" if direction == "up" else "下移"}'})


@api.route('/studio-cards')
def get_studio_cards():
    """获取AI Studio功能卡片列表"""
    cards = StudioCard.query.filter_by(is_published=True)\
        .order_by(StudioCard.sort_order.desc()).all()
    return jsonify([{
        'id': c.id,
        'title': c.title,
        'description': c.description,
        'image': c.image,
        'tags': c.get_tags_list(),
        'sort_order': c.sort_order,
    } for c in cards])


@api.route('/studio-cards/<int:card_id>/move', methods=['POST'])
def move_studio_card(card_id):
    """调整AI Studio功能卡片排位"""
    card = StudioCard.query.get_or_404(card_id)
    direction = request.json.get('direction', 'up')
    siblings = StudioCard.query.order_by(StudioCard.sort_order.desc()).all()
    idx = next((i for i, c in enumerate(siblings) if c.id == card_id), None)
    if idx is None:
        return jsonify({'ok': False, 'msg': '卡片未找到'}), 404
    if direction == 'up' and idx == 0:
        return jsonify({'ok': False, 'msg': '已经是第一个了'})
    if direction == 'down' and idx == len(siblings) - 1:
        return jsonify({'ok': False, 'msg': '已经是最后一个了'})
    other = siblings[idx - 1] if direction == 'up' else siblings[idx + 1]
    card.sort_order, other.sort_order = other.sort_order, card.sort_order
    db.session.commit()
    return jsonify({'ok': True, 'msg': f'已{"上移" if direction == "up" else "下移"}'})


@api.route('/platform-cards')
def get_platform_cards():
    """获取AI Studio平台卡片列表"""
    cards = PlatformCard.query.filter_by(is_published=True)\
        .order_by(PlatformCard.sort_order.desc()).all()
    return jsonify([{
        'id': c.id,
        'title': c.title,
        'description': c.description,
        'image': c.image,
        'tags': c.get_tags_list(),
        'sort_order': c.sort_order,
    } for c in cards])


@api.route('/platform-cards/<int:card_id>/move', methods=['POST'])
def move_platform_card(card_id):
    """调整AI Studio平台卡片排位"""
    card = PlatformCard.query.get_or_404(card_id)
    direction = request.json.get('direction', 'up')
    siblings = PlatformCard.query.order_by(PlatformCard.sort_order.desc()).all()
    idx = next((i for i, c in enumerate(siblings) if c.id == card_id), None)
    if idx is None:
        return jsonify({'ok': False, 'msg': '卡片未找到'}), 404
    if direction == 'up' and idx == 0:
        return jsonify({'ok': False, 'msg': '已经是第一个了'})
    if direction == 'down' and idx == len(siblings) - 1:
        return jsonify({'ok': False, 'msg': '已经是最后一个了'})
    other = siblings[idx - 1] if direction == 'up' else siblings[idx + 1]
    card.sort_order, other.sort_order = other.sort_order, card.sort_order
    db.session.commit()
    return jsonify({'ok': True, 'msg': f'已{"上移" if direction == "up" else "下移"}'})


@api.route('/admin/ai-generate', methods=['POST'])
def ai_generate_case():
    """AI 自动生成案例的英文名和介绍"""
    import requests
    import re
    
    data = request.get_json() or {}
    title = data.get('title', '')
    category = data.get('category', '')
    
    if not title:
        return jsonify({'ok': False, 'msg': '标题不能为空'}), 400
    
    en_name = ''
    description = ''
    
    # 1. 英文名：用 Google Translate 免费 API
    try:
        url = 'https://translate.googleapis.com/translate_a/single'
        params = {'client': 'gtx', 'sl': 'zh-CN', 'tl': 'en', 'dt': 't', 'q': title}
        resp = requests.get(url, params=params, timeout=5)
        if resp.status_code == 200:
            result = resp.json()
            translated = ''.join([s[0] for s in result[0] if s[0]])
            # 清理：去掉 AI 空格多余符号
            en_name = re.sub(r'\s+', ' ', translated).strip()
    except Exception:
        en_name = title  # fallback
    
    # 2. 介绍：基于标题生成简短英文介绍
    cat_map = {
        'ai-production': 'AI Brand Video',
        'ai-training': 'AI Training',
        'tourism': 'Cultural Tourism',
        'brand': 'Brand Marketing'
    }
    cat_en = cat_map.get(category, 'Brand Video')
    
    if en_name and en_name != title:
        description = f'A {cat_en} created by Xingyu Creative Media. {en_name} — showcasing the fusion of AI technology and creative storytelling.'
    
    return jsonify({
        'ok': True,
        'en_name': en_name,
        'description': description
    })
