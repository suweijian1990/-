"""
星羽创媒 CMS — 管理后台视图
"""
import os
import uuid
from flask import redirect, url_for, request, flash
from markupsafe import Markup
from flask_admin import AdminIndexView, expose
from flask_admin.contrib.sqla import ModelView
from flask_admin.form import FileUploadField
from flask_login import current_user
from wtforms import StringField, TextAreaField, FileField
from werkzeug.utils import secure_filename

MAX_IMAGE_SIZE = 1 * 1024 * 1024  # 1MB


def compress_image(filepath, max_size=MAX_IMAGE_SIZE):
    """压缩图片到指定大小以内"""
    try:
        from PIL import Image
        import io

        # 检查文件大小
        if os.path.getsize(filepath) <= max_size:
            return

        img = Image.open(filepath)

        # 转换 RGBA 到 RGB
        if img.mode in ('RGBA', 'LA', 'P'):
            background = Image.new('RGB', img.size, (255, 255, 255))
            if img.mode == 'P':
                img = img.convert('RGBA')
            background.paste(img, mask=img.split()[-1] if img.mode == 'RGBA' else None)
            img = background

        # 逐步降低质量直到文件大小符合要求
        quality = 85
        while quality > 20:
            buffer = io.BytesIO()
            img.save(buffer, format='JPEG', quality=quality, optimize=True)
            if buffer.tell() <= max_size:
                # 保存压缩后的图片
                with open(filepath, 'wb') as f:
                    f.write(buffer.getvalue())
                # 修改文件扩展名为 .jpg
                new_filepath = os.path.splitext(filepath)[0] + '.jpg'
                if new_filepath != filepath:
                    os.rename(filepath, new_filepath)
                    return os.path.basename(new_filepath)
                return None
            quality -= 10

        # 如果降低质量还不够，就缩小尺寸
        ratio = 0.8
        while ratio > 0.3:
            new_size = (int(img.width * ratio), int(img.height * ratio))
            resized = img.resize(new_size, Image.Resampling.LANCZOS)
            buffer = io.BytesIO()
            resized.save(buffer, format='JPEG', quality=70, optimize=True)
            if buffer.tell() <= max_size:
                with open(filepath, 'wb') as f:
                    f.write(buffer.getvalue())
                new_filepath = os.path.splitext(filepath)[0] + '.jpg'
                if new_filepath != filepath:
                    os.rename(filepath, new_filepath)
                    return os.path.basename(new_filepath)
                return None
            ratio -= 0.1

    except Exception as e:
        print(f'图片压缩失败: {e}')
        return None


def save_upload(file_storage, folder, allowed_exts=None, compress=False):
    """保存上传文件，返回相对路径文件名"""
    if not file_storage or not file_storage.filename:
        return ''
    original = file_storage.filename
    safe = secure_filename(original)
    ext = os.path.splitext(original)[1].lower()
    # 如果 secure_filename 把中文等非ASCII字符清空，用UUID命名
    if not safe or len(os.path.splitext(safe)[0]) == 0:
        safe = f"{uuid.uuid4().hex[:8]}{ext}"
    else:
        safe = f"{uuid.uuid4().hex[:8]}_{safe}"
    if allowed_exts and ext not in allowed_exts:
        return ''
    filepath = os.path.join(folder, safe)
    file_storage.save(filepath)

    # 压缩图片
    if compress and ext in ('.jpg', '.jpeg', '.png', '.webp'):
        result = compress_image(filepath)
        if result:
            return result

    return safe


class AuthMixin:
    """管理后台认证 mixin"""
    def is_accessible(self):
        return current_user.is_authenticated

    def inaccessible_callback(self, name, **kwargs):
        return redirect(url_for('login', next=request.url))


class MyAdminIndexView(AuthMixin, AdminIndexView):
    @expose('/')
    def index(self):
        from models import Case, ContentBlock, TeamMember
        stats = {
            'cases': Case.query.count(),
            'content': ContentBlock.query.count(),
            'team': TeamMember.query.count(),
        }
        return self.render('admin/index.html', stats=stats)


