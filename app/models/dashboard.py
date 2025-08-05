from app import db
from datetime import datetime
from decimal import Decimal
import json


class DashboardMetrics(db.Model):
    """Model for caching frequently calculated dashboard metrics for performance"""
    __tablename__ = 'dashboard_metrics'

    id = db.Column(db.Integer, primary_key=True)
    metric_key = db.Column(db.String(50), unique=True, nullable=False)  # e.g., 'total_customers', 'total_disbursed'
    metric_value = db.Column(db.Numeric(20, 2), nullable=False)
    metric_data = db.Column(db.Text)  # JSON data for complex metrics
    last_updated = db.Column(db.DateTime, default=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True)

    def __repr__(self):
        return f'<DashboardMetrics {self.metric_key}: {self.metric_value}>'

    def to_dict(self):
        return {
            'metric_key': self.metric_key,
            'metric_value': float(self.metric_value),
            'metric_data': json.loads(self.metric_data) if self.metric_data else None,
            'last_updated': self.last_updated.isoformat() if self.last_updated else None
        }

    @classmethod
    def update_metric(cls, key, value, data=None):
        """Update or create a metric value"""
        metric = cls.query.filter_by(metric_key=key).first()
        if metric:
            metric.metric_value = value
            metric.metric_data = json.dumps(data) if data else None
            metric.last_updated = datetime.utcnow()
        else:
            metric = cls(
                metric_key=key,
                metric_value=value,
                metric_data=json.dumps(data) if data else None
            )
            db.session.add(metric)
        db.session.commit()
        return metric


class RealtimeData(db.Model):
    """Model for tracking real-time data updates and notifications"""
    __tablename__ = 'realtime_data'

    id = db.Column(db.Integer, primary_key=True)
    data_type = db.Column(db.String(50), nullable=False)  # 'loan_created', 'payment_received', etc.
    data_content = db.Column(db.Text, nullable=False)  # JSON data
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    processed = db.Column(db.Boolean, default=False)
    priority = db.Column(db.String(20), default='normal')  # low, normal, high, critical

    def __repr__(self):
        return f'<RealtimeData {self.data_type}: {self.priority}>'

    def to_dict(self):
        return {
            'id': self.id,
            'data_type': self.data_type,
            'data_content': json.loads(self.data_content),
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'priority': self.priority
        }


class UserPreferences(db.Model):
    """Model for storing user-specific dashboard preferences"""
    __tablename__ = 'user_preferences'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    preference_key = db.Column(db.String(50), nullable=False)
    preference_value = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (db.UniqueConstraint('user_id', 'preference_key'),)

    def __repr__(self):
        return f'<UserPreferences {self.user_id}: {self.preference_key}>'

    def to_dict(self):
        return {
            'preference_key': self.preference_key,
            'preference_value': json.loads(self.preference_value),
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

    @classmethod
    def set_preference(cls, user_id, key, value):
        """Set or update a user preference"""
        pref = cls.query.filter_by(user_id=user_id, preference_key=key).first()
        if pref:
            pref.preference_value = json.dumps(value)
            pref.updated_at = datetime.utcnow()
        else:
            pref = cls(
                user_id=user_id,
                preference_key=key,
                preference_value=json.dumps(value)
            )
            db.session.add(pref)
        db.session.commit()
        return pref


class AlertSettings(db.Model):
    """Model for user notification and alert preferences"""
    __tablename__ = 'alert_settings'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    alert_type = db.Column(db.String(50), nullable=False)  # 'overdue_payment', 'new_loan', etc.
    is_enabled = db.Column(db.Boolean, default=True)
    threshold_value = db.Column(db.Numeric(15, 2))  # For amount-based alerts
    notification_method = db.Column(db.String(20), default='dashboard')  # dashboard, email, sms
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (db.UniqueConstraint('user_id', 'alert_type'),)

    def __repr__(self):
        return f'<AlertSettings {self.user_id}: {self.alert_type}>'

    def to_dict(self):
        return {
            'alert_type': self.alert_type,
            'is_enabled': self.is_enabled,
            'threshold_value': float(self.threshold_value) if self.threshold_value else None,
            'notification_method': self.notification_method,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }


class DashboardActivity(db.Model):
    """Model for tracking recent dashboard activities and user actions"""
    __tablename__ = 'dashboard_activities'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    activity_type = db.Column(db.String(50), nullable=False)  # 'view_customer', 'create_loan', etc.
    activity_description = db.Column(db.String(200), nullable=False)
    related_entity_type = db.Column(db.String(20))  # 'customer', 'loan', 'payment'
    related_entity_id = db.Column(db.Integer)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<DashboardActivity {self.user_id}: {self.activity_type}>'

    def to_dict(self):
        return {
            'id': self.id,
            'activity_type': self.activity_type,
            'activity_description': self.activity_description,
            'related_entity_type': self.related_entity_type,
            'related_entity_id': self.related_entity_id,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

    @classmethod
    def log_activity(cls, user_id, activity_type, description, entity_type=None, entity_id=None):
        """Log a new dashboard activity"""
        activity = cls(
            user_id=user_id,
            activity_type=activity_type,
            activity_description=description,
            related_entity_type=entity_type,
            related_entity_id=entity_id
        )
        db.session.add(activity)
        db.session.commit()
        return activity