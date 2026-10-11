
# Voice and Sound

## Voiceover

1. Confirm the final narration text, language, intended tone, and placement. Reuse the user's chosen voice when one is already explicit.
2. Otherwise read `@references/voices.md` and present a short, provider-neutral shortlist in ordinary Hana chat. Keep each displayed voice tied to the exact preset ID in that reference; do not invent voice IDs or names.
3. State the selected voice and text scope and warn that generation may consume ChatCut credits; wait for explicit confirmation.
4. Call `submit_voice` with the selected preset ID and the current tool schema.
5. Track completion, then place or replace the audio with `edit_item` as requested.
6. Read back the audio item range and check sync against the visual timeline.

For long narration, split only at natural semantic boundaries and preserve consistent voice/settings. If visual timing changes later, retime visuals or regenerate only when necessary; do not silently stretch speech unnaturally.

## Sound effects

Search the built-in Sound Effects library with `browse_library` before generating. Use `submit_sound` only when the user needs a custom sound that the library cannot supply, and apply the same credit confirmation rule before submission.


---

## 附：video-sync

# Voiceover Video Sync

Use this reference from the `voice` skill when existing visuals drive narration
timing. The job is not just generating TTS; it is making the spoken meaning line
up with what is on screen.

## When to Use

- The user has an existing video, timeline, screen recording, slide animation,
  product demo, B-roll edit, MG explainer, or similar visual sequence.
- The user provides narration text, asks you to write narration, or asks to add,
  replace, redo, dub, or generate voiceover for that visual sequence.
- The timeline already has narration/voiceover and the user asks to trim, speed
  up, slow down, reorder, replace, or retime the visuals while keeping the
  existing voiceover aligned.
- The video has meaningful visual sections: slide changes, product states,
  screen steps, chart/data moments, scene cuts, action beats, or key visual
  events.

Do not wait for the user to explicitly ask for sync. If there is a visual target,
assume the narration should respect the visual content and pacing unless the user
only wants a standalone audio asset.

Do not use this as the main path for cutting original human speech. Use the
talking-head workflow for editing existing spoken content.

## Workflow

1. Read the project state and identify the exact visual target: timeline range,
   video asset, selected item, or full composition. If multiple candidates are
   plausible, ask which one should receive voiceover.
2. Check whether the conversation already contains a usable narration plan,
   storyboard, or script table. Treat it as a draft sync map, not as approved
   TTS input. Reuse it only when it names visual anchors and time ranges for the
   same current visual target. If the target changed, the table is missing
   visual evidence, or any boundary is only a guess, verify only the missing or
   uncertain boundaries instead of restarting the whole visual review.
3. Keep the sync map tied to the current visual state. If an edit changes where
   visual content appears after the map was made, mark the affected rows stale.
   Before placing or reusing voiceover, rebuild or patch those rows from the
   current timeline/asset state. Do not keep using old visual windows after a
   visual retiming edit.
4. Understand the visuals before generating audio. Use project reads, timeline
   screenshots, and `view_asset_frames` for source-frame sampling when needed.
   Segment the target by visible content changes, not by arbitrary equal
   intervals.
5. Build a visual-voiceover sync map from actual visual evidence. Do not
   generate TTS or place voiceover until every segment has a confirmed visual
   anchor and placement start frame/time. For each segment, record:
   - visual start/end frame or time
   - visual anchor: slide title, product state, screen action, chart/data point,
     scene content, or event
   - evidence: inspected frame/time, screenshot, or visual-analysis result
   - narration text assigned to that visual moment
   - target duration and estimated TTS duration
   - fit status: fits / too long / uncertain
   - voiceover placement start frame or time
   - confidence or uncertainty
6. Split or write narration to fit the visual map. Keep each TTS segment tied to
   one visual segment or one intentional multi-shot beat. Do not create one long
   audio file for a video with multiple visual states. Before submitting TTS,
   map each narration line to a visual segment and check that the estimated TTS
   duration is plausibly short enough for its visual window. For short windows,
   prefer phrase-length copy over full sentences. Do not submit TTS for a line
   whose fit status is `too long` or `uncertain` until you tighten the wording,
   split the line, adjust supported speed, or ask the user to approve the timing
   tradeoff.
7. Follow the `voice` skill's audition workflow if the user has not picked a
   voice. Generate TTS per mapped segment.
