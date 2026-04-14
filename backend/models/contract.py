from db import db
from datetime import datetime, timezone


class Contract(db.Model):
    __tablename__ = "contracts"

    id = db.Column(db.Integer, primary_key=True)
    endpoint = db.Column(db.String(255), nullable=False)
    method = db.Column(db.String(10), nullable=False)
    request_schema = db.Column(db.JSON, nullable=False)
    response_schema = db.Column(db.JSON, nullable=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    def to_dict(self):
        return {
            "id": self.id,
            "endpoint": self.endpoint,
            "method": self.method.upper(),
            "request_schema": self.request_schema,
            "response_schema": self.response_schema,
            "created_at": self.created_at.isoformat(),
        }