def generate_gif_preview(video_filename, video_folder, image_folder):
    """用 ffmpeg 从视频截取4秒生成 MP4 预览封面，返回 MP4 文件名"""
    import subprocess
    import os
    import shutil

    if not shutil.which('ffmpeg'):
        return None

    video_path = os.path.join(video_folder, video_filename)
    if not os.path.exists(video_path):
        return None

    # 获取视频时长
    try:
        result = subprocess.run(
            ['ffprobe', '-v', 'error', '-show_entries', 'format=duration',
             '-of', 'csv=p=0', video_path],
            capture_output=True, text=True, timeout=10
        )
        duration = float(result.stdout.strip())
    except Exception:
        duration = 60

    mid = max(0, int(duration / 2))
    base = os.path.splitext(video_filename)[0]
    mp4_name = f"auto_{base}.mp4"
    mp4_path = os.path.join(image_folder, mp4_name)

    try:
        # 检测黑边
        crop_result = subprocess.run(
            ['ffmpeg', '-ss', str(mid), '-t', '1', '-i', video_path,
             '-vf', 'cropdetect=limit=24:round=2', '-f', 'null', '-'],
            capture_output=True, text=True, timeout=15
        )
        crop_line = None
        for line in crop_result.stderr.split('\n'):
            if 'crop=' in line:
                crop_line = line.split('crop=')[-1].strip().split(' ')[0]
        
        crop_filter = 'scale=640:-2'
        if crop_line:
            parts = crop_line.split(':')
            if len(parts) == 4:
                cw, ch = int(parts[0]), int(parts[1])
                try:
                    probe = subprocess.run(
                        ['ffprobe', '-v', 'error', '-select_streams', 'v:0',
                         '-show_entries', 'stream=width,height', '-of', 'csv=p=0', video_path],
                        capture_output=True, text=True, timeout=5
                    )
                    ow, oh = map(int, probe.stdout.strip().split(','))
                    if cw < ow * 0.9 or ch < oh * 0.9:
                        crop_filter = f'crop={crop_line},scale=640:-2'
                except Exception:
                    pass

        # 生成 MP4：h264, 静音, crf 30, faststart
        cmd = [
            'ffmpeg', '-y', '-ss', str(mid), '-t', '4', '-i', video_path,
            '-vf', f'{crop_filter},fps=24',
            '-an', '-c:v', 'libx264', '-preset', 'fast', '-crf', '23',
            '-pix_fmt', 'yuv420p', '-movflags', '+faststart',
            mp4_path
        ]
        subprocess.run(cmd, capture_output=True, timeout=30)

        if os.path.exists(mp4_path) and os.path.getsize(mp4_path) > 1000:
            return mp4_name
    except Exception:
        pass

    return None