8. After each TTS segment finishes, read the real audio duration before placing
   it. If the real duration exceeds its visual window or would make the
   narration describe a visual that is not currently on screen, do not place it
   on the timeline yet. Fix the mismatch before final delivery:
   - tighten or split narration
   - adjust speech speed when supported and natural
   - shift the placement to a better visual range
   - extend or hold a visual only when that preserves the edit
   - ask the user when the tradeoff changes meaning or style
9. Place each voiceover segment only after the actual-duration fit check passes.
   Place it at the matching visual start time from the current sync map. If
   original audio, music, or sound effects exist, decide whether to mute, duck,
   replace, or mix them based on user intent.
10. After patching or rebuilding stale rows, read back the updated timeline
    positions before claiming the edit is done. Confirm that caption text, spoken
    content, visual segment, placement, and actual audio duration still
    correspond.
11. Run a final coverage check before delivery. Every visual segment the user
    expected to be explained should either have matching voiceover or an explicit
    reason for silence. Voiceover should not start before its visual appears, and
    old voiceover should not remain over footage whose timing changed. If the
    turn changed any narration-backed visual timing, include a `Final sync check`
    in the response before saying the edit is complete.
12. Verify after placement. Read back item start/end/duration and inspect
    representative frames around each segment start, middle, and end. Preview or
    screenshot enough of the timeline to confirm the spoken meaning and current
    visual information match.

## Rules

- Do not drop a single generated narration track over a multi-section video and
  call it done.
- Do not let a TTS segment talk about a visual that has already disappeared or
  has not appeared yet.
- Do not rewrite user-provided narration in a way that changes claims, names,
  numbers, or intended meaning just to fit timing. Ask or preserve meaning.
- Do not cover meaningful original speech unless the user asked to replace,
  dub, mute, or voice over it.
- Do not treat slide/video length as enough evidence. Use visible anchors and
  content changes.
- Do not treat a script table or narration draft as ready-to-submit TTS input
  until each line has been mapped to a visual segment and checked against that
  segment's target duration.
- Do not use equal division or rough duration estimates as placement
  boundaries. If a boundary is only estimated, inspect more frames around that
  range until the content-change frame is confirmed, or ask the user to approve
  the approximation.
- Do not silently switch from visual-driven sync to narration-driven timing.
  That changes the edit contract. Ask the user before extending visuals,
  allowing desync, overlapping voiceover, or letting narration timing drive the
  cut.
- Do not treat a generated TTS asset as ready for placement just because it
  completed successfully. Real audio duration must pass the sync map's fit check
  first.
- Do not reuse a sync map after timeline or visual-source edits changed where
  visual content appears. Patch or rebuild the affected rows first.
- Do not report completion until expected voiceover coverage has been checked
  against the current timeline.
- Do not end a retiming turn immediately after timeline edits. First read back
  the updated item positions and report a `Final sync check` for each changed
  visual/voiceover pair.

## Output Format

When planning or reporting execution, use this compact shape:

- `target_visual`: asset/item/timeline range
- `segments`: visual range, visual anchor, narration text, TTS asset, audio
  duration, target duration, estimated duration, fit status, placement range,
  mismatch handling, map status
- `mix`: what happened to original audio/music
- `Final sync check`: pass/fail per segment, stale-map fixes, coverage gaps, and
  any timing fixes applied


---

## 附：voices

# Voice Presets

This page is the curated preset snapshot the agent works from. The backend
holds the source of truth and keeps this file in sync.

Use tags as selection filters. Use descriptions as practical hints. Age,
accent, pronunciation, and exact duration are not stable controls unless the
TTS provider exposes explicit parameters for them.

## Doubao Chinese Voices

Use Doubao for Chinese-optimized narration.

