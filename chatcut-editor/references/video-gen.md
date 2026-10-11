
# Video Gen

Submits one video generation job per call and returns a `jobId`. Job management (wait / status) belongs to `track_progress`; this skill does **not** place videos on the timeline automatically.

## When to Use

Any time the user wants to generate a video clip — text-to-video, image-to-video, first-last-frame transition, reference-based generation, or generatively editing / extending an existing video (producing new generated footage based on a source clip; not timeline trimming).

## Models

| Model       | Reference                                          | Strengths                                                                                                                |
| ----------- | -------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------ |
| `seedance2` | [references/seedance2.md](references/seedance2.md) | Default. Rich reference system (image / video / audio refs), multi-shot consistency, editing / extending existing clips. |
| `kling`     | [references/kling.md](references/kling.md)         | Camera-control language via prompt; strong on fine emotional / performance control for character shots.                  |

**IMPORTANT:** Before generating, READ the chosen model's reference for capabilities, input channels, modes, prompt structure, and model-specific behavior.

## Model Selection

`seedance2` is the **default**. Only switch to `kling` when one of:

- **User explicitly named kling** ("用 Kling", "use Kling", "/kling") — switch, no need to re-ask.
- **Seedance clearly can't or won't do it well** — when you hit a known case where Seedance struggles, propose switching to `kling` and confirm before submitting.

Otherwise stay on `seedance2`.

Access note: `seedance2` and `kling` both require ChatCut paid video-generation entitlement (subscription or paid credits). Never present Kling as a free workaround for a Seedance subscription gate; offer free Motion Graphic animation instead when the user asks for a free path.

## Tool Params

| Param             | Values                            | Default   |
| ----------------- | --------------------------------- | --------- |
| `prompt`          | video description (required)      | —         |
| `model`           | `seedance2`, `kling`              | seedance2 |
| `durationSeconds` | seconds                           | 5         |
| `ratio`           | see model docs                    | 16:9      |
| `resolution`      | `720p`, `1080p`                   | 720p      |
| `name`            | descriptive asset name (required) | —         |
| `firstFrame`      | project asset ref                 | —         |
| `lastFrame`       | project asset ref                 | —         |

Model-specific params (e.g., Kling `mode`, Seedance `refImages` / `refVideos` / `refAudios`) — see the model's reference.

## Input Resolution

`firstFrame` / `lastFrame` / `refImages` / `refVideos` / `refAudios` all take a project asset reference. Prefer a full UUID or short prefix from `read_project`; `asset://<id>` and same-project asset URLs returned by `read_project` are also accepted. Per-slot type: frame slots and `refImages` → image; `refVideos` → video; `refAudios` → audio.

External URLs and base64 are not accepted. If the source is a public URL, download it into the project first (`download_media` for video/audio, `submit_image` for images) and pass the resulting asset id.

## Workflow

Four-step loop. For each new generation, restart from Step 1 if the user's intent has shifted.

### Step 1 — Align scope with the user

Before writing any prompt, align on three dimensions:

1. **Duration & segments** — total length, how many shots, and whether they live in one clip or several.

   If the user has already stated a direction ("做一段", "in one video", "分别生成", "split into N shots", etc.), follow it — don't second-guess.

   Otherwise, surface the two paths and let the user pick:
   - **Multi-shot within one clip** (see model ref) — single inference, subject / lighting / style physically consistent across sub-shots; fits a coherent narrative within the per-clip duration cap.
   - **Multiple clips** — each clip is independently controllable and re-rollable, but identity and style continuity have to be carried by anchors; fits durations beyond the cap or hard scene breaks.

   Offer the trade-off; do not pick for the user.

2. **Content** — what each clip depicts. Summarize back what you understood, segment by segment. When content is vague (e.g. "generate a video of a girl dancing"), the user typically hasn't specified one or more of:
   - **Subject**: who / what is the main subject (appearance, outfit, defining features)?
   - **Action**: what are they doing? (For talking / emotional shots, what micro-expression?)
   - **Scene**: where — setting, time of day, environmental details?
   - **Lighting / color mood**: what atmosphere?
   - **Camera**: any shot-size / angle / movement preference?
   - **Style**: visual style or reference (cinematic / anime / documentary / ...).

   Focus on the items that matter for this specific request and can't be safely inferred — don't turn this into a blank-filling exercise. Summarize the understood parts back to the user before proceeding.

3. **Consistency anchors** — only when multiple shots reuse a character, object, or scene: identify which anchor (reference image or video) to pin across shots. For sourcing rules, see §Visual consistency across shots below.

For each dimension, check the user's words:

- **Clear** — proceed.
- **Ambiguous or missing** — ASK the user. Do not guess, do not default to your own interpretation. A round-trip confirmation is cheaper than a wasted generation.

#### What NOT to do

- **Do not "tell then submit"** — announcing "I'll make this as 2 clips" and immediately submitting is not alignment, it's a unilateral decision with announcement.
- **Do not default to splitting a single-video request into multiple clips.** A single clip can carry multiple sub-shots (see model ref), with subject / lighting / style physically consistent across them. Surface the trade-off, then let the user choose.
- **Do not skip the ask** because you think the answer is obvious.

#### Hard overrides (user's explicit word wins)

- "one clip / single clip / 一条 / 一个镜头 / in 1 clip" → never split, even if the description is objectively long.
- "N shots / N 段 / N 个镜头" → generate exactly N.
- "use this image / 用这张图" → use as reference, don't substitute.

### Step 2 — Write the prompt

See the chosen model's reference for prompt structure and param combinations (e.g., Seedance's 8-element structure and modes; Kling's prompt tips). Before submitting, check:

- `name` is a **descriptive** asset name — descriptive enough for the user (and you in later turns) to recognize this asset in the project library. Avoid vague names like "Untitled" or "clip 1".
- Param combination matches the user's intent — see the **Modes** section in the model's reference.
- Generated video audio is not a tool parameter. Seedance 2.0 and Kling are submitted with audio enabled by the backend.
- On validation failure, read the error and fix the inputs — **do not blindly retry the same invalid arguments**.

### Step 3 — Submit one, wait, confirm

**Submit one generation job at a time.** Unless the user explicitly asked for multiple clips in parallel, do not submit the next clip until the current one completes and the user has reviewed it. Parallel submission hides problems: if the first shot has drift or wrong framing, the user would rather redo it once than have several misaligned shots to discard.

- `submit_video.ratio` controls the generated asset only; it does not change the project timeline canvas. If the user requested a final output aspect ratio (for example "9:16 vertical" or "16:9 landscape"), set the timeline canvas to the same ratio with `manage_timelines` action=update (e.g. ratio:"9:16") before placing the completed asset. If the user asked for no black bars / full-bleed, pass `fit:"cover"` when setting the canvas or updating/adding the visual item.
- Do not use this skill for job management — use the `track_progress` tool for status/wait.
- After submitting, end your turn (tell the user the job was created) unless a follow-up task is already queued.
- When the job finishes, surface the result to the user for review before proceeding to the next shot.
- Model-specific failure handling — see the model's reference.

### Step 4 — Iterate

When the user wants a next clip, a revision, or a continuation:

- **If it's the next shot in a multi-shot sequence** — reuse the established anchor (see §Visual consistency across shots below for principles, model ref for flag-level details).
- **If the user's feedback is ambiguous** ("it doesn't feel right") — ask what specifically to change before regenerating.
- **If the same text-prompt adjustment has failed twice** — stop adjusting text. Switch to reference images, or switch to edit mode where the model supports it (see model ref).
- Each new generation restarts the loop at Step 1 — realign if scope shifted.

## Visual consistency across shots

Text alone cannot reliably maintain visual identity across shots; visual references constrain output far more precisely than words.

### Anchors: the cornerstone of consistency

An **anchor** is a reference image or video pinned across every shot that shares the same character, object, or style. Any multi-shot sequence with recurring visual elements needs an anchor — don't try to reproduce them from text.

### Sourcing an anchor

Have reference awareness. When the user's request involves a recurring character / object / scene, think about what anchor to use **before** writing prompts:

- **Check the project first.** What has the user already provided or approved? Uploaded images, previously generated and approved shots, or earlier project assets can all serve as anchors.
- **Match the user's intent.** If the user pointed to a specific asset ("use this photo", "像上一段那样"), use that. If they described a character only in words, no anchor exists yet and one must be established.
- **When in doubt, ask the user.** Don't guess which asset to pin, and don't silently generate a new anchor when the user may already have one in mind.

### Establishing a new anchor (with user consent)

When no existing asset fits and one must be generated, propose it to the user first — it costs credits and shapes every downstream shot. Model-specific paths — see the chosen model's ref.

### Using the anchor

- Pass the anchor in **every shot** that shares the character / object / style. The specific flag(s) to use depend on the model — see the model's ref.
- Describe the anchor by appearance in the prompt, not by name: "The BLACK RACING CAR with chrome exhaust" constrains far more than "Fleetmaster". When role confusion is likely, add explicit negations: "The motorcycle does NOT transform."
- Refer to the anchor with `@Image1` / `@Video1` in the prompt — not vague phrases like "the same car as before".
- When a shot depends on a previous generation, **wait for the previous job to complete** (via `track_progress` with `action=wait`) to obtain its `assetId`, then pass it as the anchor reference. Do not submit dependent shots in parallel.