class CaseAdminView(AuthMixin, ModelView):
    """案例管理"""
    column_list = ['id', 'title', 'category', 'tags', 'is_published', 'show_on_home', 'sort_order', 'updated_at']
    column_labels = {
        'title': '标题', 'description': '描述', 'video_file': '视频文件',
        'thumbnail': '缩略图', 'tags': '标签(逗号分隔)', 'category': '分类',
        'sort_order': '排序', 'is_published': '已发布', 'show_on_home': '首页展示',
        'created_at': '创建时间', 'updated_at': '更新时间',
    }
    column_searchable_list = ['title', 'tags']
    column_filters = ['category', 'is_published', 'show_on_home']
    column_default_sort = ('sort_order', True)
    column_formatters = {
        'video_file': lambda v, c, m, p: Markup(f'<span style="font-size:0.8rem;color:#8B5CF6;background:rgba(139,92,246,0.08);padding:4px 10px;border-radius:6px;">🎬 {m.video_file[:30]}...</span>') if m.video_file else '',
        'thumbnail': lambda v, c, m, p: Markup(f'<img src="/uploads/images/{m.thumbnail}" style="height:48px;width:48px;border-radius:8px;object-fit:cover;">') if m.thumbnail else '',
        'show_on_home': lambda v, c, m, p: Markup(
            f'<button class="btn btn-xs {"btn-success" if m.show_on_home else "btn-default"}" '
            f'onclick="toggleHome({m.id}, this); return false;" '
            f'style="font-size:0.78rem;padding:6px 14px;border-radius:8px;min-width:72px;font-weight:600;">'
            f'{"✓ 首页" if m.show_on_home else "设为首页"}</button>'
        ),
        'sort_order': lambda v, c, m, p: Markup(
            f'<div style="display:flex;align-items:center;gap:4px;">'
            f'<button class="sort-btn" onclick="moveCase({m.id},\'up\',this);return false;" title="上移" style="width:28px;height:28px;border-radius:6px;background:#f3f4f6;border:1px solid #e5e7eb;cursor:pointer;font-size:0.75rem;display:flex;align-items:center;justify-content:center;">▲</button>'
            f'<button class="sort-btn" onclick="moveCase({m.id},\'down\',this);return false;" title="下移" style="width:28px;height:28px;border-radius:6px;background:#f3f4f6;border:1px solid #e5e7eb;cursor:pointer;font-size:0.75rem;display:flex;align-items:center;justify-content:center;">▼</button>'
            f'</div>'
        ),
        'title': lambda v, c, m, p: Markup(f'<div style="font-weight:600;color:#1f2937;">{m.title}</div><div style="font-size:0.8rem;color:#9ca3af;margin-top:2px;">{m.category}</div>'),
        'tags': lambda v, c, m, p: Markup(f'<div class="case-tags">{"".join(["<span class=\"case-tag\">" + t.strip() + "</span>" for t in m.tags.split(",") if t.strip()])}</div>') if m.tags else '',
    }
    page_size = 20
    can_view_details = True
    create_template = 'admin/case_create.html'
    edit_template = 'admin/case_edit.html'
    list_template = 'admin/case_list.html'

    def on_model_change(self, form, model, is_created):
        """处理文件上传"""
        import logging
        logger = logging.getLogger('admin_views')
        from config import VIDEO_FOLDER, IMAGE_FOLDER
        
        # Ensure directories exist
        os.makedirs(VIDEO_FOLDER, exist_ok=True)
        os.makedirs(IMAGE_FOLDER, exist_ok=True)

        # 视频上传
        video = request.files.get('video_upload')
        logger.info(f'Video upload: filename={video.filename if video else None}, content_type={video.content_type if video else None}')
        if video and video.filename:
            name = save_upload(video, VIDEO_FOLDER, {'.mp4', '.mov', '.avi', '.webm'})
            if name:
                model.video_file = name
                flash(f'✅ 视频已上传: {name}', 'success')
                # 🎬 自动生成 GIF 预览封面
                try:
                    gif_name = generate_gif_preview(name, VIDEO_FOLDER, IMAGE_FOLDER)
                    if gif_name and not request.files.get('thumb_upload'):
                        model.thumbnail = gif_name
                        logger.info(f'GIF preview generated: {gif_name}')
                except Exception as e:
                    logger.error(f'GIF generation failed: {e}')
            else:
                flash('❌ 视频上传失败，请检查文件格式（支持 mp4/mov/avi/webm）', 'error')
                logger.error(f'Video upload failed for {video.filename}')
        elif video and not video.filename:
            pass  # No file selected
        else:
            pass  # No file field

        # 缩略图上传（用户手动上传的优先）
        thumb = request.files.get('thumb_upload')
        logger.info(f'Thumb upload: filename={thumb.filename if thumb else None}')
        if thumb and thumb.filename:
            name = save_upload(thumb, IMAGE_FOLDER, {'.jpg', '.jpeg', '.png', '.webp', '.gif'}, compress=True)
            if name:
                model.thumbnail = name
                flash(f'✅ 缩略图已上传: {name}', 'success')
            else:
                flash('❌ 缩略图上传失败，请检查文件格式（支持 jpg/png/webp/gif）', 'error')
                logger.error(f'Thumb upload failed for {thumb.filename}')


