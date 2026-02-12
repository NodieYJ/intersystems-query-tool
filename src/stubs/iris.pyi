"""
iris 类型存根文件
Intersystems IRIS Python 驱动
用于 LSP 类型检查
"""

from typing import Any, Optional, List, Dict, Tuple, Union

class Connection:
    """数据库连接"""
    def close(self) -> None: ...
    def commit(self) -> None: ...
    def rollback(self) -> None: ...
    def cursor(self) -> 'Cursor': ...
    def is_open(self) -> bool: ...

class Cursor:
    """游标"""
    def execute(self, operation: str, parameters: Optional[Tuple] = None) -> None: ...
    def executemany(self, operation: str, seq_of_parameters: List[Tuple]) -> None: ...
    def fetchone(self) -> Optional[Tuple]: ...
    def fetchall(self) -> List[Tuple]: ...
    def fetchmany(self, size: int = 1) -> List[Tuple]: ...
    def close(self) -> None: ...
    @property
    def description(self) -> List[Tuple[str, Any, int, int, int, int, bool]]: ...
    @property
    def rowcount(self) -> int: ...

def connect(
    hostname: str = "localhost",
    port: int = 1972,
    namespace: str = "USER",
    username: str = "_SYSTEM",
    password: str = "SYS",
    timeout: int = 10,
    sharedmemory: bool = True,
    **kwargs: Any
) -> Connection: ...

# dbapi 模块
class dbapi:
    """DB API 2.0 接口"""
    apilevel: str = "2.0"
    threadsafety: int = 1
    paramstyle: str = "qmark"
    
    @staticmethod
    def connect(
        hostname: str = "localhost",
        port: int = 1972,
        namespace: str = "USER",
        username: str = "_SYSTEM",
        password: str = "SYS",
        timeout: int = 10,
        **kwargs: Any
    ) -> Connection: ...
    
    Warning: type = Exception
    Error: type = Exception
    InterfaceError: type = Exception
    DatabaseError: type = Exception
    DataError: type = Exception
    OperationalError: type = Exception
    IntegrityError: type = Exception
    InternalError: type = Exception
    ProgrammingError: type = Exception
    NotSupportedError: type = Exception