### Multi-character projects

When a project has multiple named characters with distinct attributes (e.g. Faz with fire energy, Kev with ice energy), treat each character as a **separate anchor** — one reference asset per character. In every prompt:

- Name the **active** character and attach their distinctive attributes ("Kev has **blue ice** electric energy").
- Add explicit negations for the others to prevent attribute leakage ("NOT red fire energy, NOT Faz's look").
- Pin the correct character's anchor (model-specific flag — see model ref). Do not reuse another character's anchor by accident.

Missing either explicit attribution or negation causes cross-character attribute mixing.

**Multiple characters in the same frame.** For shots where multiple characters appear together (especially facing the camera), the model is prone to face-swap or body-clipping. Add **strong positional + outfit anchors** to each character and prefer a **fixed camera** for that shot:

- "the character on the LEFT wears a grey-blue tactical jacket, short beard, silver earring"
- "the character on the RIGHT wears a red cape with gold trim, long braided hair"
- "fixed camera, medium shot, both characters clearly separated"

Positional words (left / right / foreground / background) + distinctive outfit colors give the model enough signal to keep the characters apart.

### Escalate when text adjustments fail

If a visual-identity issue (wrong character, drift, color mismatch) persists after **two text-prompt adjustments** on the same shot, stop adjusting text. Text is not a substitute for an anchor. Escalate to:

- Adding or switching the anchor.
- Edit mode where the model supports it (see model ref for how to invoke).

Do **not** submit a third text-only retry on the same consistency issue.

### When to skip anchoring

Simple, one-off, or exploratory requests do not need anchors — generate directly.

## Run

```ts
// Text-to-video (seedance2 default)
submit_video({
  model: "seedance2",
  prompt: "A cat walks across a sunny windowsill",
  name: "Cat on windowsill",
});

// Image-to-video with seedance2 — pass the project asset id directly; backend resolves to the asset's remoteUrl
submit_video({
  model: "seedance2",
  prompt: "The scene comes to life, gentle breeze rustles the curtains",
  firstFrame: "abc12345",
  name: "Living room animation",
});

// Kling text-to-video — only after Model Selection check
submit_video({
  model: "kling",
  prompt: "A sports car drifts around a wet corner",
  name: "Car drift shot",
});
```

After submission, call the `track_progress` tool: `action=status jobIds=<jobId>` to poll, `action=wait jobIds=<jobId>` to block until terminal.

## Config Mode

For complex multimodal jobs, build the full args object up front and pass it in a single call:

```ts
submit_video({
  model: "seedance2",
  prompt: "...",
  name: "...",
  firstFrame: "abc12345",
  refImages: ["def67890", "ghi24680"],
  refVideos: ["abc99999"],
  refAudios: ["jkl55555"],
  durationSeconds: 8,
  ratio: "9:16",
});
```

## Rules

- Always provide `--name` with a descriptive asset name.
- Default to submit-only. End your turn after submitting unless a follow-up task is queued.
- Do not call this skill with `--job`, `--wait`, or `--timeout` — job management belongs to `track_progress`.
- Generation costs credits. Before submitting, briefly tell the user what you're about to generate.


---

## 附：kling

# Kling

Read this document before generating videos with `model: "kling"` on `submit_video`.

## Model & task

We expose **Kling V3 Omni** only, always submitted as the `omni-video` task internally. Don't surface model variants (V3 / O3 / O1 / 2.6 / 2.5 Turbo) to the user — refer to it as "Kling".

## Capabilities

- Duration: 3–15 seconds (integer only, default 5s)
- Aspect ratio: `16:9`, `9:16`, `1:1`
- Mode: `std` (default) or `pro` (higher quality, slower)
- Prompt: up to 2500 characters
- Input images: 300×300 min, 10MB max, JPG/JPEG/PNG (no data URLs)
- Native audio generation (always on)
- Multi-shot storyboard: 2–6 shots in one job, identity preserved across shots

## Input Channels

| Param                 | Meaning                                                                                           |
| --------------------- | ------------------------------------------------------------------------------------------------- |
| `firstFrame: string`  | Start frame                                                                                       |
| `lastFrame: string`   | End frame (omni-video requires a first frame whenever an end frame is given)                      |
| `refImages: string[]` | Style/subject references (combined ≤7 with first/last frames; referenced as `@Image1`, `@Image2`) |

Image inputs take a project **asset reference**. Prefer a UUID or short prefix from `read_project`; `asset://<id>` and same-project asset URLs returned by `read_project` are also accepted. External URLs and base64 are rejected at the tool boundary — import them into the project first.