| Preset               | Official display | English display      | Tags                                                           | Selection hint                                                |
| -------------------- | ---------------- | -------------------- | -------------------------------------------------------------- | ------------------------------------------------------------- |
| `vivi`               | Vivi             | Vivi                 | female, young, friendly, general, short-explainer              | Everyday Chinese narration, product intros, short explainers  |
| `xiaohe`             | 小何             | Xiaohe               | female, young, soft, calm, tutorial, walkthrough               | Calm tutorials, product walkthroughs, instructional narration |
| `yunzhou`            | 云舟             | Yunzhou              | male, young, neutral, business, explainer                      | Business explainers, factual reads, product narration         |
| `xiaotian`           | 小天             | Xiaotian             | male, young, bright, upbeat, casual                            | Casual creator-style videos and light social narration        |
| `naiqimengwa`        | 奶气萌娃         | Childlike Boy        | male, child, cute, storybook, character                        | Cute boy character lines and children's stories               |
| `yingtaowanzi`       | 樱桃丸子         | Cherry Voice         | female, child, cartoon, roleplay, character                    | Animated/kid-oriented character dialogue                      |
| `wenroumama`         | 温柔妈妈         | Warm Mom             | female, middle-aged, warm, family, gentle                      | Family, lifestyle, parenting, gentle explanations             |
| `zhixingnv`          | 知性女声         | Knowledgeable Female | female, middle-aged, calm, knowledge, explainer                | Education, culture, thoughtful explainers                     |
| `dayi`               | 大壹             | Dayi                 | male, young, steady, formal, documentary, video-voiceover      | Formal voiceover, documentary, corporate narration            |
| `jitangnv`           | 鸡汤女           | Inspirational Female | female, young, warm, inspirational, emotional, video-voiceover | Motivational, uplifting, emotional video narration            |
| `liuchang`           | 流畅女声         | Smooth Female        | female, young, smooth, polished, video-voiceover, narration    | Clean product narration and polished video voiceover          |
| `ruyayichen`         | 儒雅逸辰         | Yichen               | male, young, elegant, premium, culture, video-voiceover        | Cultural, premium, poetic, documentary-style narration        |
| `morgan`             | Morgan           | Morgan               | male, middle-aged, deep, knowledge, explainer                  | Deep knowledge explainer, documentary, serious narration      |
| `qingcang`           | 擎苍             | Qingcang             | male, old-like, authoritative, audiobook, character            | Weighty narration, dramatic reads, audiobook scenes           |
| `huiben`             | 儿童绘本         | Storybook Voice      | female, young, gentle, storybook, audiobook                    | Gentle storybook or bedtime-style narration                   |
| `popo`               | 婆婆             | Grandma              | female, old, warm, story, character                            | Grandmother characters, folk stories, nostalgic narration     |
| `yuanboxiaoshu`      | 渊博小叔         | Erudite Uncle        | male, middle-aged, knowledge, calm, explainer                  | Calm explainers, cultural commentary, educational narration   |
| `baqiqingshu`        | 霸气青叔         | Confident Uncle      | male, middle-aged, confident, audiobook, narrative             | Audiobook narration, long-form stories, dramatic reads        |
| `shuanglangshaonian` | 爽朗少年         | Cheerful Teen        | male, young, cheerful, youthful, roleplay, character           | Bright roleplay, teen/creator dialogue, youthful scenes       |
| `tangseng`           | 唐僧             | Tang Seng            | male, old-like, calm, roleplay, character                      | Monk-like dialogue, traditional stories, steady narration     |

Important caveat: the current Doubao seed-tts-2.0 resource does not expose an
explicit general-purpose old-male voice. `qingcang` and `tangseng` are
old-like approximations, not guaranteed old-male controls.

### Doubao Control Support

Base controls for curated Doubao voices: `speedRatio`, `loudnessRatio`, and
`pitch`.

Expressive controls:

- Supports `emotion`, `emotionScale`, `performancePrompt`, and ASMR-style prompt
  directions: `vivi`, `xiaohe`, `yunzhou`, `xiaotian`, `naiqimengwa`,
  `yingtaowanzi`, `wenroumama`, `zhixingnv`, `dayi`, `jitangnv`, `liuchang`,
  `ruyayichen`, `morgan`, `qingcang`, `huiben`, `popo`, `yuanboxiaoshu`,
  `baqiqingshu`, `tangseng`.
- `shuanglangshaonian` supports `performancePrompt` and COT/QA-style
  instruction following only. Do not use `emotion`, `emotionScale`, or
  ASMR-style prompt directions with this voice.
- `explicitDialect` is only supported by `vivi`; allowed values are `dongbei`,
  `shaanxi`, and `sichuan`.

## ElevenLabs English / Multilingual Voices

Use ElevenLabs for English or multilingual narration. Official accent labels
are English-source voice cues, not target-language accent controls.

