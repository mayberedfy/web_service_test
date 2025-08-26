from flask import Blueprint, request, jsonify, g
from src.extensions import db
from src.models.admin_user_model import User
from src.auth.decorators import require_role, require_permission, require_auth
import uuid
import logging
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

user_mgmt_bp = Blueprint('user_mgmt_bp', __name__, url_prefix='/api/users')













@user_mgmt_bp.route('/<user_id>', methods=['PUT'])
@require_auth()
@require_role('admin')
def update_user(user_id):
    """管理员更新用户信息"""
    try:
        data = request.get_json() or {}
        current_user = g.current_user
        
        # 获取要更新的目标用户
        target_user = User.query.get(user_id)
        if not target_user:
            return jsonify({'error': 'User not found'}), 404
        
        # 防止管理员修改自己的关键状态（可选安全检查）
        if target_user.id == current_user.id:
            # 管理员不能禁用自己或降级自己的角色
            if 'is_active' in data and not data['is_active']:
                return jsonify({'error': 'Cannot deactivate your own account'}), 400
            if 'role' in data and data['role'] != 'admin':
                return jsonify({'error': 'Cannot change your own admin role'}), 400
        
        # 记录更新前的状态（用于日志）
        old_values = {
            'username': target_user.username,
            'email': target_user.email,
            'role': target_user.role,
            'is_active': target_user.is_active,
            'is_verified': target_user.is_verified
        }
        
        # 可更新的字段列表
        updatable_fields = {
            'username': str,
            'email': str,
            'role': str,
            'is_active': bool,
            'is_verified': bool,
            'permissions': list
        }
        
        changes_made = []
        
        # 逐字段验证并更新
        for field, field_type in updatable_fields.items():
            if field in data:
                new_value = data[field]
                
                # 类型验证
                if not isinstance(new_value, field_type):
                    return jsonify({'error': f'Invalid type for {field}'}), 400
                
                # 特殊字段验证
                if field == 'username':
                    new_value = new_value.strip()
                    if not new_value:
                        return jsonify({'error': 'Username cannot be empty'}), 400
                    if len(new_value) < 3 or len(new_value) > 50:
                        return jsonify({'error': 'Username must be 3-50 characters'}), 400
                    
                    # 检查用户名唯一性（如果改变了用户名）
                    if new_value != target_user.username:
                        existing_user = User.query.filter_by(username=new_value).first()
                        if existing_user:
                            return jsonify({'error': 'Username already exists'}), 409
                
                elif field == 'email':
                    if new_value:  # 允许空邮箱
                        new_value = new_value.strip().lower()
                        # 简单邮箱格式验证
                        import re
                        if not re.match(r'^[^@]+@[^@]+\.[^@]+$', new_value):
                            return jsonify({'error': 'Invalid email format'}), 400
                        
                        # 检查邮箱唯一性（如果改变了邮箱）
                        if new_value != target_user.email:
                            existing_user = User.query.filter_by(email=new_value).first()
                            if existing_user:
                                return jsonify({'error': 'Email already exists'}), 409
                
                elif field == 'role':
                    valid_roles = ['admin', 'manager', 'operator', 'viewer']
                    if new_value not in valid_roles:
                        return jsonify({'error': f'Invalid role. Must be one of: {", ".join(valid_roles)}'}), 400
                
                elif field == 'permissions':
                    # 验证权限列表格式
                    if not isinstance(new_value, list):
                        return jsonify({'error': 'Permissions must be a list'}), 400
                    # 可以在这里添加具体的权限验证逻辑
                    valid_permissions = ['upload', 'read', 'write', 'delete', 'manage_users', 'manage_api_keys', 'view_stats']
                    for perm in new_value:
                        if not isinstance(perm, str):
                            return jsonify({'error': 'Each permission must be a string'}), 400
                        # 可选：验证权限是否在允许列表中
                        # if perm not in valid_permissions and perm != '*':
                        #     return jsonify({'error': f'Invalid permission: {perm}'}), 400
                
                # 记录变更
                old_value = getattr(target_user, field)
                if old_value != new_value:
                    setattr(target_user, field, new_value)
                    changes_made.append({
                        'field': field,
                        'old_value': old_value,
                        'new_value': new_value
                    })
        
        if not changes_made:
            return jsonify({'message': 'No changes made', 'user': target_user.to_dict()}), 200
        
        # 更新修改者和时间戳
        target_user.update_time = datetime.now(timezone.utc)
        # 如果你的模型有 updated_by 字段，可以设置
        # target_user.updated_by = current_user.id
        
        db.session.commit()
        
        # 记录详细的操作日志
        changes_summary = '; '.join([f"{c['field']}: {c['old_value']} -> {c['new_value']}" for c in changes_made])
        logger.info(f"User updated by admin {current_user.username}: "
                   f"target_user={target_user.username}, changes=({changes_summary})")
        
        return jsonify({
            'message': 'User updated successfully',
            'user': target_user.to_dict(),
            'changes_made': changes_made
        })
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Update user error: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500








