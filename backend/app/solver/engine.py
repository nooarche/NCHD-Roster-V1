from .interfaces import DatedWindow, ActivityProvider, AssignmentSink
from .calendar import merge_baseline
from .allocations import candidates_day_call, candidates_night_call
from .constraints import forbid_rest_on_tag

class Solver:
    def __init__(self, acts: ActivityProvider, sink: AssignmentSink):
        self.acts = acts
        self.sink = sink

    def preview_month(self, post_id: int, month: int, year: int) -> dict:
        acts = list(self.acts.windows_for_post(post_id, month, year))
        baseline = merge_baseline(core=[], acts=acts)

        day = candidates_day_call(baseline)
        night = candidates_night_call(baseline)

        rest_windows: list[DatedWindow] = []
        forbidden = {"clinic","opd"}
        if forbid_rest_on_tag(rest_windows, acts, forbidden):
            night = []

        return {
            "baseline": [w.__dict__ for w in baseline],
            "proposed_day": [w.__dict__ for w in day],
            "proposed_night": [w.__dict__ for w in night],
        }
