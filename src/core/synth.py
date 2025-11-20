import os
import sys

try:
    import fluidsynth
except Exception as e:
    fluidsynth = None
    print(f"Warning: Audio engine (fluidsynth) could not be loaded: {e}")
    print("Audio will be disabled.")

class PianoSynth:
    def __init__(self, soundfont_path=None):
        self.fs = None
        self.driver = None
        
        if not fluidsynth:
            return

        if soundfont_path is None or not os.path.exists(soundfont_path):
            print(f"Warning: Soundfont not found at {soundfont_path}")
            # Try to find a default one or just fail gracefully
            return

        try:
            self.fs = fluidsynth.Synth()
            # On Windows, 'dsound' is common. On Linux 'alsa' or 'pulseaudio'.
            # We'll try to let it pick default or specify 'dsound' for Windows.
            if sys.platform == 'win32':
                self.fs.start(driver='dsound')
            else:
                self.fs.start()

            sfid = self.fs.sfload(soundfont_path)
            self.fs.program_select(0, sfid, 0, 0)
            print("Fluidsynth started successfully.")
        except Exception as e:
            print(f"Error initializing fluidsynth: {e}")
            self.fs = None

    def note_on(self, note, velocity, channel=0):
        if self.fs:
            self.fs.noteon(channel, note, velocity)

    def note_off(self, note, channel=0):
        if self.fs:
            self.fs.noteoff(channel, note)

    def set_instrument(self, program, channel=0):
        if self.fs:
            self.fs.program_change(channel, program)
    
    def all_notes_off(self):
        """Stop all currently playing notes"""
        if self.fs:
            for channel in range(16):  # MIDI has 16 channels
                for note in range(128):  # MIDI notes 0-127
                    try:
                        self.fs.noteoff(channel, note)
                    except:
                        pass
    
    def cleanup(self):
        """Clean up resources before shutdown"""
        try:
            if self.fs:
                self.all_notes_off()
                # FluidSynth cleanup is automatic on object deletion
                self.fs = None
        except Exception as e:
            print(f"Error in PianoSynth cleanup: {e}")