@user_mgmt_bp.route('', methods=['GET'])
@require_role(['admin', 'manager'])
def list_users():
    """获取用户列表（管理员和经理可查看）"""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        role_filter = request.args.get('role')
        active_filter = request.args.get('is_active')
        search = request.args.get('search', '').strip()
        
        # 构建查询
        query = User.query
        
        # 角色过滤
        if role_filter:
            query = query.filter(User.role == role_filter)
        
        # 活跃状态过滤
        if active_filter is not None:
            is_active = active_filter.lower() in ['true', '1', 'yes']
            query = query.filter(User.is_active == is_active)
        
        # 搜索过滤（用户名或邮箱）
        if search:
            query = query.filter(
                db.or_(
                    User.username.like(f'%{search}%'),
                    User.email.like(f'%{search}%')
                )
            )
        
        # 分页
        pagination = query.order_by(User.create_time.desc()).paginate(
            page=page, per_page=per_page, error_out=False
        )
        
        return jsonify({
            'users': [user.to_dict() for user in pagination.items],
            'pagination': {
                'page': page,
                'per_page': per_page,
                'total': pagination.total,
                'pages': pagination.pages,
                'has_next': pagination.has_next,
                'has_prev': pagination.has_prev
            }
        })
        
    except Exception as e:
        logger.error(f"List users error: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500








@user_mgmt_bp.route('', methods=['POST'])
@require_role('admin')
def create_user():
    """创建新用户"""
    try:
        data = request.get_json() or {}
        username = data.get('username', '').strip()
        email = data.get('email', '').strip()
        password = data.get('password')
        role = data.get('role', 'viewer')
        permissions = data.get('permissions', [])
        
        if not username or not password:
            return jsonify({'error': 'Username and password required'}), 400
        
        # 检查用户名是否已存在
        if User.query.filter_by(username=username).first():
            return jsonify({'error': 'Username already exists'}), 400
        
        # 检查邮箱是否已存在
        if email and User.query.filter_by(email=email).first():
            return jsonify({'error': 'Email already exists'}), 400
        
        # 创建新用户
        user = User(
            username=username,
            email=email if email else None,
            role=role,
            permissions=permissions,
            is_active=True,
            is_verified=True
        )
        user.set_password(password)
        
        db.session.add(user)
        db.session.commit()
        
        logger.info(f"User created: {username}")
        return jsonify({
            'message': 'User created successfully',
            'user': user.to_dict()
        }), 201
        
    except Exception as e:
        logger.error(f"Create user error: {str(e)}")
        db.session.rollback()
        return jsonify({'error': 'Internal server error'}), 500






@user_mgmt_bp.route('/<user_id>', methods=['GET'])
@require_auth()
@require_role(['admin', 'manager'])
def get_user_detail(user_id):
    """获取用户详细信息"""
    try:
        user = User.query.get(user_id)
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        # 可以返回比 to_dict() 更详细的信息
        user_detail = user.to_dict()
        user_detail.update({
            'last_login_formatted': user.last_login.strftime('%Y-%m-%d %H:%M:%S') if user.last_login else None,
            'create_time_formatted': user.create_time.strftime('%Y-%m-%d %H:%M:%S') if user.create_time else None,
            'is_locked': user.locked_until and datetime.now(timezone.utc) < user.locked_until,
            'failed_attempts': int(user.failed_login_attempts)
        })
        
        return jsonify({'user': user_detail})
        
    except Exception as e:
        logger.error(f"Get user detail error: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500