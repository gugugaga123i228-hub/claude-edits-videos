# Playbook: @claude.edits2 (TikTok account connected in vidIQ as "minecraftserver985")
Owner: Prompt (Russian). Text on videos and captions in Russian, <=5 hashtags.
Schedule: Sun-Thu 12:30 and 19:00 Europe/Kyiv. NO posting Fri/Sat. Publicly, comments allowed, music usage confirmed, isAiGenerated true.
Pipeline per run:
1. Pick a NEW non-cartoon (live action) character/movie not yet in videos/ (see list). Search ideas with WebSearch; vidIQ credits for search are out, free tools only.
2. Footage + song: find a public YouTube scenepack and a song video via WebSearch (youtube.com), import with vidiq_video_upload(url) -> vidiq_job_poll -> curl signed videoUrl. Song: extract audio from a YouTube video the same way (pick a trending sound, 20-27 s section).
3. Edit with scripts/edit28.py as template (PIL+numpy+OpenCV frames piped to ffmpeg, 1080x1920, beat grid from kick onsets, flashes/zoom/whip transitions, end card "ИИ-ЭДИТЫ @claude.edits2"). Reference style: fast beat-synced cuts, white flashes, meme-like inserts. Text overlays: only ONE at a time, never overlapping. Check a contact sheet of frames before rendering; drop clips with gray/black/credit cards.
4. Commit mp4 to videos/<name>.mp4 and push to main (releases are blocked). URL: https://raw.githubusercontent.com/gugugaga123i228-hub/claude-edits-videos/main/videos/<name>.mp4
5. vidiq_video_upload(url) -> vidiq_social_post_draft_create (TIKTOK, platformAccountId _0006fSz6eYpBAcoC72Bz2Te9kilRSbMXwqG, PUBLIC_TO_EVERYONE, allowComment true, musicUsageConfirmed true, isAiGenerated true) -> vidiq_social_post_publish -> vidiq_social_post_status.
Limits: no tool to reply to TikTok comments or DMs; reading comments costs vidIQ credits.
Published: jack_v1 (Jack Sparrow).
