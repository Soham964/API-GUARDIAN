from db import db
from models.contract import Contract


def create_contract(endpoint: str, method: str, request_schema: dict, response_schema: dict) -> dict:
    contract = Contract(
        endpoint=endpoint,
        method=method.upper(),
        request_schema=request_schema,
        response_schema=response_schema,
    )
    db.session.add(contract)
    db.session.commit()
    return contract.to_dict()


def get_all_contracts() -> list[dict]:
    contracts = Contract.query.order_by(Contract.created_at.desc()).all()
    return [c.to_dict() for c in contracts]


def get_contract(endpoint: str, method: str) -> Contract | None:
    return Contract.query.filter_by(
        endpoint=endpoint,
        method=method.upper()
    ).first()


def delete_contract(contract_id: int) -> bool:
    contract = db.session.get(Contract, contract_id)
    if not contract:
        return False
    db.session.delete(contract)
    db.session.commit()
    return True
