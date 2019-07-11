import datetime
from collections import defaultdict
from dataclasses import dataclass
from typing import NewType, Tuple, Union, List, Dict, Any, Set
from bson import ObjectId
from networkx import DiGraph

from frozendict import ComparableDict

Trial = NewType("Trial", dict)
ParentPath = NewType("ParentPath", Tuple[Union[str, int]])
MatchClause = NewType("MatchClause", List[Dict[str, Any]])
MatchTree = NewType("MatchTree", DiGraph)
MultiCollectionQuery = NewType("MultiCollectionQuery", dict)
NodeID = NewType("NodeID", int)
MatchClauseLevel = NewType("MatchClauseLevel", str)
MongoQueryResult = NewType("MongoQueryResult", Dict[str, Any])
MongoQuery = NewType("MongoQuery", Dict[str, Any])
GenomicID = NewType("GenomicID", ObjectId)
ClinicalID = NewType("ClinicalID", ObjectId)
Collection = NewType("Collection", str)


class PoisonPill(object):
    pass


@dataclass
class MatchCriteria:
    criteria: Dict
    depth: int


@dataclass
class MatchCriterion:
    criteria_list: List[MatchCriteria]

    def hash(self) -> str:
        return ComparableDict({"query": [criteria.criteria for criteria in self.criteria_list]}).hash()


@dataclass
class QueryPart:
    query: Dict
    negate: bool
    render: bool

    def hash(self) -> str:
        return ComparableDict(self.query).hash()


@dataclass
class QueryNode:
    query_level: str
    query_depth: int
    query_parts: List[QueryPart]
    exclusion: Union[None, bool]

    def hash(self) -> str:
        return ComparableDict({
            "_tmp1": [query_part.hash()
                      for query_part in self.query_parts],
            '_tmp2': self.exclusion
        }).hash()

    def extract_raw_query(self):
        return {
            key: value
            for query_part in self.query_parts
            for key, value in query_part.query.items()
            if query_part.render
        }


@dataclass
class MultiCollectionQuery:
    genomic: List[QueryNode]
    clinical: List[QueryNode]


class RunLog:
    protocol_no: str
    clinical_id: ObjectId
    marked_available: list
    inserted: list
    marked_disabled: list
    _created: datetime.datetime

    def __init__(self, protocol_no: str, clinical_id: ObjectId):
        self.protocol_no = protocol_no
        self.clinical_id = clinical_id
        self.marked_available = list()
        self.inserted = list()
        self.marked_disabled = list()
        self._created = datetime.datetime.now()


@dataclass
class MatchClauseData:
    match_clause: MatchClause
    internal_id: str
    code: str
    coordinating_center: str
    is_suspended: bool
    status: str
    parent_path: ParentPath
    match_clause_level: MatchClauseLevel
    match_clause_additional_attributes: dict
    protocol_no: str


@dataclass
class GenomicMatchReason:
    query_node: QueryNode
    width: int
    clinical_id: ClinicalID
    genomic_id: Union[GenomicID, None]

    reason_name = 'genomic'


@dataclass
class ClinicalMatchReason:
    query_node: QueryNode
    clinical_id: ClinicalID
    reason_name = 'clinical'


MatchReason = NewType("MatchReason", Union[GenomicMatchReason, ClinicalMatchReason])


@dataclass
class TrialMatch:
    trial: Trial
    match_clause_data: MatchClauseData
    match_criterion: MatchCriterion
    multi_collection_query: MultiCollectionQuery
    match_reason: MatchReason


class Cache(object):
    docs: Dict[ObjectId, MongoQueryResult]
    ids: dict
    run_log: dict

    def __init__(self):
        self.docs = dict()
        self.ids = dict()
        self.run_log = dict()


class RunLogCache(object):
    trials: Dict[str, datetime.datetime]
    clinical: Dict[str, datetime.datetime]
    genomic: Dict[str, datetime.datetime]
    clinical_protocol_runs: Dict[ClinicalID, Dict[str, datetime.datetime]]

    def __init__(self):
        self.trials = dict()
        self.clinical = dict()
        self.genomic = dict()
        self.clinical_protocol_runs = defaultdict(lambda: defaultdict(lambda: None))


@dataclass
class QueryTask:
    trial: Trial
    match_clause_data: MatchClauseData
    match_path: MatchCriterion
    query: MultiCollectionQuery
    clinical_ids: Set[ClinicalID]


@dataclass
class UpdateTask:
    ops: List
    protocol_no: str


@dataclass
class RunLogUpdateTask:
    run_log: RunLog


@dataclass
class Secrets:
    HOST: str
    PORT: int
    DB: str
    AUTH_DB: str
    RO_USERNAME: str
    RO_PASSWORD: str
    RW_USERNAME: str
    RW_PASSWORD: str
    REPLICASET: str
    MAX_POOL_SIZE: str
