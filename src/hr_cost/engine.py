from datetime import date
from typing import List
from .models import Inputs, Holiday


class CalculationEngine:
    """
    Engine chịu trách nhiệm tính toán toàn bộ logic theo spec.md
    Không phụ thuộc Streamlit.
    Không phụ thuộc UI.
    """

    def __init__(self, inputs: Inputs, holidays: List[Holiday]):
        self.inputs = inputs
        self.holidays = holidays

    def calculate_year(self):
        """
        Return:
            List[dict]  # mỗi dict là 1 tháng
        """
        raise NotImplementedError("Engine logic chưa được implement.")