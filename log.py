from .enums import DhpmLogType, DhpmRetCode, OperationStatus, RETCODE_METADATA

class LogList:

    def __init__(self, max_log_count=0):

        self.max_log_count = max_log_count
        self.log_list = []

    def log(self, log_str):

        self.log_list.append(log_str)

        if self.max_log_count > 0 and len(self.log_list) > self.max_log_count:
            del self.log_list[0]

    def __iter__(self):
        return self.log_list.__iter__()

    def __len__(self):
        return len(self.log_list)

    def __getitem__(self, key):
        return self.log_list[key]

class LogManager:

    OPSTATUS_PRIORITY = [OperationStatus.ERROR, OperationStatus.WARNING]

    LOGTYPE_TO_OPSTATUS = {
        DhpmLogType.ERROR : OperationStatus.ERROR,
        DhpmLogType.WARNING : OperationStatus.WARNING,
        DhpmLogType.INFO : OperationStatus.CORRECT
    }

    def __init__(self, post_log_op=None):

        self.post_log_op = post_log_op
        self.engine_retcode = None

        self.log_lists = {
            DhpmLogType.STATUS :     LogList(max_log_count=0),
            DhpmLogType.INFO :       LogList(max_log_count=5),
            DhpmLogType.WARNING :    LogList(max_log_count=0),
            DhpmLogType.ERROR :      LogList(max_log_count=0),
            DhpmLogType.HINT :       LogList(max_log_count=0)
        }
     
    def log_engine_retcode(self, engine_retcode):
        self.engine_retcode = engine_retcode


    def log_list(self, log_type):

        log_list = self.log_lists.get(log_type, None)
        if log_list is None:
            raise RuntimeError('Unexpected log type')

        return log_list

    def log(self, log_type, log_str):

        self.log_list(log_type).log(log_str)

        if self.post_log_op is not None:
            post_log_op = self.post_log_op
            post_log_op(log_type, log_str)
        
    def type_logged(self, log_type):

        return len(self.log_list(log_type)) > 0

    def operation_status(self):

        retcode_op_status = RETCODE_METADATA[self.engine_retcode].op_status if self.engine_retcode is not None else None

        for op_status in self.OPSTATUS_PRIORITY:
            if retcode_op_status is not None and retcode_op_status == op_status:
                return op_status

            for log_type, log_op_status in self.LOGTYPE_TO_OPSTATUS.items():
                if op_status != log_op_status:
                    continue
                if self.type_logged(log_type):
                    return op_status

        return OperationStatus.CORRECT

    def last_log(self, log_type):
        log_list = self.log_list(log_type)
        return log_list[-1] if len(log_list) > 0 else None