class ContentBlockAdminView(AuthMixin, ModelView):
    """文案管理"""
    column_list = ['page', 'section', 'key', 'value', 'content_type']
    column_labels = {
        'page': '页面', 'section': '区块', 'key': '字段名',
        'value': '内容', 'content_type': '类型',
    }
    column_searchable_list = ['page', 'section', 'key', 'value']
    column_filters = ['page', 'section', 'content_type']
    column_default_sort = [('page', False), ('section', False), ('key', False)]
    page_size = 50
    can_view_details = True
    column_formatters = {
        'value': lambda v, c, m, p: Markup(f'<span style="max-width:300px;display:inline-block;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;">{m.value[:80]}</span>') if m.value else '',
    }


class TeamMemberAdminView(AuthMixin, ModelView):
    """团队管理"""
    column_list = ['id', 'name', 'role', 'is_founder', 'sort_order']
    column_labels = {
        'name': '姓名', 'role': '职位', 'bio': '简介',
        'photo': '照片', 'is_founder': '创始人', 'sort_order': '排序',
    }
    column_searchable_list = ['name', 'role']
    column_filters = ['is_founder']
    column_default_sort = ('sort_order', True)
    column_formatters = {
        'photo': lambda v, c, m, p: Markup(f'<img src="/uploads/images/{m.photo}" style="height:40px;width:40px;border-radius:50%;object-fit:cover;">') if m.photo else '',
        'sort_order': lambda v, c, m, p: Markup(
            f'<div style="display:flex;align-items:center;gap:4px;">'
            f'<button class="sort-btn" onclick="moveTeam({m.id},\'up\',this);return false;" title="上移" style="width:28px;height:28px;border-radius:6px;background:#f3f4f6;border:1px solid #e5e7eb;cursor:pointer;font-size:0.75rem;display:flex;align-items:center;justify-content:center;">▲</button>'
            f'<button class="sort-btn" onclick="moveTeam({m.id},\'down\',this);return false;" title="下移" style="width:28px;height:28px;border-radius:6px;background:#f3f4f6;border:1px solid #e5e7eb;cursor:pointer;font-size:0.75rem;display:flex;align-items:center;justify-content:center;">▼</button>'
            f'</div>'
        ),
    }
    page_size = 20
    form_excluded_columns = []
    create_template = 'admin/team_create.html'
    edit_template = 'admin/team_edit.html'
    list_template = 'admin/team_list.html'

    def on_model_change(self, form, model, is_created):
        from config import IMAGE_FOLDER
        photo = request.files.get('photo_upload')
        if photo and photo.filename:
            name = save_upload(photo, IMAGE_FOLDER, {'.jpg', '.jpeg', '.png', '.webp'}, compress=True)
            if name:
                model.photo = name


class TrainingCardAdminView(AuthMixin, ModelView):
    """培训卡片管理"""
    column_list = ['id', 'title', 'tags', 'is_published', 'sort_order', 'updated_at']
    column_labels = {
        'title': '标题', 'description': '描述', 'image': '图片',
        'tags': '标签(逗号分隔)', 'sort_order': '排序', 'is_published': '已发布',
        'created_at': '创建时间', 'updated_at': '更新时间',
    }
    column_searchable_list = ['title', 'tags']
    column_filters = ['is_published']
    column_default_sort = ('sort_order', True)
    column_formatters = {
        'image': lambda v, c, m, p: Markup(f'<div style="width:100%;height:80px;overflow:hidden;border-radius:8px;"><img src="/images/{m.image}" style="width:100%;height:100%;object-fit:cover;display:block;"></div>') if m.image else '',
        'sort_order': lambda v, c, m, p: Markup(
            f'<div style="display:flex;align-items:center;gap:4px;">'
            f'<button class="sort-btn" onclick="moveTraining({m.id},\'up\',this);return false;" title="上移" style="width:28px;height:28px;border-radius:6px;background:#f3f4f6;border:1px solid #e5e7eb;cursor:pointer;font-size:0.75rem;display:flex;align-items:center;justify-content:center;">▲</button>'
            f'<button class="sort-btn" onclick="moveTraining({m.id},\'down\',this);return false;" title="下移" style="width:28px;height:28px;border-radius:6px;background:#f3f4f6;border:1px solid #e5e7eb;cursor:pointer;font-size:0.75rem;display:flex;align-items:center;justify-content:center;">▼</button>'
            f'</div>'
        ),
        'tags': lambda v, c, m, p: Markup(f'<div class="case-tags">{"".join(["<span class=\"case-tag\">" + t.strip() + "</span>" for t in m.tags.split(",") if t.strip()])}</div>') if m.tags else '',
    }
    page_size = 20
    column_editable_list = ['is_published']
    create_template = 'admin/training_card_create.html'
    edit_template = 'admin/training_card_edit.html'

    def on_model_change(self, form, model, is_created):
        """处理图片上传"""
        import os
        IMAGE_DIR = os.path.join(os.path.dirname(__file__), 'images')
        image = request.files.get('image_upload')
        if image and image.filename:
            name = save_upload(image, IMAGE_DIR, {'.jpg', '.jpeg', '.png', '.webp', '.gif', '.svg'}, compress=True)
            if name:
                model.image = name


