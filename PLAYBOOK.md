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
- 2026-11-23 12:30 Kyiv: joker (Kordhell - Murder In My Mind)
- 2026-11-23 19:00 Kyiv: bateman (Interworld - Metamorphosis)
- 2026-11-24 12:30 Kyiv: wick (Hensonn - Sahara)
- 2026-11-24 19:00 Kyiv: spiderman (Tom Holland; Montagem Tomada slowed)
Before making a video, check this list: if the current slot is listed here, do nothing.
Used characters (don't repeat): Jack Sparrow, Joker (Heath Ledger), Patrick Bateman, John Wick, Spider-Man (Tom Holland). Earlier manual posts: Darth Vader, Thomas Shelby, Iron Man.

## Text rules
NO character name text at the start of the video (user asked). Use txt: [] in configs. Only the end card "ИИ-ЭДИТЫ @claude.edits2".
## Stats dashboard (do this EVERY run, even when the slot is pre-scheduled)
index.html (user opens it as a home-screen app) reads stats.json from this repo. Each run:
1. Copy current account numbers in stats.json into "previous" (followers, likes, views = sum of video views).
2. If Windsor.ai connector 'tiktok_organic' has a connected account (get_connectors), pull followers/likes/video stats with get_fields+get_data and fill account + per-video views/likes/comments. Otherwise if vidIQ balance > 0, use vidiq_tiktok_profile + vidiq_tiktok_profile_videos (handle claude.edits2). Otherwise leave numbers as they are.
3. Append any newly published video {title, url (from vidiq_social_post_status postUrl), posted, views,likes,comments}. Set "updated" to now (UTC ISO). Commit + push.
