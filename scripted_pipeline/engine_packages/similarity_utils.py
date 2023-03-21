from scripted_pipeline import GenericScenario
from dhpm_core import SimilarityParams

class SimilarityScenario(GenericScenario):

    def pre_run(self):

        self.simi_params = SimilarityParams()
        self.simi_params.precision = self.cx.params['precision']
        self.simi_params.threshold = self.cx.params['threshold']
        self.simi_params.adjust_scale = self.cx.params['adjust_scale']
        self.simi_params.check_vertices = self.cx.params['check_vertices']
        self.simi_params.correct_vertices = self.cx.params['correct_vertices']
        self.simi_params.vertex_threshold = self.cx.params['vertex_threshold']

