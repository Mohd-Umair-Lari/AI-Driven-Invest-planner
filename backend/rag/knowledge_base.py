
from typing import List, Tuple

KNOWLEDGE_CHUNKS: List[Tuple[str, str]] = [

    ("sip_basics", ),

    ("mutual_fund_categories", ),

    ("sip_corpus_calculation", ),

    ("tax_80c", ),

    ("new_tax_regime", ),

    ("tax_80d_nps", ),

    ("emergency_fund", ),

    ("debt_management", ),

    ("asset_allocation", ),

    ("ppf_nps", ),

    ("term_insurance", ),

    ("goal_planning", ),

    ("50_30_20_rule", ),

    ("inflation_fd", ),
]

def get_all_chunks() -> List[Tuple[str, str]]:

    return [(doc_id, text.strip()) for doc_id, text in KNOWLEDGE_CHUNKS]