class MediaFileAdminView(AuthMixin, ModelView):
    """媒体文件管理"""
    column_list = ['id', 'filename', 'file_type', 'file_size', 'uploaded_at']
    column_labels = {
        'filename': '文件名', 'filepath': '路径', 'file_type': '类型',
        'file_size': '大小', 'uploaded_at': '上传时间',
    }
    column_filters = ['file_type']
    can_create = False
    page_size = 30


class InquiryAdminView(AuthMixin, ModelView):
    """咨询管理"""
    column_list = ['id', 'name', 'company', 'phone', 'service_type', 'status', 'created_at']
    column_labels = {
        'name': '姓名', 'company': '公司名称', 'phone': '联系电话',
        'service_type': '服务类型', 'message': '需求描述', 'status': '状态',
        'created_at': '提交时间',
    }
    column_searchable_list = ['name', 'company', 'phone']
    column_filters = ['status', 'service_type']
    column_default_sort = ('created_at', True)
    column_formatters = {
        'status': lambda v, c, m, p: Markup(
            f'<span style="padding:4px 10px;border-radius:12px;font-size:0.78rem;font-weight:600;'
            f'{"background:rgba(245,158,11,0.1);color:#F59E0B;" if m.status == "pending" else ""}'
            f'{"background:rgba(59,130,246,0.1);color:#3B82F6;" if m.status == "contacted" else ""}'
            f'{"background:rgba(16,185,129,0.1);color:#10B981;" if m.status == "done" else ""}'
            f'">'
            f'{"待处理" if m.status == "pending" else "已联系" if m.status == "contacted" else "已完成"}'
            f'</span>'
        ),
        'message': lambda v, c, m, p: Markup(f'<span style="max-width:200px;display:inline-block;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;">{m.message[:50]}...</span>') if m.message else '',
    }
    column_editable_list = ['status']
    can_create = False
    can_delete = True
    page_size = 20


