import contextvars

current_run_id = contextvars.ContextVar('current_run_id', default=None)
current_delegation_depth = contextvars.ContextVar('current_delegation_depth', default=0)
