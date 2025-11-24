class PianoSynth:
    """
    Dummy PianoSynth class for compatibility.
    FluidSynth functionality has been removed - using pygame samples instead.
    """
    def __init__(self, soundfont_path=None):
        # No-op: FluidSynth not used
        pass

    def note_on(self, note, velocity, channel=0):
        # No-op: Audio handled by pygame samples
        pass

    def note_off(self, note, channel=0):
        # No-op: Audio handled by pygame samples
        pass

    def set_instrument(self, program, channel=0):
        # No-op: Audio handled by pygame samples
        pass
    
    def all_notes_off(self):
        """Stop all currently playing notes"""
        # No-op: Audio handled by pygame samples
        pass
    
    def cleanup(self):
        """Clean up resources before shutdown"""
        # No-op: Nothing to clean up
        pass