class EventCardAdminView(AuthMixin, ModelView):
    """文旅IP卡片管理"""
    column_list = ['id', 'title', 'tags', 'badge', 'is_published', 'sort_order']
    column_labels = {
        'title': '标题', 'description': '描述', 'image': '图片',
        'tags': '标签(逗号分隔)', 'badge': '标签文字', 'badge_color': '标签颜色', 'sort_order': '排序', 'is_published': '已发布',
    }
    column_searchable_list = ['title', 'tags']
    column_filters = ['is_published', 'badge_color']
    column_default_sort = ('sort_order', True)
    column_formatters = {
        'image': lambda v, c, m, p: Markup(f'<div style="width:100%;height:80px;overflow:hidden;border-radius:8px;"><img src="/images/{m.image}" style="width:100%;height:100%;object-fit:cover;display:block;"></div>') if m.image else '',
        'tags': lambda v, c, m, p: Markup(f'<div class="case-tags">{"".join(["<span class=\"case-tag\">" + t.strip() + "</span>" for t in m.tags.split(",") if t.strip()])}</div>') if m.tags else '',
        'sort_order': lambda v, c, m, p: Markup(
            f'<div style="display:flex;align-items:center;gap:4px;">'
            f'<button class="sort-btn" onclick="moveItem(\'event-cards\',{m.id},\'up\',this);return false;" title="上移" style="width:28px;height:28px;border-radius:6px;background:#f3f4f6;border:1px solid #e5e7eb;cursor:pointer;font-size:0.75rem;">▲</button>'
            f'<button class="sort-btn" onclick="moveItem(\'event-cards\',{m.id},\'down\',this);return false;" title="下移" style="width:28px;height:28px;border-radius:6px;background:#f3f4f6;border:1px solid #e5e7eb;cursor:pointer;font-size:0.75rem;">▼</button>'
            f'</div>'
        ),
    }
    column_editable_list = ['is_published']
    create_template = 'admin/card_create.html'
    edit_template = 'admin/card_edit.html'

    def on_model_change(self, form, model, is_created):
        import os
        IMAGE_DIR = os.path.join(os.path.dirname(__file__), 'images')
        image = request.files.get('image_upload')
        if image and image.filename:
            name = save_upload(image, IMAGE_DIR, {'.jpg', '.jpeg', '.png', '.webp', '.gif', '.svg'}, compress=True)
            if name:
                model.image = name


class AgentCardAdminView(AuthMixin, ModelView):
    """企业AI Agent卡片管理"""
    column_list = ['id', 'title', 'tags', 'is_published', 'sort_order']
    column_labels = {
        'title': '标题', 'description': '描述', 'image': '图片',
        'tags': '标签(逗号分隔)', 'sort_order': '排序', 'is_published': '已发布',
    }
    column_searchable_list = ['title', 'tags']
    column_filters = ['is_published']
    column_default_sort = ('sort_order', True)
    column_formatters = {
        'image': lambda v, c, m, p: Markup(f'<div style="width:100%;height:80px;overflow:hidden;border-radius:8px;"><img src="/images/{m.image}" style="width:100%;height:100%;object-fit:cover;display:block;"></div>') if m.image else '',
        'tags': lambda v, c, m, p: Markup(f'<div class="case-tags">{"".join(["<span class=\"case-tag\">" + t.strip() + "</span>" for t in m.tags.split(",") if t.strip()])}</div>') if m.tags else '',
        'sort_order': lambda v, c, m, p: Markup(
            f'<div style="display:flex;align-items:center;gap:4px;">'
            f'<button class="sort-btn" onclick="moveItem(\'agent-cards\',{m.id},\'up\',this);return false;" title="上移" style="width:28px;height:28px;border-radius:6px;background:#f3f4f6;border:1px solid #e5e7eb;cursor:pointer;font-size:0.75rem;">▲</button>'
            f'<button class="sort-btn" onclick="moveItem(\'agent-cards\',{m.id},\'down\',this);return false;" title="下移" style="width:28px;height:28px;border-radius:6px;background:#f3f4f6;border:1px solid #e5e7eb;cursor:pointer;font-size:0.75rem;">▼</button>'
            f'</div>'
        ),
    }
    column_editable_list = ['is_published']
    create_template = 'admin/card_create.html'
    edit_template = 'admin/card_edit.html'

    def on_model_change(self, form, model, is_created):
        import os
        IMAGE_DIR = os.path.join(os.path.dirname(__file__), 'images')
        image = request.files.get('image_upload')
        if image and image.filename:
            name = save_upload(image, IMAGE_DIR, {'.jpg', '.jpeg', '.png', '.webp', '.gif', '.svg'}, compress=True)
            if name:
                model.image = name


