
def key_release_event(event):

    return (event.type not in {'MIDDLEMOUSE', 'INBETWEEN_MOUSEMOVE', 'MOUSEMOVE', 'TIMER', 'TIMER_REPORT', 'WHEELDOWNMOUSE', 'WHEELUPMOUSE'} and event.value == 'PRESS')

class DefaultFinishConditionMixin:

    def operation_done_finish_condition(self, event):

        return key_release_event(event)

    def operation_done_hint(self):

        return 'Pack Done'
