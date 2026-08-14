from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from enum import Enum


class EconomicAmountRole(str, Enum):
    PAID = "paid"
    OBLIGATED = "obligated"
    AUTHORIZED = "authorized"
    CEILING = "ceiling"
    VALUED = "valued"
    OUTSTANDING = "outstanding"
    EXPOSED = "exposed"
    ESTIMATED = "estimated"


class EconomicRelationKind(str, Enum):
    OWNERSHIP = "ownership"
    CONTROL = "control"
    CONTRACT = "contract"
    AWARD = "award"
    OBLIGATION = "obligation"
    TRANSFER = "transfer"
    LOAN = "loan"
    LIABILITY = "liability"
    SECURITY_INTEREST = "security_interest"
    SANCTION = "sanction"
    VALUATION = "valuation"
    EXPOSURE = "exposure"
    TRADE_FLOW = "trade_flow"
    PROPERTY_INTEREST = "property_interest"
    INSOLVENCY_STATE = "insolvency_state"


@dataclass(frozen=True, slots=True)
class EconomicAmount:
    value: Decimal
    currency: str
    role: EconomicAmountRole
    as_of: str | None = None
    basis: str | None = None

    def __post_init__(self) -> None:
        if not self.currency.strip():
            raise ValueError("currency must be a non-empty string")
        if not self.value.is_finite():
            raise ValueError("economic amount must be finite")


@dataclass(frozen=True, slots=True)
class EconomicRelation:
    relation_id: str
    kind: EconomicRelationKind
    subject_ref: str
    object_ref: str | None
    amount: EconomicAmount | None = None
    basis_record_refs: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if not self.relation_id.strip():
            raise ValueError("relation_id must be a non-empty string")
        if not self.subject_ref.strip():
            raise ValueError("subject_ref must be a non-empty string")

        if self.kind is EconomicRelationKind.TRANSFER:
            if self.amount is None or self.amount.role is not EconomicAmountRole.PAID:
                raise ValueError("transfer relation requires an amount with PAID semantics")
        if self.kind is EconomicRelationKind.OBLIGATION:
            if self.amount is None or self.amount.role is not EconomicAmountRole.OBLIGATED:
                raise ValueError(
                    "obligation relation requires an amount with OBLIGATED semantics"
                )
        if self.kind is EconomicRelationKind.VALUATION and self.amount is not None:
            if self.amount.role not in {
                EconomicAmountRole.VALUED,
                EconomicAmountRole.ESTIMATED,
            }:
                raise ValueError(
                    "valuation relation requires VALUED or ESTIMATED amount semantics"
                )
        if self.kind is EconomicRelationKind.EXPOSURE and self.amount is not None:
            if self.amount.role is not EconomicAmountRole.EXPOSED:
                raise ValueError("exposure relation requires EXPOSED amount semantics")