`refVideos` and `refAudios` are accepted by the tool schema for symmetry with Seedance, but **Kling currently ignores them** — see §Limitations.

## Kling-Specific Params

| Param                                         | Values                      | Default                   |
| --------------------------------------------- | --------------------------- | ------------------------- |
| `mode: "std" \| "pro"`                        | `std`, `pro`                | `std`                     |
| `shotType: "customize" \| "intelligence"`     | `customize`, `intelligence` | required for multi-shot   |
| `multiPrompts: [{ prompt, duration, index }]` | array of shots              | required when `customize` |

## Prompt References

When reference assets are passed as params, refer to them in the prompt by type and ordinal:

- `@Image1`, `@Image2`, … — reference images in order of appearance (`firstFrame` first if present, then `refImages` in array order)

Example: `"@Image1 character walks into the scene, maintaining the style of @Image2"`

## Multi-shot storyboard

Submit 2–6 shots in a single job; Kling preserves identity across them without explicit anchors.

**`shotType: "intelligence"`** — pass a single top-level `prompt` describing the whole sequence; the model auto-decomposes. Use when the user wants quick coverage and doesn't need per-shot duration control.

**`shotType: "customize"`** — omit top-level `prompt`; pass `multiPrompts` instead. Each shot is a self-contained scene. Backend rules:

- 2–6 shots
- Each `prompt` ≤ 512 characters
- Each `duration` is an integer ≥ 1
- Sum of `duration` must equal `durationSeconds` (total job duration)
- `index` is 1-based and consecutive: shot 1 → `index: 1`, shot 2 → `index: 2`, … (Kling rejects index starting at 0 or with gaps)

Example:

```ts
submit_video({
  model: "kling",
  shotType: "customize",
  durationSeconds: 12,
  ratio: "16:9",
  multiPrompts: [
    {
      index: 1,
      duration: 4,
      prompt:
        "[Shot 1] MCU. Slow dolly in. Key from camera-left, 5500K. ... Motion settles as ...",
    },
    {
      index: 2,
      duration: 4,
      prompt: "[Shot 2] WS. Static. ... Motion settles as ...",
    },
    {
      index: 3,
      duration: 4,
      prompt: "[Shot 3] CU. Pan right. ... Motion settles as ...",
    },
  ],
  name: "Cafe scene storyboard",
});
```

When using `customize`, write each shot like a standalone shot using the rules below.

## Prompt structure (essential rules)

Kling is a **technical-script** model. It does not auto-decompose scenes or auto-infer camera movements. Every shot needs explicit structure. The eight rules stack — each one fixes a specific failure mode.

### 1. Motion endpoint — required, every shot

End every shot with `Motion settles as <specific ending state>`. Without it, generations frequently stall at 99% or cut off abruptly. Applies to single-shot prompts, image-to-video, and every entry in a `customize` storyboard.

```
✗ A young woman walks down a rainy alley, neon reflections in puddles.
✓ A young woman walks down a rainy alley, neon reflections in puddles.
  Motion settles as she pauses under a red lantern, turns her face slightly toward camera.
```

### 2. Hollywood-standard shot sizes (English)

Open every shot with the English term + abbreviation. Vague Chinese terms (近景 / 中景) and unscoped prompts both drop recognition.

| Shot size        | Abbr | Use for                     |
| ---------------- | ---- | --------------------------- |
| Extreme close-up | ECU  | Eye, finger, single tear    |
| Close-up         | CU   | Face / single object        |
| Medium close-up  | MCU  | Head + shoulders, dialogue  |
| Medium shot      | MS   | Waist up                    |
| Medium long shot | MLS  | Full body, mid-distance     |
| Wide shot        | WS   | Full environment, establish |

### 3. Declare camera movement explicitly

Every shot needs ≥1 movement (`static` is valid — write it explicitly; never omit). Combine at most 2 per shot; 3+ degrades quality.

| Category    | Movements                                             |
| ----------- | ----------------------------------------------------- |
| Static      | static                                                |
| Push / Pull | dolly in, dolly out, pull back                        |
| Pan / Tilt  | pan left, pan right, tilt up, tilt down               |
| Tracking    | lateral tracking left/right, following shot           |
| Orbit       | slow 180 orbit (avoid for fast action — disorienting) |

Speed modifiers: `very slow / slow / medium / fast / whip`. Combine: `slow dolly in, then static`.

By drama type: emotional → `static` or `very slow dolly in`; action → `lateral tracking`; reveal → `slow pan` or `slow pull back`; product → `slow 180 orbit`.

### 4. Lighting triplet

"Warm lighting" alone is too vague. Spell out all three:

