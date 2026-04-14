from db import db
from datetime import datetime, timezone

VALID_DIRECTIONS = {"request", "response"}


class ValidationLog(db.Model):
    __tablename__ = "logs"

    id = db.Column(db.Integer, primary_key=True)
    endpoint = db.Column(db.String(255), nullable=False)
    method = db.Column(db.String(10), nullable=False, default="UNKNOWN")
    error_message = db.Column(db.Text, nullable=False)
    direction = db.Column(db.String(10), nullable=False)  # "request" or "response"
    timestamp = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    def to_dict(self):
        return {
            "id": self.id,
            "endpoint": self.endpoint,
            "method": self.method,
            "error_message": self.error_message,
            "direction": self.direction,
            "timestamp": self.timestamp.isoformat(),
        }