class StudioCardAdminView(AuthMixin, ModelView):
    """AI Studio功能卡片管理"""
    column_list = ['id', 'title', 'tags', 'is_published', 'sort_order']
    column_labels = {
        'title': '标题', 'description': '描述', 'image': '图片',
        'tags': '标签(逗号分隔)', 'sort_order': '排序', 'is_published': '已发布',
    }
    column_searchable_list = ['title', 'tags']
    column_filters = ['is_published']
    column_default_sort = ('sort_order', True)
    column_formatters = {
        'image': lambda v, c, m, p: Markup(f'<div style="width:100%;height:80px;overflow:hidden;border-radius:8px;"><img src="/images/{m.image}" style="width:100%;height:100%;object-fit:cover;display:block;"></div>') if m.image else '',
        'tags': lambda v, c, m, p: Markup(f'<div class="case-tags">{"".join(["<span class=\"case-tag\">" + t.strip() + "</span>" for t in m.tags.split(",") if t.strip()])}</div>') if m.tags else '',
        'sort_order': lambda v, c, m, p: Markup(
            f'<div style="display:flex;align-items:center;gap:4px;">'
            f'<button class="sort-btn" onclick="moveItem(\'studio-cards\',{m.id},\'up\',this);return false;" title="上移" style="width:28px;height:28px;border-radius:6px;background:#f3f4f6;border:1px solid #e5e7eb;cursor:pointer;font-size:0.75rem;">▲</button>'
            f'<button class="sort-btn" onclick="moveItem(\'studio-cards\',{m.id},\'down\',this);return false;" title="下移" style="width:28px;height:28px;border-radius:6px;background:#f3f4f6;border:1px solid #e5e7eb;cursor:pointer;font-size:0.75rem;">▼</button>'
            f'</div>'
        ),
    }
    column_editable_list = ['is_published']
    create_template = 'admin/card_create.html'
    edit_template = 'admin/card_edit.html'

    def on_model_change(self, form, model, is_created):
        import os
        IMAGE_DIR = os.path.join(os.path.dirname(__file__), 'images')
        image = request.files.get('image_upload')
        if image and image.filename:
            name = save_upload(image, IMAGE_DIR, {'.jpg', '.jpeg', '.png', '.webp', '.gif', '.svg'}, compress=True)
            if name:
                model.image = name


class PlatformCardAdminView(AuthMixin, ModelView):
    """AI Studio平台卡片管理"""
    column_list = ['id', 'title', 'tags', 'is_published', 'sort_order']
    column_labels = {
        'title': '标题', 'description': '描述', 'image': '图片',
        'tags': '标签(逗号分隔)', 'sort_order': '排序', 'is_published': '已发布',
    }
    column_searchable_list = ['title', 'tags']
    column_filters = ['is_published']
    column_default_sort = ('sort_order', True)
    column_formatters = {
        'image': lambda v, c, m, p: Markup(f'<div style="width:100%;height:80px;overflow:hidden;border-radius:8px;"><img src="/images/{m.image}" style="width:100%;height:100%;object-fit:cover;display:block;"></div>') if m.image else '',
        'tags': lambda v, c, m, p: Markup(f'<div class="case-tags">{"".join(["<span class=\"case-tag\">" + t.strip() + "</span>" for t in m.tags.split(",") if t.strip()])}</div>') if m.tags else '',
        'sort_order': lambda v, c, m, p: Markup(
            f'<div style="display:flex;align-items:center;gap:4px;">'
            f'<button class="sort-btn" onclick="moveItem(\'platform-cards\',{m.id},\'up\',this);return false;" title="上移" style="width:28px;height:28px;border-radius:6px;background:#f3f4f6;border:1px solid #e5e7eb;cursor:pointer;font-size:0.75rem;">▲</button>'
            f'<button class="sort-btn" onclick="moveItem(\'platform-cards\',{m.id},\'down\',this);return false;" title="下移" style="width:28px;height:28px;border-radius:6px;background:#f3f4f6;border:1px solid #e5e7eb;cursor:pointer;font-size:0.75rem;">▼</button>'
            f'</div>'
        ),
    }
    column_editable_list = ['is_published']
    create_template = 'admin/card_create.html'
    edit_template = 'admin/card_edit.html'

    def on_model_change(self, form, model, is_created):
        import os
        IMAGE_DIR = os.path.join(os.path.dirname(__file__), 'images')
        image = request.files.get('image_upload')
        if image and image.filename:
            name = save_upload(image, IMAGE_DIR, {'.jpg', '.jpeg', '.png', '.webp', '.gif', '.svg'}, compress=True)
            if name:
                model.image = name