- **Direction**: e.g., `key from camera-left window`
- **Color temperature**: a specific Kelvin value (2700K–7500K)
- **Color tone**: e.g., `warm amber`, `teal-and-amber`, `cool blue`, `neutral`

Skipping any of the three causes face drift across frames and inconsistent shadows.

### 5. Sequential action — `first / then / finally`

For multi-step actions inside one shot, use the explicit sequencing structure. Flat description ("he walks in and turns around") confuses temporal reasoning.

```
First, she reads the open book calmly.
Then, she looks up suddenly as if hearing something, eyes widening.
Finally, she closes the book and stands up.
Motion settles as she stands fully upright, hand resting on the closed book.
```

### 6. Time slicing for shots ≥ 5s

For multi-beat shots, specify how many seconds each beat takes:

```
[Shot 2 / MCU / 6s]
  - 0–2s: Grandmother wraps the scarf around granddaughter's neck
  - 2–4s: Her fingers smooth the wool at the throat
  - 4–6s: Granddaughter closes her eyes, leans into grandmother's hand
Motion settles as grandmother's hand rests on the girl's cheek.
```

### 7. Emotions → physical manifestations (≥3)

Replace abstract emotion words with concrete physical signals. One signal feels mechanical; combine ≥3.

| Emotion | Combine 3+ of                                                                        |
| ------- | ------------------------------------------------------------------------------------ |
| Sad     | eyes glisten, lower lip trembles, breath becomes shallow, fingers curl loosely       |
| Scared  | pupils contract, breath catches in throat, cold sweat on forehead, hands tremble     |
| Happy   | eye-corner crinkles, mouth corners lift asymmetrically, shoulders relax, soft exhale |
| Angry   | jaw clenches, nostrils flare, knuckles whiten, breath quickens                       |

```
✗ Marcus looks scared.
✓ Marcus's pupils contract as his eyes widen, breath catches in his throat,
  a thin film of cold sweat forms on his forehead, his left hand trembles at his side.
```

### 8. Complexity ceiling — ≤7 elements per shot

Count elements: each character ≈ 1, each independent physical event ≈ 1, each continuous action ≈ 1, each background environment ≈ 1, secondary dynamics (wind/fog/falling leaves) ≈ 0.5. Over the limit → split into two shots.

## Multi-character anchors

