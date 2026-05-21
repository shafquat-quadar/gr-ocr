from __future__ import annotations

from abc import ABC, abstractmethod


class SAPAdapter(ABC):

    @abstractmethod
    def get_purchase_order(self, po_number: str) -> dict:
        pass

    @abstractmethod
    def post_goods_receipt(self, payload: dict) -> dict:
        pass

    @abstractmethod
    def get_material_document(self, material_document: str, year: str) -> dict:
        pass

    @abstractmethod
    def ping(self) -> dict:
        pass
