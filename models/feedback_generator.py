from .feature_extractor import FeatureExtractor
class QualityFeedback:
   """Generate detailed feedback on essay quality"""
   
   def __init__(self):
       self.feature_extractor = FeatureExtractor()
       
   def get_feedback(self, essay):
       """Generate detailed feedback on different aspects"""
       feedback = {}
       
       readability = self.feature_extractor.get_readability_metrics(essay)
       grammar = self.feature_extractor.get_grammar_metrics(essay)
       coherence = self.feature_extractor.get_coherence_metrics(essay)
       argument = self.feature_extractor.get_argument_metrics(essay)
       
       # Get feedback for each aspect
       read_fb = self._get_readability_feedback(readability)
       gram_fb = self._get_grammar_feedback(grammar) 
       coh_fb = self._get_coherence_feedback(coherence)
       arg_fb = self._get_argument_feedback(argument)
       
       # Only include categories that have feedback
       if read_fb: feedback['readability'] = read_fb
       if gram_fb: feedback['grammar'] = gram_fb
       if coh_fb: feedback['coherence'] = coh_fb
       if arg_fb: feedback['argumentation'] = arg_fb
       
       return feedback
   
   def _get_readability_feedback(self, metrics):
       feedback = []
       if metrics['avg_sent_length'] > 35:
           feedback.append("Try breaking longer sentences into shorter ones to improve clarity")
       if metrics['avg_word_length'] > 6:
           feedback.append("Consider using simpler words in some places to make your writing clearer")
       if metrics['flesch_score'] < 0.3:
           feedback.append("Make your writing more engaging by varying your sentence structure")
       return feedback
   
   def _get_grammar_feedback(self, metrics):
       feedback = []
       if metrics['spelling_errors'] > 3:
           feedback.append(f"Review your essay for spelling errors - found approximately {metrics['spelling_errors']} potential mistakes")
       if metrics['grammar_errors'] > 2:
           feedback.append("Check your grammar, focusing on subject-verb agreement and proper tense usage")
       if metrics['style_errors'] > 2:
           feedback.append("Review your punctuation and capitalization")
       return feedback

   def _get_coherence_feedback(self, metrics):
       feedback = []
       if metrics['vocab_richness'] < 0.4:
           feedback.append("Try using more varied vocabulary to express your ideas")
       if metrics['unique_sent_starts'] < 5:
           feedback.append("Start your sentences in different ways to make your writing more interesting")
       return feedback

   def _get_argument_feedback(self, metrics):
       feedback = []
       if metrics['discourse_markers'] < 3:
           feedback.append("Add transition words (like 'however', 'therefore', 'moreover') to connect your ideas better")
       if metrics['topic_development'] < 0.3:
           feedback.append("Develop your ideas further by adding more specific examples and details")
       return feedback