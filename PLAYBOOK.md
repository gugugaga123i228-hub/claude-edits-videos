# Playbook: @claude.edits2 (TikTok account connected in vidIQ as "minecraftserver985")
Owner: Prompt (Russian). Text on videos and captions in Russian, <=5 hashtags.
Schedule: Sun-Thu 12:30 and 19:00 Europe/Kyiv. NO posting Fri/Sat. Publicly, comments allowed, music usage confirmed, isAiGenerated true.
Pipeline per run:
1. Pick a NEW non-cartoon (live action) character/movie not yet in videos/ (see list). Search ideas with WebSearch; vidIQ credits for search are out, free tools only.
2. Footage + song: find a public YouTube scenepack and a song video via WebSearch (youtube.com), import with vidiq_video_upload(url) -> vidiq_job_poll -> curl signed videoUrl. Song: extract audio from a YouTube video the same way (pick a trending sound, 20-27 s section).
3. Edit with scripts/edit29.py (config-driven: python3 edit29.py cfg.json out.mp4 [preview]; see configs/*.json for examples; 'lb' trims letterbox; s0 = song offset so the drop lands at a0). Older template scripts/edit28.py (PIL+numpy+OpenCV frames piped to ffmpeg, 1080x1920, beat grid from kick onsets, flashes/zoom/whip transitions, end card "ИИ-ЭДИТЫ @claude.edits2"). Reference style: fast beat-synced cuts, white flashes, meme-like inserts. Text overlays: only ONE at a time, never overlapping. Check a contact sheet of frames before rendering; drop clips with gray/black/credit cards.
4. Commit mp4 to videos/<name>.mp4 and push to main (releases are blocked). URL: https://raw.githubusercontent.com/gugugaga123i228-hub/claude-edits-videos/main/videos/<name>.mp4
5. vidiq_video_upload(url) -> vidiq_social_post_draft_create (TIKTOK, platformAccountId _0006fSz6eYpBAcoC72Bz2Te9kilRSbMXwqG, PUBLIC_TO_EVERYONE, allowComment true, musicUsageConfirmed true, isAiGenerated true) -> vidiq_social_post_publish -> vidiq_social_post_status.
Limits: no tool to reply to TikTok comments or DMs; reading comments costs vidIQ credits.
Published: jack_v1 (Jack Sparrow).
## Pre-made queue (already SCHEDULED in vidIQ, do NOT make a new video for these slots — just exit with a short note):
- 2026-11-23 12:30 Kyiv: tyler_v1 (Tyler Durden; user's own song)
- 2026-11-25 12:30 Kyiv: joker_v4 (Lthiago - Montagem da Chupeta)
- 2026-11-23 19:00 Kyiv: bateman (Interworld - Metamorphosis)
- 2026-11-24 12:30 Kyiv: wick_v3 (Odetari - I'm a Blackhole)
- 2026-11-24 19:00 Kyiv: spidey_v3 (BIA - We On Go, cinematic intro edit audio)
vidIQ postIds (use vidiq_social_post_status to get postUrl for stats.json): tyler 7603792a-ed86-4c13-a50d-c1e5447f414b, joker 846a9a41-d6c4-4719-bcf2-8af373ddd346, bateman d5a47600-0902-49ab-8035-7aede5d3662d, wick b6233c21-a0d8-451b-98e3-2d4a5d0098d9, spiderman 679beb42-6d10-4ebe-9da4-bafc88acb60a, jack eebe17c7-3e17-4483-ae77-c8040d0b5a85.
Before making a video, check this list: if the current slot is listed here, do NOT make or post a video — only update stats.json (see below).
Nice to have: if a run has spare time, it may pre-make the NEXT slot's video and schedule it with publishAt (then add it to this queue list).
Used characters (don't repeat): Jack Sparrow, Joker (Heath Ledger), Patrick Bateman, John Wick, Spider-Man (Tom Holland), Tyler Durden. Earlier manual posts: Darth Vader, Thomas Shelby, Iron Man.

## Text rules
NO character name text at the start of the video (user asked). Use txt: [] in configs. Only the end card "ИИ-ЭДИТЫ @claude.edits2".
## Stats dashboard (do this EVERY run, even when the slot is pre-scheduled)
index.html (user opens it as a home-screen app) reads stats.json from this repo. Each run:
1. Copy current account numbers in stats.json into "previous" (followers, likes, views = sum of video views).
2. If Windsor.ai connector 'tiktok_organic' has a connected account (get_connectors), pull followers/likes/video stats with get_fields+get_data and fill account + per-video views/likes/comments. Otherwise if vidIQ balance > 0, use vidiq_tiktok_profile + vidiq_tiktok_profile_videos (handle claude.edits2). Otherwise leave numbers as they are.
3. Append any newly published video {title, url (from vidiq_social_post_status postUrl), posted, views,likes,comments}. Set "updated" to now (UTC ISO). Commit + push.

## STYLE (user feedback 2026-11-23) — follow strictly
- Use scripts/edit30.py (clean style). NOT edit29: user hated shake, spins, rotations, glitch/kaleido. Hard cuts on beats, static framing with slow push-in, white flash after cuts, zoom punch only on a few accent beats, strobe only on the last ~1.3 s before the drop. Emotional songs: no flash, 2-4 beat holds.
- Songs MUST be current trends (search 'trending TikTok sounds <this month>' / tokchart.com / '#editaudio'). User was angry at a 2021 song. Liked: bateman edit.
- Shots: clean close-ups of the main character, middle of scenes, no dark/empty/blurred frames; check the preview sheet before rendering.

## PIPELINE v3 (user feedback 2026-11-23: character must be IN FRAME every shot, cuts ON the beat)
1. scripts/scan.py pack.mp4 scan.json <letterbox 0..0.15> 0.25   (MediaPipe face+person per 0.25 s; models: curl -o /home/claude/models/face.tflite https://storage.googleapis.com/mediapipe-models/face_detector/blaze_face_short_range/float16/latest/blaze_face_short_range.tflite and det.tflite = .../object_detector/efficientdet_lite0/float32/latest/efficientdet_lite0.tflite ; pip install --break-system-packages mediapipe librosa)
2. scripts/cands.py scan.json pack.mp4 cands.jpg 0.75  -> numbered crop sheet of shots centred on the detected face. LOOK at it and pick only ids that show THE main character clearly (drop other people, dark, empty).
3. Write spec (see configs/joker4.spec.json, spidey3.spec.json): song wav, drop time (song seconds), pre 5.5, post ~16, ids in order. scripts/assemble.py spec out.json  (cuts snap to librosa beats).
4. scripts/edit30.py out.json preview.jpg preview -> check every tile has the character -> render.
