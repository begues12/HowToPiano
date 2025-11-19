"""
Performance Evaluator for Piano Practice
Evaluates user performance based on 5 criteria:
1. Note Accuracy
2. Rhythmic Precision (Timing)
3. Fluency/Continuity
4. Dynamics (Volume)
5. Expression/Articulation
"""

import time
from typing import List, Dict, Tuple

class PerformanceEvaluator:
    def __init__(self):
        # Expected notes from MIDI file
        self.expected_notes = []  # List of {time, note, velocity, duration}
        
        # Actual notes played by user
        self.played_notes = []  # List of {time, note, velocity, duration}
        
        # Tracking
        self.start_time = None
        self.end_time = None
        self.active_notes = {}  # note -> start_time
        
        # Mistakes tracking
        self.wrong_notes = []  # Notes played incorrectly
        self.missed_notes = []  # Expected notes not played
        self.extra_notes = []  # Notes played but not expected
        self.timing_errors = []  # Notes played too early/late
        self.pauses = []  # Long pauses detected
        
    def load_expected_notes(self, midi_events):
        """Load expected notes from MIDI file events"""
        self.expected_notes = []
        note_starts = {}  # note -> start_time
        
        for evt in midi_events:
            msg = evt['msg']
            time_val = evt['time']
            
            if msg.type == 'note_on' and msg.velocity > 0:
                note_starts[msg.note] = {
                    'time': time_val,
                    'velocity': msg.velocity
                }
            elif msg.type == 'note_off' or (msg.type == 'note_on' and msg.velocity == 0):
                if msg.note in note_starts:
                    start_info = note_starts[msg.note]
                    duration = time_val - start_info['time']
                    self.expected_notes.append({
                        'time': start_info['time'],
                        'note': msg.note,
                        'velocity': start_info['velocity'],
                        'duration': duration
                    })
                    del note_starts[msg.note]
        
        print(f"PerformanceEvaluator: Loaded {len(self.expected_notes)} expected notes")
    
    def start_recording(self):
        """Start recording user performance"""
        self.start_time = time.time()
        self.played_notes = []
        self.active_notes = {}
        self.wrong_notes = []
        self.missed_notes = []
        self.extra_notes = []
        self.timing_errors = []
        self.pauses = []
    
    def record_note_on(self, note, velocity):
        """Record when user presses a note"""
        if self.start_time is None:
            return
        
        current_time = time.time() - self.start_time
        self.active_notes[note] = {
            'start': current_time,
            'velocity': velocity
        }
    
    def record_note_off(self, note):
        """Record when user releases a note"""
        if self.start_time is None or note not in self.active_notes:
            return
        
        current_time = time.time() - self.start_time
        note_info = self.active_notes[note]
        duration = current_time - note_info['start']
        
        self.played_notes.append({
            'time': note_info['start'],
            'note': note,
            'velocity': note_info['velocity'],
            'duration': duration
        })
        
        del self.active_notes[note]
    
    def stop_recording(self):
        """Stop recording and finalize"""
        self.end_time = time.time()
    
    def evaluate(self) -> Dict:
        """
        Evaluate performance and return scores for each criterion
        Returns: {
            'note_accuracy': float (0-100),
            'timing_precision': float (0-100),
            'fluency': float (0-100),
            'dynamics': float (0-100),
            'expression': float (0-100),
            'overall_stars': int (0-5),
            'details': dict with detailed feedback
        }
        """
        if not self.played_notes or not self.expected_notes:
            return self._empty_evaluation()
        
        # 1. Note Accuracy
        note_accuracy = self._evaluate_note_accuracy()
        
        # 2. Timing Precision
        timing_precision = self._evaluate_timing()
        
        # 3. Fluency/Continuity
        fluency = self._evaluate_fluency()
        
        # 4. Dynamics (Volume)
        dynamics = self._evaluate_dynamics()
        
        # 5. Expression/Articulation
        expression = self._evaluate_expression()
        
        # Calculate overall stars (0-5)
        scores = [note_accuracy, timing_precision, fluency, dynamics, expression]
        average_score = sum(scores) / len(scores)
        
        # Star calculation: each criterion must score >= 80 to pass
        passed_criteria = sum(1 for score in scores if score >= 80)
        overall_stars = passed_criteria
        
        return {
            'note_accuracy': note_accuracy,
            'timing_precision': timing_precision,
            'fluency': fluency,
            'dynamics': dynamics,
            'expression': expression,
            'overall_stars': overall_stars,
            'average_score': average_score,
            'details': {
                'wrong_notes': len(self.wrong_notes),
                'missed_notes': len(self.missed_notes),
                'extra_notes': len(self.extra_notes),
                'timing_errors': len(self.timing_errors),
                'long_pauses': len(self.pauses),
                'total_expected': len(self.expected_notes),
                'total_played': len(self.played_notes)
            }
        }
    
    def _evaluate_note_accuracy(self) -> float:
        """Evaluate percentage of notes played correctly"""
        if not self.expected_notes:
            return 100.0
        
        tolerance = 0.5  # 500ms window to consider notes matching
        
        correct_notes = 0
        self.missed_notes = []
        self.wrong_notes = []
        self.extra_notes = list(self.played_notes)  # Start with all played notes
        
        for expected in self.expected_notes:
            # Find matching played note
            matched = False
            for i, played in enumerate(self.extra_notes):
                if (played['note'] == expected['note'] and 
                    abs(played['time'] - expected['time']) <= tolerance):
                    correct_notes += 1
                    matched = True
                    self.extra_notes.pop(i)
                    break
            
            if not matched:
                self.missed_notes.append(expected)
        
        # Wrong notes are the ones played but not matching any expected
        self.wrong_notes = self.extra_notes
        
        accuracy = (correct_notes / len(self.expected_notes)) * 100
        return min(100.0, accuracy)
    
    def _evaluate_timing(self) -> float:
        """Evaluate rhythmic precision"""
        if not self.played_notes or not self.expected_notes:
            return 100.0
        
        tolerance = 0.2  # 200ms tolerance
        
        self.timing_errors = []
        timing_scores = []
        
        for expected in self.expected_notes:
            # Find closest played note
            closest = None
            min_diff = float('inf')
            
            for played in self.played_notes:
                if played['note'] == expected['note']:
                    time_diff = abs(played['time'] - expected['time'])
                    if time_diff < min_diff:
                        min_diff = time_diff
                        closest = played
            
            if closest:
                if min_diff <= tolerance:
                    # Perfect or acceptable timing
                    timing_scores.append(100 - (min_diff / tolerance) * 20)
                else:
                    # Too early or too late
                    timing_scores.append(60)  # Penalty
                    self.timing_errors.append({
                        'expected_time': expected['time'],
                        'played_time': closest['time'],
                        'difference': min_diff
                    })
        
        if not timing_scores:
            return 100.0
        
        return sum(timing_scores) / len(timing_scores)
    
    def _evaluate_fluency(self) -> float:
        """Evaluate continuity (no long pauses, omissions, unnecessary repetitions)"""
        if not self.played_notes:
            return 100.0
        
        self.pauses = []
        max_pause = 2.0  # Maximum acceptable pause (2 seconds)
        
        # Check for long pauses between notes
        for i in range(1, len(self.played_notes)):
            gap = self.played_notes[i]['time'] - (
                self.played_notes[i-1]['time'] + self.played_notes[i-1]['duration']
            )
            
            if gap > max_pause:
                self.pauses.append({
                    'time': self.played_notes[i-1]['time'],
                    'duration': gap
                })
        
        # Score based on pauses and missed notes
        pause_penalty = len(self.pauses) * 10
        missed_penalty = len(self.missed_notes) * 5
        
        score = 100 - pause_penalty - missed_penalty
        return max(0.0, min(100.0, score))
    
    def _evaluate_dynamics(self) -> float:
        """Evaluate volume variations (MIDI velocity)"""
        if not self.played_notes or not self.expected_notes:
            return 100.0
        
        # Compare velocity of played vs expected notes
        velocity_scores = []
        
        for expected in self.expected_notes:
            # Find matching played note
            for played in self.played_notes:
                if (played['note'] == expected['note'] and 
                    abs(played['time'] - expected['time']) <= 0.5):
                    # Compare velocities
                    expected_vel = expected['velocity']
                    played_vel = played['velocity']
                    
                    # Calculate similarity (0-100)
                    diff = abs(expected_vel - played_vel)
                    similarity = 100 - (diff / 127.0) * 100
                    velocity_scores.append(max(0, similarity))
                    break
        
        if not velocity_scores:
            return 80.0  # Neutral score if no data
        
        return sum(velocity_scores) / len(velocity_scores)
    
    def _evaluate_expression(self) -> float:
        """Evaluate articulation and note duration accuracy"""
        if not self.played_notes or not self.expected_notes:
            return 100.0
        
        duration_scores = []
        
        for expected in self.expected_notes:
            # Find matching played note
            for played in self.played_notes:
                if (played['note'] == expected['note'] and 
                    abs(played['time'] - expected['time']) <= 0.5):
                    # Compare durations
                    expected_dur = expected['duration']
                    played_dur = played['duration']
                    
                    # Allow 30% tolerance in duration
                    if expected_dur > 0:
                        ratio = played_dur / expected_dur
                        if 0.7 <= ratio <= 1.3:
                            duration_scores.append(100)
                        elif 0.5 <= ratio <= 1.5:
                            duration_scores.append(80)
                        else:
                            duration_scores.append(60)
                    break
        
        if not duration_scores:
            return 80.0  # Neutral score
        
        return sum(duration_scores) / len(duration_scores)
    
    def _empty_evaluation(self) -> Dict:
        """Return empty evaluation result"""
        return {
            'note_accuracy': 0.0,
            'timing_precision': 0.0,
            'fluency': 0.0,
            'dynamics': 0.0,
            'expression': 0.0,
            'overall_stars': 0,
            'average_score': 0.0,
            'details': {
                'wrong_notes': 0,
                'missed_notes': 0,
                'extra_notes': 0,
                'timing_errors': 0,
                'long_pauses': 0,
                'total_expected': 0,
                'total_played': 0
            }
        }
