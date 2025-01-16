import time
import os
import mido
import pygame
from mido import MidiFile

pygame.mixer.init()
REGULAR_ASCII = ['-', '=', '#', '*', '+', 'o', 'O']
SPECIAL_ASCII = ['░', '▒', '▓', '█', '■', '◆', '◆']

NOTE_COLORS = {
    'blue': (51, 102, 255),
    'orange': (255, 126, 51),
    'green': (51, 255, 102),
    'pink': (255, 51, 129),
    'cyan': (51, 255, 255),
    'purple': (228, 51, 255)
}

COLOR_MAPPING = {
    0: NOTE_COLORS['blue'],   # Bass notes
    1: NOTE_COLORS['green'],  # Chords
    2: NOTE_COLORS['orange'],  # Melody notes
    3: NOTE_COLORS['pink'],   # Mid-range non-melody notes
    4: NOTE_COLORS['cyan'],   # Additional melody
    5: NOTE_COLORS['purple'],  # Special effects or other
}


RESET_COLOR = '\033[0m'
NPS_THRESHOLD_AGGRESSIVE_1 = 10000
NPS_THRESHOLD_AGGRESSIVE_2 = 20000
SPEEDUP_FACTOR = 0.8
AGGRESSIVE_SPEEDUP_FACTOR = 0.6

class ASCIIPiano:
    def __init__(self, use_color=False, ascii_style=REGULAR_ASCII):
        self.active_notes = {}
        self.use_color = use_color
        self.ascii_style = ascii_style

    def visualize_piano(self):
        piano_keys = [" " for _ in range(128)]
        
        for note, channel in self.active_notes.items():
            if 0 <= note < 128:
                symbol = self.ascii_style[channel % len(self.ascii_style)]
                if self.use_color:
                    # Get RGB color for the current channel
                    color = COLOR_MAPPING.get(channel % len(COLOR_MAPPING), (255, 255, 255))
                    color_code = f"\033[38;2;{color[0]};{color[1]};{color[2]}m"
                    piano_keys[note] = f"{color_code}{symbol}{RESET_COLOR}"
                else:
                    piano_keys[note] = symbol

        print("\r" + "".join(piano_keys), end="")

    def note_on(self, note, channel):
        self.active_notes[note] = channel

    def note_off(self, note):
        if note in self.active_notes:
            del self.active_notes[note]

def get_bpm(midi_file):
    """Extract BPM from the MIDI file."""
    for msg in midi_file:
        if msg.type == 'set_tempo':
            return mido.tempo2bpm(msg.tempo)
    return 120

def calculate_sleep_time(bpm, ticks_per_beat):
    """Calculate sleep time based on BPM and ticks per beat."""
    return 60 / (bpm * ticks_per_beat)

def play_midi(midi_path, ascii_style, use_color=False, audio_path=None):
    try:
        mid = MidiFile(midi_path)
    except Exception as e:
        print(f"Error loading MIDI file: {e}")
        return

    piano = ASCIIPiano(use_color=use_color, ascii_style=ascii_style)

    bpm = get_bpm(mid)
    ticks_per_beat = mid.ticks_per_beat
    sleep_time = calculate_sleep_time(bpm, ticks_per_beat)

    notes_played = 0
    start_time = time.time()
    audio_played = False

    try:
        for message in mid.play():
            if message.is_meta:
                continue

            current_time = time.time()
            elapsed_time = current_time - start_time

            if elapsed_time >= 1.0:
                nps = notes_played / elapsed_time

                if nps > NPS_THRESHOLD_AGGRESSIVE_2:
                    sleep_time *= AGGRESSIVE_SPEEDUP_FACTOR
                elif nps > NPS_THRESHOLD_AGGRESSIVE_1:
                    sleep_time *= SPEEDUP_FACTOR

                notes_played = 0
                start_time = current_time

            if message.type == 'note_on' and message.velocity > 0:
                piano.note_on(message.note, message.channel)
                piano.visualize_piano()
                notes_played += 1

                if not audio_played and audio_path:
                    pygame.mixer.music.load(audio_path)
                    pygame.mixer.music.play()
                    audio_played = True

            elif message.type == 'note_off' or (message.type == 'note_on' and message.velocity == 0):
                piano.note_off(message.note)
                piano.visualize_piano()

            time.sleep(sleep_time * message.time)

            if sleep_time < calculate_sleep_time(bpm, ticks_per_beat):
                continue

    except Exception as e:
        print(f"Error during MIDI playback: {e}")

def get_midi_file(folder_path):
    midi_files = [f for f in os.listdir(folder_path) if f.endswith('.mid') or f.endswith('.midi')]
    
    if not midi_files:
        print("No MIDI files found.")
        return None
    
    print("Available MIDI files:")
    for i, midi_file in enumerate(midi_files):
        print(f"{i + 1}: {midi_file}")

    choice = input(f"Select a MIDI file (1-{len(midi_files)}): ")
    if choice.isdigit() and 1 <= int(choice) <= len(midi_files):
        return os.path.join(folder_path, midi_files[int(choice) - 1])
    else:
        print("Invalid choice.")
        return None

def get_audio_file(folder_path):
    audio_files = [f for f in os.listdir(folder_path) if f.endswith('.mp3') or f.endswith('.wav')]
    
    if not audio_files:
        print("No audio files found.")
        return None
    
    print("Available audio files:")
    for i, audio_file in enumerate(audio_files):
        print(f"{i + 1}: {audio_file}")

    choice = input(f"Select an audio file (1-{len(audio_files)}): ")
    if choice.isdigit() and 1 <= int(choice) <= len(audio_files):
        return os.path.join(folder_path, audio_files[int(choice) - 1])
    else:
        print("Invalid choice.")
        return None

print("Preparing the ASCII MIDI-Player...")
time.sleep(2)

response = input("Do you want to play a MIDI file? (Y/N): ").strip().upper()

if response == 'Y':
    play_audio_response = input("Do you want to play an audio file during MIDI playback? (Y/N): ").strip().upper()
    audio_path = None

    if play_audio_response == 'Y':
        folder_path = os.path.join(os.path.dirname(__file__), 'audios')
        if os.path.exists(folder_path) and os.path.isdir(folder_path):
            audio_path = get_audio_file(folder_path)
        else:
            print("The specified audio folder does not exist.")
    
    style_choice = input("Choose ASCII style: 1 - Regular, 2 - Special: ").strip()
    ascii_style = REGULAR_ASCII if style_choice == '1' else SPECIAL_ASCII

    color_choice = input("Enable colored notes? (Y/N): ").strip().upper()
    use_color = True if color_choice == 'Y' else False

    folder_path = os.path.join(os.path.dirname(__file__), 'midis')
    
    if os.path.exists(folder_path) and os.path.isdir(folder_path):
        midi_path = get_midi_file(folder_path)
        if midi_path:
            print(f"Playing {midi_path}...")
            play_midi(midi_path, ascii_style, use_color, audio_path)
        else:
            print("No MIDI file selected.")
    else:
        print("The specified MIDI folder does not exist.")

print("Exiting the MIDI player.")