When two characters share the frame, the model leaks attributes (A's clothing on B). Use explicit attribution + explicit negation, plus position words and outfit colors:

```
The character on the LEFT is @character_A — grey-blue tactical jacket, short beard.
NOT red cape, NOT braided hair.
The character on the RIGHT is @character_B — red cape with gold trim, long braided hair.
NOT grey-blue jacket, NOT short beard.
Camera: fixed, medium shot, both characters clearly separated.
```

## Real-person photo references

When passing a real-person photo as a reference, results are best when the photo is frontal (0–15° rotation), ≥1024×1024, evenly lit, neutral expression, no occlusion.

## Drama / emotional shot principles

When the request involves character performance or fine emotional control, lean on these (operations research, distilled):

- **No literary words** — replace "sad / shocking / eerie" with physical description (rule §7).
- **Vectorize action** — give each action a starting point, trajectory, and force/frequency, not just a verb.
- **Bio-consistency** — force ≥3 micro-expressions per emotion (throat swallow, jaw tension, blink rate).
- **Frame anchoring** — every shot must declare shot size + camera + lighting (rules §2/§3/§4).
- **Motion endpoint mandatory** — no exceptions (rule §1).
- **Bilingual division** — narrative in any language; technical directives (`Camera`, `Lighting`, `Motion settles`, `[Speaker:]`, `@reference`) in English.

## Limitations (don't promise these)

- **Voice Binding / voice cloning**: Kling O3 Omni only — not on V3 Omni. Don't offer.
- **Motion Brush**: a Kling Web UI feature, not in the public API.
- **Motion Control via reference video**: not currently forwarded by our integration; `refVideos` is accepted by the tool schema but has no effect on Kling submissions today.
- **`negative_prompt` field**: omni-video doesn't accept it. Bake avoidance directly into the `prompt` text, e.g. `… Avoid: blurry hands, extra fingers.`
- **Element library binding**: we don't yet upload to Kling's element library, so there's no parameter for it today.

## Failure handling

- 99% stall / abrupt cut-off → almost always a missing motion endpoint (rule §1).
- Face drift across separate jobs → reuse the same `refImages` entry on every shot; wait for the previous shot to complete (`track_progress` with `action=wait`) and use its frozen frame as the next shot's `firstFrame`. For 2–6 shots in one job, prefer multi-shot storyboard instead.
- Identity bleed between two on-screen characters → use the multi-character anchors block above.
- After **two** text-only retries on the same drift → stop adjusting text. Add or switch the reference image.


---

## 附：seedance2

# Seedance 2.0

Read this document before generating videos with `model: "seedance2"` (the default for `submit_video`).

## Capabilities

- Duration: 4–15 seconds (default 5s) via `durationSeconds`
- Audio: always on (music, narration, ambient). There is no audio toggle parameter for Seedance 2.0.
- Aspect ratio: `16:9`, `4:3`, `1:1`, `3:4`, `9:16`, `21:9`, or `adaptive` via `ratio`. `adaptive` auto-follows the input image's ratio — the backend auto-rewrites `ratio` to `adaptive` when `firstFrame` or `lastFrame` is set.
- Resolution: `720p` (only resolution currently wired; do not pass other values to `resolution`)

## Input Channels

Two categories:

- **Frames** appear at specific positions in the generated clip (first / last frame).
- **References** shape the generation (style, subject, motion, or audio) but are not placed as fixed frames in the output. How strictly a reference is followed depends on how you describe it in the prompt — from "use exactly this style" to "take inspiration from this".

| Category      | Param                 | Meaning                                                                                                                                  |
| ------------- | --------------------- | ---------------------------------------------------------------------------------------------------------------------------------------- |
| **Frame**     | `firstFrame: string`  | The exact first frame of the generated clip                                                                                              |
| **Frame**     | `lastFrame: string`   | The exact last frame; setting this enables first-last-frame transition mode                                                              |
| **Reference** | `refImages: string[]` | Image references — e.g. subject appearance, style, composition. Not placed as specific frames in the output.                             |
| **Reference** | `refVideos: string[]` | Video references — e.g. motion continuity, style, or as the source for edit / extend / bridge. How each is used is driven by the prompt. |
| **Reference** | `refAudios: string[]` | Audio references — e.g. rhythm, melody, ambient tone. Must combine with at least one visual input (frame or image / video reference).    |

Limits: 9 ref images, 3 ref videos, 3 ref audio. Each file ≤50MB (video), ≤30MB (image), ≤15MB (audio).

All frame/reference slots take a project **asset id** (UUID or short prefix from `read_project`), `asset://<id>`, or a same-project asset URL. External URLs are not accepted — pull them into the project first via `download_media` or `submit_image`.

## Modes (inferred from params)

Modes are inferred automatically from which params you pass — there is no separate mode parameter.

| Param combination                                                                                | Mode                        | Notes                                                                                                                                                                                                                                                                                       |
| ------------------------------------------------------------------------------------------------ | --------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `prompt` only                                                                                    | text-to-video               | No visual input                                                                                                                                                                                                                                                                             |
| `firstFrame` alone                                                                               | image-to-video              | Animate forward from a specific start frame                                                                                                                                                                                                                                                 |
| `firstFrame` + `lastFrame`                                                                       | first-last-frame transition | Strict start → end frames                                                                                                                                                                                                                                                                   |
| any of `refImages` / `refVideos` / `refAudios` (alone or combined, optionally with `firstFrame`) | reference-guided            | Generation guided by one or more references. What each reference _does_ (style guide, subject anchor, motion continuity, editing existing footage, bridging segments, …) is driven by the **prompt**, not by how many refs you pass. See §Editing & Extending for concrete prompt patterns. |

**First-last-frame mode is mutually exclusive with reference inputs.** If `lastFrame` is set, you cannot also pass `refImages`, `refVideos`, or `refAudios` — the request will be rejected by the backend. Choose one: either strict frame transition, or reference-guided generation.

## Content Review

Seedance applies content review on inputs. Two cases worth knowing:

- **Real human faces** (including AI-generated photorealistic faces) — supported. Pass real-person photos directly via `refImages`, `firstFrame`, or `lastFrame`.
- **Copyright / IP-protected likenesses** — recognizable celebrities, public figures, well-known fictional characters, branded mascots — remain blocked. If submission fails and the input is a recognizable IP face, surface the failure and ask for a different reference.

_Edge case: videos previously generated by Seedance 2.0 under the same account can be reused as edit / extend inputs without re-review._

## Seedance Error Handling

- If a submission fails with a content-review error, surface the failure and ask the user for a different reference. Don't retry with the same input.

## Prompt Writing

Seedance 2.0 has strong intent comprehension. Structure prompts around eight elements:

**Subject** + **Action** + **Scene** + **Lighting / Color** + **Camera** + **Style** + **Quality** + **Negative Constraints**

- **Subject** — who / what is the main subject (appearance, outfit, defining features).
- **Action** — what they are doing, including micro-expressions for talking or emotional shots.
- **Scene** — where, when, environmental details.
- **Lighting / Color** — atmosphere, color grading, contrast, mood.
- **Camera** — shot size, angle, movement (see **Camera language** below).
- **Style** — visual style or genre (cinematic, anime, documentary, film-grain, …).
- **Quality** — resolution and detail cues, e.g. "4K, sharp details, film-grade quality".
- **Negative Constraints** — what to avoid (see **Quality & stability tails** below).

Keep prompts concise: Chinese ≤500 characters, English ≤1000 words. Overly long prompts dilute focus — the model may drop details when information is too dense.

### Prompt References

When reference assets are passed as params, the prompt text refers to them by type and ordinal number. The Seedance API assigns numbers **by order of appearance in the request**, without distinguishing frame vs reference.

- `@Image1` / `@图片1` — first image input. `firstFrame` counts as Image1 if present; otherwise `refImages[0]` is Image1. Subsequent images follow array order (`@Image2`, `@Image3`, …).
- `@Video1` / `@视频1` — `refVideos[0]`; `@Video2` is `refVideos[1]`; etc.
- `@Audio1` / `@音频1` — `refAudios[0]`; same pattern.

Example: `refImages: ["A", "B"], refVideos: ["C"]` → in the prompt, `@Image1` = A, `@Image2` = B, `@Video1` = C.

In prompts, always refer to passed inputs by explicit numbered references (`@Image1`, `@Video1`, `@Audio1`) rather than vague descriptions.

**Do**: `"@Image1 (the dark-haired woman) walks into the scene from @Image2 (the living room)"` — clear, unambiguous.
**Don't**: `"make the character look like that reference image"` — vague; the model may pick the wrong input.

**After `@ImageN` / `@VideoN`, always follow with a noun or clarifier** — `@Image1 character walks...`, `@Image1 (the black car) drifts...`, `@视频1 的镜头继续`. Do NOT directly attach a verb, position word, or another number (e.g. `@Image2 stands...`, `@图2位于...`, `@Image1 2 seconds later`) — the model may mis-segment the number and produce wrong counts.

### Quality & Stability Tails

For character-focused or face-visible clips, **always append quality and stability cues** as a tail, for example:

> "4K, sharp details" + "character face stable, no mutation, no clipping, no duplicated limbs, hands and fingers anatomically correct"

These failure-prevention tails materially improve hit rate. Include them by default unless the user explicitly asks for a raw / lo-fi / experimental look.

### Camera Language

Seedance 2.0 understands these terms well:

| Category  | Terms                                                          |
| --------- | -------------------------------------------------------------- |
| Shot size | Close-up, Medium Shot, Full Shot, Long Shot, Extreme Long Shot |
| Angle     | Low Angle, High Angle, Eye-level, Over-the-shoulder            |
| Movement  | Push-in, Pull-out, Pan, Dolly/Track, Following Shot, Orbit     |
| Effects   | Slow Motion, Time-lapse, Shallow Depth of Field, Handheld Feel |

**Single camera movement per sub-shot.** Avoid stacking conflicting movements in one sub-shot (e.g. push-in + pan-left, or dolly + orbit). When a beat needs a different camera move, use another sub-shot — prefer chaining sub-shots inside the same clip (see §Multi-shot within a single clip below); split into multiple clips only when the total duration exceeds 15s or the boundary is a hard scene break.

## Multi-shot within a single clip

A single 4–15s Seedance generation does not have to carry only one camera setup. With clear sub-shot structure in the prompt (`Shot 1: ... → Shot 2: ...`, or timestamp slicing `0–2s ... | 2–4s ...`), the model strings several sub-shots into a continuous beat inside one clip.

**Characteristic.** A single generation is a single inference pass — subject identity, lighting, color, and style are physically consistent across the whole clip as a natural byproduct of one diffusion process. When the same beats are split into multiple separate clips, each clip is an independent inference; subject identity, lighting, and color tend to drift across clips and need `--ref-image` / `--ref-video` to keep them aligned.

**When to fall back to multiple clips.**

- Total duration exceeds 15s.
- A sub-shot boundary is a hard cut to a completely unrelated scene or subject — anchor-based cross-clip consistency fits that better than a single-clip narrative.

A single sub-shot still follows the one-camera-movement rule. Multiple camera movements get multiple sub-shots, not stacked into one.

**Prompt structure.**

- Write each sub-shot in the 8-element form, but only fill in what changes from the previous sub-shot — let the model carry forward the rest.
- Put transitions at sub-shot boundaries when intentional ("camera cuts to a CU as she turns").
- The Quality & Negative tail covers the whole prompt; do not repeat it per sub-shot.

**Example (8s vertical, 4 sub-shots):**

```
8s, 9:16, cinematic.
Shot 1 (0–2s): Full shot, she walks onto the red carpet, soft top-light, slow forward dolly.
Shot 2 (2–4s): Medium shot, she turns to camera, holds @Image1 perfume bottle, key light from camera-left.
Shot 3 (4–6s): Close-up on @Image1, gentle rotation, shallow depth of field.
Shot 4 (6–8s): Medium shot, she smiles back at camera, dress hem flutters.
4K sharp details, character face stable, no mutation, no clipping, hands anatomically correct.
```

## Editing & Extending

These are **prompt-driven use cases** of the `reference-guided` mode — they produce a **new generated video clip** based on a source clip, not timeline edits. The output is a fresh asset; the original is not modified.

All three patterns pass the source clip(s) via `refVideos`; the use case is determined by what the prompt asks for. The source video must be a completed generation (use its `assetId`).

| Use case   | What the prompt asks                                                           | Example prompt                                        |
| ---------- | ------------------------------------------------------------------------------ | ----------------------------------------------------- |
| **Edit**   | Replace or adjust elements while keeping the rest                              | "Replace the scarf in @Video1 with a red one"         |
| **Extend** | Continue forward, or prepend earlier footage                                   | "Continue from @Video1, the character opens the door" |
| **Bridge** | Fill a gap between 2–3 segments (pass each as a separate entry in `refVideos`) | "Smooth transition from @Video1 to @Video2"           |

These are typical patterns, not an exhaustive list — `refVideos` is a flexible reference channel and the prompt can express other intents too (style continuation, motion-only carry-over, etc.).

When the user is unhappy with a result, prefer editing over regenerating from scratch — cheaper, and preserves what already works.

## Seedance-Specific Consistency Implementation

Seedance 2.0 is stateless — each call is independent. For cross-model anchor _principles_ (when to use, how to source, multi-character, escalation), see §Visual consistency across shots in SKILL.md. The Seedance-specific _implementation_ details below complement those principles.

### How to pass an anchor (Seedance params)

- `refImages: [<imageAssetId>]` — pin a static image anchor (character, style, composition).
- `refVideos: [<videoAssetId>]` — pin a video anchor (motion continuity, edit/extend/bridge source).

### Carry approved shots forward when consistency is explicit

In a multi-shot sequence with a clearly stated consistency need (same character, scene, or style across shots), after the first shot is approved, pass the most recently approved shot in `refVideos` for subsequent shots — **in addition to** the static image anchor. The combination `refImages: [<character>] + refVideos: [<previous-approved-shot>]` anchors both identity (from the image) and motion / style continuity (from the video), and is stronger than either one alone. If the user's consistency intent is not clear — e.g. the next shot is in a very different setting and it's not obvious what should stay the same — **ask before generating**. Don't assume.

### When a shot depends on a previous generation

Wait for the previous job to complete (via `track_progress` with `action=wait`) to obtain its `assetId`, then pass that id in `refVideos`. Do not submit dependent shots in parallel.

### Establishing a new anchor — Seedance paths

When no existing asset fits and one must be generated:

- **Generated character / illustration** → `submit_image` to create a reference, then pass its asset id in `refImages`.
- **Real-person photo** → if the user has an existing photo, use it directly in `refImages`. The backend handles content review automatically. If the user wants a generated photorealistic character, use `submit_image` then pass in `refImages` — same flow.

### Multi-character — Seedance param

Pin the correct character's anchor in `refImages`. Do not reuse another character's anchor by accident.

### Escalation — edit mode on Seedance

Reuse the best-looking existing shot in `refVideos` and describe the change in the prompt. This is Seedance's "edit mode" path for breaking a stuck consistency loop.

### Example: two-shot sequence with a character anchor

```ts
// Shot 1 — anchor character appearance with a reference image
submit_video({
  model: "seedance2",
  refImages: ["character-ref-id"],
  prompt:
    "@Image1 black racing car drifts around a rain-soaked corner, left to right. Sparks fly from tires.",
  name: "Chase scene — shot 1 drift",
});

// Wait for shot 1 to finish (call `track_progress` with action="wait", jobIds=[<shot1-jobId>]),
// then read its `outputAssetId` from the returned entry.

// Shot 2 — same character ref + shot 1 as video reference for motion continuity
submit_video({
  model: "seedance2",
  refImages: ["character-ref-id"],
  refVideos: ["<shot1-assetId>"],
  prompt:
    "Same @Image1 black racing car continues speeding. Carry forward the motion style of @Video1. Camera follows from behind.",
  name: "Chase scene — shot 2 follow-through",
});
```
