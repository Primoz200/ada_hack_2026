"""Camera exercises (gameType "camera", level = exercise). Single source of truth: the recorder fetches this
via GET /api/camera/exercises, scoring reads it directly.

Cue timeline (ms from recording start): cues at first_cue_s + k * cue_period_s, k = 0..n_cues-1.
  hand:  beep = hand fully open; "ODPRI" shown 0.5 s before to 0.5 s after the beep, then "stisni" 2 s (3 s cycle).
  arms:  high beep = "up" (hold until up_s), low beep = "down"; one repetition per cue.
The first second (before the first cue) is the rest pose used as each recording's own zero.
"""

EXERCISES = {
    1: {
        "key": "hand_open_close",
        "name": "Odpiranje in zapiranje dlani",
        "detector": "hand",
        "duration_s": 21.0,
        "first_cue_s": 1.0,
        "cue_period_s": 3.0,  # ODPRI 0.5 s before the beep + 0.5 s after it, then "stisni" 2.0 s
        "n_cues": 7,
        "up_s": None,
        "open_window_s": 0.5,  # "ODPRI" shown from beep - 0.5 s to beep + 0.5 s (beep = hand fully open)
        "instructions": "Dlan obrni proti kameri, komolec na mizi. Ob vsakem pisku dlan čim bolj odpri, "
                        "med piski jo stisni v pest.",
    },
    2: {
        "key": "shoulder_abduction",
        "name": "Roke v stran",
        "detector": "pose",
        "duration_s": 42.0,
        "first_cue_s": 1.0,
        "cue_period_s": 8.0,  # 4 s up, 4 s down
        "n_cues": 5,
        "up_s": 4.0,
        "instructions": "Sedi vzravnano, zgornji del telesa v kadru. Ob visokem pisku iztegnjeni roki dvigni "
                        "skozi stran čim višje, ob nizkem ju spusti.",
    },
    3: {
        "key": "arm_raise",
        "name": "Dvig rok čim višje",
        "detector": "pose",
        "duration_s": 42.0,
        "first_cue_s": 1.0,
        "cue_period_s": 8.0,  # 4 s up, 4 s down
        "n_cues": 5,
        "up_s": 4.0,
        "instructions": "Sedi vzravnano, zgornji del telesa v kadru. Ob visokem pisku dvigni roki čim višje "
                        "nad glavo, ob nizkem ju spusti.",
    },
}

# MediaPipe landmark indices
HAND_WRIST, HAND_MIDDLE_MCP = 0, 9
HAND_FINGERTIPS = (8, 12, 16, 20)  # index..pinky (thumb moves differently, left out)
POSE = {
    "nose": 0, "left_ear": 7, "right_ear": 8,
    "left_shoulder": 11, "right_shoulder": 12, "left_elbow": 13, "right_elbow": 14,
    "left_wrist": 15, "right_wrist": 16, "left_hip": 23, "right_hip": 24,
}
N_LANDMARKS = {"hand": 21, "pose": 33}


def cue_times_ms(ex: dict):
    return [1000.0 * (ex["first_cue_s"] + k * ex["cue_period_s"]) for k in range(ex["n_cues"])]
