# Practice Statistics

This directory stores practice session statistics for each song.

## File Format

Each song has a JSON file named `{song_uuid}.json` with the following structure:

```json
{
  "song_uuid": "a1a1e7eaaa439658326e312512d21e2a",
  "sessions": [
    {
      "timestamp": 1700000000.0,
      "total_notes": 150,
      "correct_notes": 142,
      "mistakes": [
        {
          "time": 12.5,
          "expected": [60, 64, 67],
          "played": 61,
          "timestamp": 1700000012.5
        }
      ],
      "accuracy": 94.67
    }
  ]
}
```

## Fields

- **song_uuid**: Unique identifier for the song
- **sessions**: Array of practice sessions
  - **timestamp**: Unix timestamp when session started
  - **total_notes**: Total number of notes expected to play
  - **correct_notes**: Number of notes played correctly
  - **mistakes**: Array of mistakes made during practice
    - **time**: Time in song when mistake occurred (seconds)
    - **expected**: List of MIDI note numbers that should have been played
    - **played**: MIDI note number that was actually played
    - **timestamp**: Unix timestamp when mistake occurred
  - **accuracy**: Percentage of correct notes (0-100)

## Usage

Statistics are automatically saved when:
- Practice Mode is stopped
- Practice Mode completes a song
- User switches to a different mode

The statistics can be used to:
- Track learning progress over time
- Identify difficult sections of songs
- Generate practice recommendations
- Display accuracy metrics in the UI