| Preset      | Tags                                                       | Selection hint                                             |
| ----------- | ---------------------------------------------------------- | ---------------------------------------------------------- |
| `amelia`    | female, young, upbeat, narrative-story, social-media       | Story reads, podcast intros, reels, enthusiastic ads       |
| `brittney`  | female, young, upbeat, social-media, fun                   | Creator videos, recaps, hot-topic commentary, how-to clips |
| `hope`      | female, young, upbeat, clear, social-media                 | Crisp short-form narration and quick explainers            |
| `jessica`   | female, middle-aged, calm, conversational, narrative-story | Composed narration, confident product copy, direct reads   |
| `arabella`  | female, young, gentle, emotive, narrative-story            | Fantasy, romance, wellness, atmospheric stories            |
| `jane`      | female, old, professional, audiobook, narrative-story      | Long-form book pacing and classic narration                |
| `maria`     | female, old, calm, grandmother, narrative-story            | Grandmother-style narration and reflective story delivery  |
| `mark`      | male, young, casual, conversational, natural               | Dialogue, assistant-style replies, informal scripts        |
| `frederick` | male, middle-aged, calm, documentary, narrative-story      | History, science, mystery, factual films                   |
| `peter`     | male, middle-aged, confident, credible, narrative-story    | Trustworthy narration, explainers, brand reads             |
| `james`     | male, middle-aged, deep, husky, narrative-story            | Audiobooks, heavier story narration, professional VO       |
| `jon`       | male, middle-aged, calm, grounded, narrative-story         | Clear messaging, commercials, trustworthy narration        |
| `sully`     | male, old, deep, storyteller, narrative-story              | Deep elderly narration and warm authoritative reads        |
| `david`     | male, old, deep, storyteller, narrative-story              | Classic audiobook passages and grounded dramatic reads     |
| `alex`      | male, young, confident, entertainment-tv, social-media     | YouTube, shorts, entertainment clips                       |

### ElevenLabs Control Support

All current curated ElevenLabs presets support the same request-level controls:
`modelId`, `speed`, and `stability`.

Important limits:

- These controls are provider/model-level controls, not per-voice capability
  switches. No current curated ElevenLabs preset is excluded from them, but the
  audible result varies by the source voice's natural delivery.
- For ElevenLabs `eleven_v3`, inline audio tags are available when the user
  asks for expressive delivery such as emotion, tone, nonverbal cues, accent
  hints, or local pacing. Official examples fit these useful TTS categories:
  emotion/tone tags such as `[happy]`, `[sad]`, `[angry]`, `[excited]`,
  `[curious]`, `[sarcastic]`, `[crying]`, `[annoyed]`, `[appalled]`,
  `[thoughtful]`, `[surprised]`, and `[mischievously]`; vocal delivery and
  nonverbal cue tags such as `[whispers]`, `[laughs]`, `[sighs]`, `[exhales]`,
  `[inhales deeply]`, `[clears throat]`, `[snorts]`, `[swallows]`,
  `[wheezing]`, and `[coughs]`;
  pacing/pause/local speed tags such as `[slowly]`, `[pause]`,
  `[short pause]`, `[long pause]`, `[rushed]`, and `[drawn out]`; and
  accent/special-performance tags such as
  `[strong X accent]`, for example `[strong French accent]`, plus `[sings]`,
  `[singing]`, `[woo]`, and `[pirate voice]`. Official examples are
  non-exhaustive; similar auditory tags can be tried when the user explicitly
  asks for that delivery and the tag describes how the voice should sound, not
  a visual action. Write tags directly in `text`, close to the short phrase
  they should affect. Treat tags as local guidance, not paragraph-wide controls.
- For pauses and pacing in `eleven_v3`, use punctuation, text structure,
  shorter generated segments, or local audio tags such as `[short pause]` and
  `[slowly]` when needed.

## Audition Samples

Each curated preset has a local editor sample under:

```text
/voice-samples/<provider>-<preset>.mp3
```

Examples:

- `/voice-samples/doubao-morgan.mp3`
- `/voice-samples/doubao-zhixingnv.mp3`
- `/voice-samples/elevenlabs-peter.mp3`
- `/voice-samples/elevenlabs-sully.mp3`

Prefer these samples when rendering a voice audition widget before calling
`submit_voice`.
